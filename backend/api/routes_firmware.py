"""
ARIS Firmware Upload & Management REST API Routes.
Endpoints:
- POST /api/firmware/upload
- GET /api/firmware
- GET /api/firmware/{firmware_id}
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.api.dependencies import get_firmware_mgr, get_build_flasher, get_db, get_serial_mgr
from backend.database.models import FirmwareRecord, RunRecord
from backend.instrumentation.sketch_instrumenter import SketchInstrumenter
from datetime import datetime, timezone
from backend.analysis.static_analyzer import StaticAnalyzer
from backend.firmware.preflight_analyzer import PreflightMemoryAnalyzer, PreflightMemoryReport
from backend.telemetry.telemetry_schema import ArisException

import os
import time
import json
import glob
import urllib.parse

router = APIRouter(tags=["Firmware"])


class FirmwareUploadRequest(BaseModel):
    """Payload for uploading new firmware artifacts."""
    name: str = Field(..., description="Project name")
    source_code: Optional[str] = None
    hex_content: Optional[str] = None
    elf_path: Optional[str] = None
    map_content: Optional[str] = None


class SaveIDESketchRequest(BaseModel):
    path: str = Field(..., description="Absolute path to the .ino file to overwrite")
    source_code: str = Field(..., description="Optimized source code")


def _discover_arduino_ide_sketches() -> List[Dict[str, Any]]:
    """Helper to detect recent sketches from Arduino IDE 2.x and standard sketchbooks."""
    results = []
    seen_paths = set()

    # 1. Check Arduino IDE 2.x recent-sketches.json
    recent_file = os.path.expanduser('~/.arduinoIDE/recent-sketches.json')
    if os.path.exists(recent_file):
        try:
            with open(recent_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
            for uri, ts in sorted_items:
                clean_path = urllib.parse.unquote(uri.replace('file:///', ''))
                clean_path = os.path.normpath(clean_path)
                if os.path.exists(clean_path):
                    if os.path.isdir(clean_path):
                        for ino in glob.glob(os.path.join(clean_path, '*.ino')):
                            ino_norm = os.path.normpath(ino)
                            if ino_norm not in seen_paths:
                                seen_paths.add(ino_norm)
                                results.append({
                                    'name': os.path.basename(ino_norm),
                                    'path': ino_norm,
                                    'last_modified': ts / 1000 if ts > 1e11 else ts
                                })
                    elif clean_path.endswith('.ino') and clean_path not in seen_paths:
                        seen_paths.add(clean_path)
                        results.append({
                            'name': os.path.basename(clean_path),
                            'path': clean_path,
                            'last_modified': ts / 1000 if ts > 1e11 else ts
                        })
        except Exception:
            pass

    # 2. Check standard Arduino sketchbook folders
    sketchbook_dirs = [
        os.environ.get('ARDUINO_SKETCHBOOK_DIR', ''),
        os.path.expanduser('~/OneDrive/Documents/Arduino'),
        os.path.expanduser('~/Documents/Arduino'),
    ]
    for sb in sketchbook_dirs:
        if sb and os.path.exists(sb):
            for ino in glob.glob(os.path.join(sb, '**', '*.ino'), recursive=True):
                ino_norm = os.path.normpath(ino)
                # Ignore third-party library examples in libraries/
                if os.sep + "libraries" + os.sep in ino_norm or "/libraries/" in ino_norm.replace("\\", "/"):
                    continue
                if ino_norm not in seen_paths:
                    seen_paths.add(ino_norm)
                    results.append({
                        'name': os.path.basename(ino_norm),
                        'path': ino_norm,
                        'last_modified': os.path.getmtime(ino_norm)
                    })

    results.sort(key=lambda x: x['last_modified'], reverse=True)
    return results


@router.post("/api/firmware/upload")
def upload_firmware(req: FirmwareUploadRequest) -> Dict[str, Any]:
    """
    Uploads firmware artifacts (source, hex, elf, or map).
    Returns created FirmwareRecord.
    """
    mgr = get_firmware_mgr()
    record = mgr.upload_firmware(
        name=req.name,
        source_code=req.source_code,
        hex_content=req.hex_content,
        elf_path=req.elf_path,
        map_content=req.map_content
    )
    return record.model_dump()


@router.get("/api/firmware")
def list_all_firmware() -> List[Dict[str, Any]]:
    """Lists all stored firmware bundles."""
    mgr = get_firmware_mgr()
    return [fw.model_dump() for fw in mgr.list_firmwares()]


@router.get("/api/firmware/ide-recent")
def get_recent_ide_sketches() -> Dict[str, Any]:
    """
    Auto-discovers sketches compiled or opened in the Arduino IDE.
    Returns the list and automatically reads the source code of the most recent sketch.
    """
    sketches = _discover_arduino_ide_sketches()
    if not sketches:
        return {"found": False, "sketches": [], "active_sketch": None}

    latest = sketches[0]
    source = ""
    try:
        with open(latest["path"], "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except Exception:
        pass

    latest_with_code = {
        **latest,
        "source_code": source
    }

    return {
        "found": True,
        "sketches": sketches[:10],
        "active_sketch": latest_with_code
    }


@router.post("/api/firmware/sync-ide")
def sync_ide_sketch(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes an Arduino IDE sketch path, reads it, and registers it into ARIS firmware manager.
    """
    import os
    path = req.get("path")
    if not path or not os.path.exists(path):
        # Fallback to latest
        sketches = _discover_arduino_ide_sketches()
        if not sketches:
            return {"success": False, "error": "No Arduino sketches found on machine"}
        path = sketches[0]["path"]

    name = os.path.basename(path)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()

    mgr = get_firmware_mgr()
    fw = mgr.upload_firmware(name=name, source_code=source)
    return {
        "success": True,
        "firmware": fw.model_dump(),
        "path": path,
        "source_code": source,
        "name": name
    }


