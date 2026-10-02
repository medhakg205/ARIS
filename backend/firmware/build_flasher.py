"""
ARIS Build & Flash Subsystem.
Provides abstractions for:
- Compiling firmware sketches targeting specific board profiles (Uno, Nano, Mega)
- Flashing compiled binaries to target boards via arduino-cli / avrdude
- Verifying binary upload integrity
If hardware tooling (arduino-cli, avr-gcc, avrdude) is unavailable during development,
provides a clean adapter with realistic simulation and testable failure states.
"""

import os
import sys
import time
import json
import shutil
import tempfile
import subprocess
import logging
from typing import Dict, Any, Optional

from backend.firmware.board_profiles import get_board_profile, BoardProfile
from backend.serial.serial_discovery import find_arduino_cli_path
from backend.telemetry.telemetry_schema import ArisException

logger = logging.getLogger("aris.firmware.flasher")


class BuildFlasher:
    """
    Abstractions for compilation, flashing, and upload verification.
    Integrates directly with arduino-cli for real compilation and flashing,
    with deterministic simulation fallbacks when physical toolchains are absent.
    """

    def __init__(self, use_simulated_toolchain_if_missing: bool = True):
        self.use_simulated = use_simulated_toolchain_if_missing
        # Detect host toolchain availability
        self.arduino_cli_path = find_arduino_cli_path()
        self.avrdude_path = shutil.which("avrdude")

    def compile_firmware(
        self,
        source_code: str,
        board_id: str,
        fail_simulation: bool = False,
        is_simulation: bool = False
    ) -> Dict[str, Any]:
        """
        Compiles Arduino source code for the target board profile.
        Determines FQBN (Fully Qualified Board Name) from the board profile:
        - arduino_uno: arduino:avr:uno
        - arduino_nano: arduino:avr:nano
        - arduino_mega: arduino:avr:mega:cpu=atmega2560
        Raises ARIS_BUILD_FAILED on syntax or compiler error.
        """
        # Validate board profile
        try:
            profile = get_board_profile(board_id)
        except KeyError:
            raise ArisException(
                error_code="ARIS_UNSUPPORTED_BOARD",
                message=f"Board ID '{board_id}' is not supported for compilation.",
                details={"board_id": board_id},
                recoverable=False,
                status_code=400
            )

        if not profile.fqbn:
            raise ArisException(
                error_code="ARIS_UNSUPPORTED_BOARD",
                message=f"Board '{profile.display_name}' ({board_id}) does not have a defined FQBN for compilation.",
                details={"board_id": board_id, "arch": profile.arch, "fqbn": profile.fqbn},
                recoverable=False,
                status_code=400
            )

        if fail_simulation:
            raise ArisException(
                error_code="ARIS_BUILD_FAILED",
                message="Simulated compilation failure: syntax error detected in source code.",
                details={"board_id": board_id, "error": "error: expected ';' before '}' token"},
                recoverable=True,
                status_code=400
            )

        # Basic source sanity check
        if not source_code or len(source_code.strip()) == 0:
            raise ArisException(
                error_code="ARIS_BUILD_FAILED",
                message="Cannot compile empty source code.",
                details={"board_id": board_id},
                recoverable=True,
                status_code=400
            )

        if not is_simulation and not self.arduino_cli_path:
            raise ArisException(
                error_code="ARIS_TOOLCHAIN_UNAVAILABLE",
                message="arduino-cli toolchain not found. Install arduino-cli and the target core to enable physical compilation.",
                details={"board_id": board_id, "fqbn": profile.fqbn},
                recoverable=False,
                status_code=503
            )

        # Real compilation if arduino-cli is installed
        if self.arduino_cli_path:
            try:
                with tempfile.TemporaryDirectory() as td:
                    sketch_dir = os.path.join(td, "sketch")
                    os.makedirs(sketch_dir, exist_ok=True)
                    sketch_file = os.path.join(sketch_dir, "sketch.ino")
                    with open(sketch_file, "w", encoding="utf-8") as f:
                        f.write(source_code)

                    cmd = [
                        self.arduino_cli_path,
                        "compile",
                        "--fqbn", profile.fqbn,
                        "--format", "json",
                        "--export-binaries",
                        sketch_dir
                    ]
                    proc = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=45.0
                    )

                    stdout_json = {}
                    if proc.stdout.strip():
                        try:
                            stdout_json = json.loads(proc.stdout)
                        except Exception:
                            pass

                    if proc.returncode != 0:
                        diag_msgs = []
                        if stdout_json:
                            builder_res = stdout_json.get("builder_result", {})
                            diags = builder_res.get("diagnostics", [])
                            for d in diags:
                                diag_msgs.append(f"Line {d.get('line', '?')}: {d.get('message', '')}")
                        err_text = "\n".join(diag_msgs) if diag_msgs else (proc.stderr.strip() or stdout_json.get("error", "Compilation failed"))
                        raise ArisException(
                            error_code="ARIS_BUILD_FAILED",
                            message=f"Firmware compilation failed on {profile.display_name}: {err_text}",
                            details={"board_id": board_id, "fqbn": profile.fqbn, "compiler_error": err_text, "raw_stderr": proc.stderr},
                            recoverable=True,
                            status_code=400
                        )

                    builder_result = stdout_json.get("builder_result", {})
                    sections = builder_result.get("executable_sections_size", [])
                    flash_used = 0
                    sram_used = 0
                    for sec in sections:
                        sec_name = sec.get("name", "").lower()
                        sec_size = sec.get("size", 0)
                        if sec_name in ("text", ".text"):
                            flash_used += sec_size
                        elif sec_name in ("data", ".data"):
                            flash_used += sec_size
                            sram_used += sec_size
                        elif sec_name in ("bss", ".bss"):
                            sram_used += sec_size

                    size_unavailable = False
                    if flash_used == 0:
                        if is_simulation:
                            flash_used = 2450 + len(source_code) * 2
                        else:
                            size_unavailable = True
                    if sram_used == 0:
                        if is_simulation:
                            sram_used = 220 + len(source_code) // 5
                        else:
                            size_unavailable = True

                    build_cache_dir = os.path.join(os.getcwd(), "build_artifacts")
                    os.makedirs(build_cache_dir, exist_ok=True)
                    hex_filename = f"{board_id}_{profile.mcu}.hex"
                    target_hex = os.path.join(build_cache_dir, hex_filename)

                    exported_hex = None
                    for root, _, files in os.walk(sketch_dir):
                        for file in files:
                            if file.endswith(".hex") and not file.endswith(".with_bootloader.hex"):
                                exported_hex = os.path.join(root, file)
                                break
                    if exported_hex and os.path.exists(exported_hex):
                        shutil.copy2(exported_hex, target_hex)
                    else:
                        target_hex = None

                    flash_pct = round((flash_used / profile.flash_bytes) * 100, 2) if (profile.flash_bytes and not size_unavailable) else 0.0
                    sram_pct = round((sram_used / profile.sram_bytes) * 100, 2) if (profile.sram_bytes and not size_unavailable) else 0.0

                    return {
                        "status": "BUILD_SUCCESS",
                        "board_id": board_id,
                        "fqbn": profile.fqbn,
                        "mcu": profile.mcu,
                        "toolchain": "arduino-cli",
                        "binary_path": target_hex,
                        "binary_size_bytes": flash_used,
                        "flash_usage_pct": flash_pct,
                        "sram_usage_bytes": sram_used,
                        "sram_usage_pct": sram_pct,
                        "size_unavailable": size_unavailable,
                        "compiler_output": stdout_json.get("compiler_out", f"Compiled sketch successfully for {profile.display_name} ({profile.mcu}).")
                    }
            except subprocess.TimeoutExpired:
                raise ArisException(
                    error_code="ARIS_BUILD_FAILED",
                    message="Firmware compilation timed out after 45 seconds.",
                    details={"board_id": board_id},
                    recoverable=True,
                    status_code=400
                )
            except ArisException:
                raise
            except Exception as e:
                logger.warning(f"Real toolchain compilation encountered exception: {e}; falling back.")
                if not is_simulation or not self.use_simulated:
                    raise ArisException(
                        error_code="ARIS_BUILD_FAILED",
                        message=f"Compiler execution error: {e}",
                        details={"board_id": board_id},
                        recoverable=True,
                        status_code=500
                    )

        # Simulated fallback compilation result
        flash_est = 2450 + len(source_code) * 2
        sram_est = 220 + len(source_code) // 5
        sim_flash_pct = round((flash_est / profile.flash_bytes) * 100, 2) if profile.flash_bytes else 0.0
        sim_sram_pct = round((sram_est / profile.sram_bytes) * 100, 2) if profile.sram_bytes else 0.0

        return {
            "status": "BUILD_SUCCESS",
            "board_id": board_id,
            "fqbn": profile.fqbn,
            "mcu": profile.mcu,
            "toolchain": "simulated",
            "binary_path": None,
            "binary_size_bytes": flash_est,
            "flash_usage_pct": sim_flash_pct,
            "sram_usage_bytes": sram_est,
            "sram_usage_pct": sim_sram_pct,
            "size_unavailable": False,
            "compiler_output": f"Simulated compilation successful for {profile.display_name} ({profile.mcu})."
        }

    def flash_board(
        self,
        board_id: str,
        port: str,
        binary_path: Optional[str] = None,
        source_code: Optional[str] = None,
        fail_simulation: bool = False
    ) -> Dict[str, Any]:
        """
        Flashes compiled binary or sketch to the microcontroller connected at port.
        Raises ARIS_FLASH_FAILED on serial programmer error or timeout.
        """
        try:
            profile = get_board_profile(board_id)
        except KeyError:
            raise ArisException(
                error_code="ARIS_UNSUPPORTED_BOARD",
                message=f"Board ID '{board_id}' is not supported for flashing.",
                details={"board_id": board_id},
                recoverable=False,
                status_code=400
            )

        if not profile.supported:
            raise ArisException(
                error_code="ARIS_UNSUPPORTED_BOARD",
                message=f"Board '{profile.display_name}' ({board_id}) is not supported for flashing.",
                details={"board_id": board_id},
                recoverable=False,
                status_code=400
            )

        if fail_simulation:
            raise ArisException(
                error_code="ARIS_FLASH_FAILED",
                message=f"avrdude failed to communicate with {profile.mcu} on {port}: programmer not responding.",
                details={"port": port, "board_id": board_id},
                recoverable=True,
                status_code=500
            )

        # Check if port is simulated or virtual
        simulated_ports = {"SIMULATED", "COM_MOCK", "VIRTUAL", "DEMO", "TEST", "MOCK"}
        is_sim_port = (not port) or port.upper() in simulated_ports

        if is_sim_port:
            logger.info(f"Simulated flash of firmware to {profile.display_name} on {port or 'simulated port'}.")
            return {
                "status": "FLASH_SUCCESS",
                "board_id": board_id,
                "port": port or "SIMULATED",
                "toolchain": "simulated",
                "bytes_written": 2450,
                "verified": True,
                "verification_method": "simulation",
                "verification_notice": "Simulated flash: target port is virtual.",
                "message": f"Successfully flashed firmware to {profile.display_name} on {port or 'SIMULATED'} (simulated)."
            }

        # Physical port requires real arduino-cli
        if not self.arduino_cli_path:
            raise ArisException(
                error_code="ARIS_TOOLCHAIN_UNAVAILABLE",
                message="arduino-cli toolchain not found. Install arduino-cli and the target core to enable physical flashing.",
                details={"board_id": board_id, "port": port},
                recoverable=False,
                status_code=503
            )

        # Real hardware flashing via arduino-cli upload
        try:
            with tempfile.TemporaryDirectory() as td:
                sketch_dir = os.path.join(td, "sketch")
                os.makedirs(sketch_dir, exist_ok=True)
                sketch_file = os.path.join(sketch_dir, "sketch.ino")
                if source_code:
                    with open(sketch_file, "w", encoding="utf-8") as f:
                        f.write(source_code)
                elif binary_path and os.path.exists(binary_path):
                    with open(sketch_file, "w", encoding="utf-8") as f:
                        f.write("void setup(){} void loop(){}")
                else:
                    raise ArisException(
                        error_code="ARIS_FLASH_FAILED",
                        message="Cannot flash target board: no source code or compiled binary provided.",
                        details={"board_id": board_id, "port": port},
                        recoverable=True,
                        status_code=400
                    )

                cmd = [
                    self.arduino_cli_path,
                    "upload",
                    "-p", port,
                    "--fqbn", profile.fqbn,
                    "--format", "json"
                ]
                if binary_path and os.path.exists(binary_path):
                    cmd.extend(["--input-file", binary_path])
                else:
                    cmd.append(sketch_dir)

                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60.0
                )

                if proc.returncode != 0:
                    err_msg = proc.stderr.strip() or proc.stdout.strip() or "Programmer failed to upload binary"
                    raise ArisException(
                        error_code="ARIS_FLASH_FAILED",
                        message=f"Upload to {profile.display_name} on {port} failed: {err_msg}",
                        details={"board_id": board_id, "port": port, "error": err_msg},
                        recoverable=True,
                        status_code=500
                    )

                verified = self.verify_upload(board_id=board_id, port=port)
                if not verified:
                    raise ArisException(
                        error_code="ARIS_FLASH_UNVERIFIED",
                        message=f"Uploaded firmware failed ARIS runtime handshake verification on target {port}.",
                        details={"board_id": board_id, "port": port},
                        recoverable=True,
                        status_code=500
                    )

                return {
                    "status": "FLASH_SUCCESS",
                    "board_id": board_id,
                    "port": port,
                    "toolchain": "arduino-cli",
                    "bytes_written": 2450,
                    "verified": True,
                    "verification_method": "runtime_handshake",
                    "verification_notice": "Upload verified by successful upload + ARIS runtime handshake; direct flash-memory checksum verification not implemented.",
                    "message": f"Successfully flashed firmware to physical {profile.display_name} on {port}."
                }
        except subprocess.TimeoutExpired:
            raise ArisException(
                error_code="ARIS_FLASH_FAILED",
                message=f"Flashing timed out after 60 seconds on {port}.",
                details={"board_id": board_id, "port": port},
                recoverable=True,
                status_code=500
            )

    def verify_upload(self, board_id: str, port: str, timeout_sec: float = 3.0) -> bool:
        """
        Verifies that the uploaded firmware is intact on the target microcontroller.
        Note: AVR microcontrollers via Arduino bootloader / avrdude do not support
        direct on-chip flash memory read-back checksum verification without an ISP programmer.
        ARIS uses the ARIS runtime serial handshake protocol ($ARIS_HELLO -> $ARIS_ACK)
        as the authoritative verification of firmware boot and runtime communication.
        """
        simulated_ports = {"SIMULATED", "COM_MOCK", "VIRTUAL", "DEMO", "TEST", "MOCK"}
        if not port:
            return False
        if port.upper() in simulated_ports:
            return True

        get_board_profile(board_id)

        try:
            from backend.api.dependencies import get_serial_mgr
            serial_mgr = get_serial_mgr()
            # Give target MCU a moment to reset after bootloader finishes flashing (DTR pulse reset)
            time.sleep(1.5)
            # Ensure serial manager connects to the target port
            if not serial_mgr.connected or serial_mgr.current_port != port:
                serial_mgr.connect(port=port, baud_rate=115200)

            res = serial_mgr.perform_handshake(timeout_sec=timeout_sec)
            return bool(res.get("handshake_success"))
        except Exception as e:
            logger.warning(f"Verification handshake failed on {port}: {e}")
            return False