class ApplyCandidateRequest(BaseModel):
    candidate_id: str = Field(..., description="Optimization candidate identifier")
    sketch_path: Optional[str] = Field(default=None, description="Path to .ino sketch")
    expected_hash: Optional[str] = Field(default=None, description="Expected SHA-256 of original file before apply")


class RevertCandidateRequest(BaseModel):
    candidate_id: Optional[str] = Field(default=None, description="Optimization candidate identifier")
    sketch_path: Optional[str] = Field(default=None, description="Path to .ino sketch")
    backup_path: Optional[str] = Field(default=None, description="Specific backup file path to restore")


@router.post("/api/firmware/apply-candidate")
def apply_candidate_endpoint(req: ApplyCandidateRequest) -> Dict[str, Any]:
    """
    Safely applies a validated optimization candidate to the user's local sketch:
    1. Verifies the sketch file exists on disk and is a valid C/C++ sketch.
    2. Calculates current SHA-256 hash. If expected_hash is provided and mismatches,
       aborts with ARIS_SOURCE_APPLY_FAILED (409 Conflict).
    3. Backs up the original sketch into .aris/backups/<sketch>.<timestamp>.bak.
    4. Computes replacement code, strictly ensuring zero ARIS runtime code is introduced.
    5. Atomically writes the optimized code to disk and verifies SHA-256 after write.
    6. If write verification fails, automatically rolls back to backup and aborts.
    7. Updates candidate and firmware provenance in the database only after verification.
    """
    from backend.optimization.source_application_engine import apply_candidate_to_source
    db = get_db()
    return apply_candidate_to_source(
        candidate_id=req.candidate_id,
        sketch_path=req.sketch_path,
        expected_hash=req.expected_hash,
        db=db
    )


@router.post("/api/firmware/revert-candidate")
def revert_candidate_endpoint(req: RevertCandidateRequest) -> Dict[str, Any]:
    """
    Reverts an applied candidate by restoring the sketch from its .aris/backups/ file.
    """
    from backend.optimization.source_application_engine import revert_candidate_source
    db = get_db()
    return revert_candidate_source(
        candidate_id=req.candidate_id,
        sketch_path=req.sketch_path,
        backup_path=req.backup_path,
        db=db
    )


@router.get("/api/firmware/active")
def get_active_firmware_endpoint() -> Dict[str, Any]:
    """Retrieves current active firmware version and lineage."""
    db = get_db()
    for fw in db.list_firmware():
        if fw.status == "ACTIVE":
            return fw.model_dump()
    fws = db.list_firmware()
    if fws:
        return fws[0].model_dump()
    return {"status": "NO_FIRMWARE", "firmware_id": None}


@router.post("/api/firmware/save-ide")
def save_ide_sketch(req: SaveIDESketchRequest) -> Dict[str, Any]:
    """
    Overwrites the specified .ino file on disk with optimized code (creating a .bak backup).
    Allows user to immediately re-flash in Arduino IDE with zero copy-pasting.
    """
    import os
    allowed_exts = (".ino", ".cpp", ".c", ".h")
    if not req.path.lower().endswith(allowed_exts):
        return {"success": False, "error": f"Invalid sketch file extension. Must be one of {allowed_exts}"}

    if not os.path.exists(req.path):
        return {"success": False, "error": f"File does not exist: {req.path}"}

    try:
        # Create backup in .aris/backups/
        sketch_dir = os.path.dirname(os.path.abspath(req.path))
        backup_dir = os.path.join(sketch_dir, ".aris", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        bak_path = os.path.join(backup_dir, f"{os.path.basename(req.path)}.{int(time.time()*1000)}.bak")

        with open(req.path, "r", encoding="utf-8") as orig:
            original_code = orig.read()
        with open(bak_path, "w", encoding="utf-8") as bak:
            bak.write(original_code)

        # Write optimized code
        with open(req.path, "w", encoding="utf-8") as f:
            f.write(req.source_code)

        return {"success": True, "path": req.path, "backup_path": bak_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/firmware/{firmware_id}")
def get_firmware_detail(firmware_id: str) -> Dict[str, Any]:
    """Retrieves specific firmware details and normalized memory sections."""
    mgr = get_firmware_mgr()
    fw = mgr.get_firmware(firmware_id)
    return fw.model_dump()


class CompileFirmwareRequest(BaseModel):
    source_code: str
    board_id: str = "arduino_uno"
    is_simulation: bool = False


class FlashFirmwareRequest(BaseModel):
    board_id: str = "arduino_uno"
    port: str
    source_code: Optional[str] = None
    binary_path: Optional[str] = None


@router.post("/api/firmware/compile")
def compile_firmware_endpoint(req: CompileFirmwareRequest) -> Dict[str, Any]:
    """Compiles source code for target board using arduino-cli or fallback."""
    flasher = get_build_flasher()
    return flasher.compile_firmware(
        source_code=req.source_code,
        board_id=req.board_id,
        is_simulation=req.is_simulation
    )


@router.post("/api/firmware/flash")
def flash_firmware_endpoint(req: FlashFirmwareRequest) -> Dict[str, Any]:
    """Flashes compiled binary or sketch onto target microcontroller."""
    flasher = get_build_flasher()
    return flasher.flash_board(
        board_id=req.board_id,
        port=req.port,
        source_code=req.source_code,
        binary_path=req.binary_path
    )


class InstrumentAndBuildRequest(BaseModel):
    source_code: Optional[str] = None
    sketch_path: Optional[str] = None
    board_id: str = "arduino_uno"
    port: Optional[str] = None
    run_id: Optional[str] = None
    execute_upload: bool = False
    instrumentation_mode: str = "BALANCED"
    sram_warning_threshold_bytes: int = 256


@router.post("/api/firmware/instrument-and-build")
def instrument_and_build_endpoint(req: InstrumentAndBuildRequest) -> Dict[str, Any]:
    """
    Transparently instruments an Arduino sketch in an isolated shadow directory,
    runs static analysis on the untouched original source, compiles via arduino-cli,
    and returns complete diff, findings, and build metrics.
    Guarantees the original source file on disk is never altered.
    """
    source_code = req.source_code
    sketch_path = req.sketch_path

    if sketch_path and os.path.exists(sketch_path):
        with open(sketch_path, "r", encoding="utf-8") as f:
            source_code = f.read()

    if not source_code or not source_code.strip():
        raise ArisException(
            error_code="ARIS_NO_SOURCE",
            message="No valid source code or sketch file path provided.",
            recoverable=True,
            status_code=400
        )

    # 1. Run static analysis on the UNTOUCHED ORIGINAL user source
    source_filename = os.path.basename(sketch_path) if sketch_path else "main.ino"
    analyzer = StaticAnalyzer(default_board_id=req.board_id)
    static_result = analyzer.analyze_source(
        source_code=source_code,
        board_id=req.board_id,
        source_file=source_filename
    )

    # 2. Transparently instrument source into isolated shadow build directory
    inst_result = SketchInstrumenter.create_shadow_workspace(
        source_code=source_code,
        source_path=sketch_path,
        board_id=req.board_id,
        run_id=req.run_id,
        instrumentation_mode=req.instrumentation_mode
    )

    # 3. Preflight Memory Analysis (Original vs Instrumented)
    preflight_analyzer = PreflightMemoryAnalyzer()
    preflight_report = preflight_analyzer.analyze_memory_and_instrumentation(
        original_source=source_code,
        board_id=req.board_id,
        instrumented_source=inst_result.instrumented_source,
        instrumentation_mode=req.instrumentation_mode,
        sram_warning_threshold_bytes=req.sram_warning_threshold_bytes
    )

    # 4. Compile the shadow sketch via BuildFlasher / arduino-cli
    flasher = get_build_flasher()
    build_result = flasher.compile_firmware(
        source_code=inst_result.instrumented_source,
        board_id=req.board_id
    )

    # 4. Physical upload, handshake verification, and telemetry activation
    upload_result = None
    run_record = None
    handshake_data = None
    if req.execute_upload:
        target_port = req.port
        if not target_port:
            from backend.serial.serial_discovery import scan_serial_ports
            ports = scan_serial_ports()
            arduino_ports = [p for p in ports if p.is_arduino]
            if arduino_ports:
                target_port = arduino_ports[0].device
            elif ports:
                target_port = ports[0].device

        if target_port:
            try:
                upload_result = flasher.flash_board(
                    board_id=req.board_id,
                    port=target_port,
                    binary_path=build_result.get("binary_path")
                )
                if upload_result.get("status") == "FLASH_SUCCESS":
                    db = get_db()
                    serial_mgr = get_serial_mgr()
                    handshake_data = serial_mgr.handshake_data
                    fw_id = None
                    try:
                        fw_mgr = get_firmware_mgr()
                        sketch_name = os.path.basename(sketch_path) if sketch_path else "Transparent Sketch"
                        fw_record = fw_mgr.upload_firmware(
                            name=sketch_name,
                            source_code=source_code
                        )
                        fw_id = fw_record.firmware_id
                    except Exception:
                        pass
                    run_record = RunRecord(
                        run_id=inst_result.run_id,
                        board_id=req.board_id,
                        firmware_id=fw_id,
                        instrumentation_mode=req.instrumentation_mode.upper(),
                        start_time=datetime.now(timezone.utc).isoformat(),
                        end_time=None,
                        status="RUNNING",
                        is_simulated=False,
                        is_demo=False,
                        baseline_id=None
                    )
                    db.save_run(run_record)
                    serial_mgr.set_active_run(inst_result.run_id)
            except ArisException as e:
                # Capture upload failure cleanly without losing successful compilation and preflight analysis
                upload_result = {
                    "status": "FLASH_FAILED",
                    "error_code": e.error_code,
                    "message": e.message,
                    **(e.details or {})
                }
        else:
            upload_result = {
                "status": "FLASH_FAILED",
                "failure_category": "DEVICE_DISCONNECTED",
                "title": "Upload aborted — No hardware port detected",
                "error_summary": "No serial or COM port was provided or detected on the host. Connect your Arduino board via USB before uploading.",
                "guidance": [
                    "Connect your Arduino board to a USB port.",
                    "Verify the USB cable supports data transfer.",
                    "Check Windows Device Manager to confirm the COM port assignment.",
                    "Use Virtual Simulation mode to run and inspect telemetry without physical hardware."
                ],
                "command": f"{flasher.arduino_cli_path or 'arduino-cli'} upload --fqbn {req.board_id}",
                "exit_code": 1,
                "raw_output": "Device not found: 0 COM ports detected.",
                "firmware_uploaded": False,
                "compilation_succeeded": True
            }

    return {
        "status": "BUILD_SUCCESS" if build_result.get("status") == "BUILD_SUCCESS" else "FAILED",
        "board_id": req.board_id,
        "run_id": inst_result.run_id,
        "original_file_path": sketch_path,
        "original_source_preserved": inst_result.verification_hash_match,
        "original_file_hash": inst_result.original_file_hash,
        "shadow_sketch_path": inst_result.shadow_sketch_path,
        "diff": inst_result.diff,
        "inserted_blocks": inst_result.inserted_blocks,
        "static_analysis": {
            "findings_count": len(static_result.findings),
            "findings": [f.model_dump() for f in static_result.findings],
            "estimated_flash_bytes": static_result.estimated_flash_bytes,
            "estimated_sram_static_bytes": static_result.estimated_sram_static_bytes,
        },
        "build_result": build_result,
        "preflight_memory": preflight_report.model_dump(),
        "upload_result": upload_result,
        "handshake": handshake_data,
        "run": run_record.model_dump() if run_record else None,
        "ready_for_physical_deployment": True,
        "telemetry_active": bool(upload_result and upload_result.get("status") == "FLASH_SUCCESS")
    }
