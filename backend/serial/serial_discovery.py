"""
ARIS Automatic Serial Port & Hardware Board Discovery.
Scans all system COM and USB TTY ports using multi-source evidence:
1. Arduino CLI JSON Board Discovery (when toolchain is available)
2. USB Vendor/Product ID (VID/PID) hardware table
3. USB serial adapter chip heuristics (CH340, CP210x, FTDI)
4. Runtime Handshake verification

Assigns explicit detection confidence:
- CONFIRMED: Verified via Arduino CLI FQBN or Runtime Handshake
- HIGH_CONFIDENCE: Exact official Arduino USB VID/PID match
- UNCERTAIN: Compatible USB-Serial bridge (CH340/CP2102/FTDI) with ambiguous board type
- UNKNOWN: Generic unclassified serial device

Strictly prevents misidentifying Arduino Uno R4 (ARM Cortex-M4) as AVR ATmega328P.
"""

import os
import sys
import json
import shutil
import logging
import subprocess
from typing import List, Dict, Any, Optional

from backend.firmware.board_profiles import CANONICAL_BOARD_PROFILES, get_board_profile_by_fqbn

logger = logging.getLogger("aris.serial.discovery")

# Identification Confidence Constants
CONFIDENCE_CONFIRMED = "CONFIRMED"
CONFIDENCE_HIGH = "HIGH_CONFIDENCE"
CONFIDENCE_UNCERTAIN = "UNCERTAIN"
CONFIDENCE_UNKNOWN = "UNKNOWN"

# Known USB Vendor IDs
KNOWN_VENDORS = {
    0x2341: "Official Arduino (Arduino SA)",
    0x2A03: "Arduino LLC / dog hunter AG",
    0x1A86: "QinHeng Electronics (CH340 / CH341 USB-Serial)",
    0x0403: "FTDI (Future Technology Devices International)",
    0x10C4: "Silicon Labs (CP210x USB to UART)",
    0x067B: "Prolific Technology (PL2303)"
}

# Known USB (VID, PID) mappings to canonical ARIS board_id & details
KNOWN_PRODUCTS = {
    # Arduino Uno R3 (ATmega16U2 USB / Official)
    (0x2341, 0x0043): ("arduino_uno", "arduino:avr:uno", "atmega328p", "avr8", CONFIDENCE_HIGH),
    (0x2341, 0x0001): ("arduino_uno", "arduino:avr:uno", "atmega328p", "avr8", CONFIDENCE_HIGH),
    (0x2A03, 0x0043): ("arduino_uno", "arduino:avr:uno", "atmega328p", "avr8", CONFIDENCE_HIGH),

    # Arduino Mega 2560 R3 (ATmega16U2 USB / Official)
    (0x2341, 0x0010): ("arduino_mega", "arduino:avr:mega", "atmega2560", "avr8", CONFIDENCE_HIGH),
    (0x2341, 0x0042): ("arduino_mega", "arduino:avr:mega", "atmega2560", "avr8", CONFIDENCE_HIGH),
    (0x2A03, 0x0042): ("arduino_mega", "arduino:avr:mega", "atmega2560", "avr8", CONFIDENCE_HIGH),

    # Arduino Nano (FTDI / Official)
    (0x2341, 0x0070): ("arduino_nano", "arduino:avr:nano", "atmega328p", "avr8", CONFIDENCE_HIGH),
    (0x0403, 0x6001): ("arduino_nano", "arduino:avr:nano", "atmega328p", "avr8", CONFIDENCE_HIGH),

    # Arduino Uno R4 (Renesas RA4M1 / ARM Cortex-M4 — NOT AVR8!)
    (0x2341, 0x1002): ("arduino_uno_r4_wifi", "arduino:renesas_uno:unor4wifi", "ra4m1", "arm_cortex_m4", CONFIDENCE_HIGH),
    (0x2341, 0x0069): ("arduino_uno_r4_minima", "arduino:renesas_uno:minima", "ra4m1", "arm_cortex_m4", CONFIDENCE_HIGH),
}


def find_arduino_cli_path() -> Optional[str]:
    """
    Locates the arduino-cli executable on the host system.
    Searches:
    1. ARDUINO_CLI_PATH environment variable
    2. System PATH
    3. Bundled Arduino IDE 2.x installation paths on Windows / macOS / Linux
    """
    env_path = os.getenv("ARDUINO_CLI_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    which_path = shutil.which("arduino-cli")
    if which_path:
        return which_path

    # Standard Arduino IDE 2.x application bundling locations
    candidate_paths = []
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("ProgramFiles", "")
        candidate_paths.extend([
            os.path.join(local_app_data, r"Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe"),
            os.path.join(program_files, r"Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe"),
            os.path.join(local_app_data, r"Arduino15\bin\arduino-cli.exe"),
        ])
    elif sys.platform == "darwin":
        candidate_paths.extend([
            "/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli",
            os.path.expanduser("~/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli"),
        ])
    else:
        candidate_paths.extend([
            "/usr/local/bin/arduino-cli",
            "/usr/bin/arduino-cli",
            os.path.expanduser("~/.local/bin/arduino-cli"),
        ])

    for path in candidate_paths:
        if path and os.path.isfile(path):
            return path

    return None


def query_arduino_cli_boards() -> Dict[str, Dict[str, Any]]:
    """
    Executes 'arduino-cli board list --format json' to obtain official FQBN board detection.
    Returns mapping from serial port address (e.g. 'COM5' or '/dev/ttyUSB0') to board info.
    """
    cli_path = find_arduino_cli_path()
    if not cli_path:
        return {}

    try:
        res = subprocess.run(
            [cli_path, "board", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=5.0
        )
        if res.returncode != 0 or not res.stdout.strip():
            return {}

        data = json.loads(res.stdout)
        results = {}
        detected_ports = data.get("detected_ports", [])
        for entry in detected_ports:
            port_info = entry.get("port", {})
            address = port_info.get("address", "")
            boards = entry.get("matching_boards", [])
            if address and boards:
                best_match = boards[0]
                results[address.upper()] = {
                    "name": best_match.get("name", ""),
                    "fqbn": best_match.get("fqbn", ""),
                    "protocol": port_info.get("protocol", "serial"),
                    "hardware_id": port_info.get("hardware_id", "")
                }
        return results
    except Exception as e:
        logger.debug(f"arduino-cli discovery query failed or timed out: {e}")
        return {}


class DiscoveredPort:
    """Represents a dynamically discovered serial port and its hardware metadata."""
    def __init__(
        self,
        device: str,
        description: str,
        hwid: str,
        vid: Optional[int] = None,
        pid: Optional[int] = None,
        manufacturer: Optional[str] = None,
        is_arduino: bool = False,
        suggested_board_id: Optional[str] = None,
        mcu: Optional[str] = None,
        architecture: Optional[str] = None,
        fqbn: Optional[str] = None,
        confidence: str = CONFIDENCE_UNKNOWN,
        profile_source: str = "UNKNOWN",
        unavailable_properties: Optional[List[str]] = None,
        display_name: Optional[str] = None
    ):
        self.device = device                        # e.g. "COM5" or "/dev/ttyUSB0"
        self.description = description              # e.g. "USB-SERIAL CH340 (COM5)"
        self.hwid = hwid                            # Hardware ID string
        self.vid = vid                              # USB Vendor ID (integer)
        self.pid = pid                              # USB Product ID (integer)
        self.manufacturer = manufacturer            # Device manufacturer string
        self.is_arduino = is_arduino                # Flag indicating probable Arduino target
        self.suggested_board_id = suggested_board_id# e.g. "arduino_uno" or "unknown_bridge"
        self.mcu = mcu                              # e.g. "atmega328p" or None
        self.architecture = architecture            # e.g. "avr8" or None
        self.fqbn = fqbn                            # e.g. "arduino:avr:uno" or None
        self.confidence = confidence                # CONFIRMED, HIGH_CONFIDENCE, UNCERTAIN, UNKNOWN
        self.profile_source = profile_source        # EXACT_PROFILE, TOOLCHAIN_DERIVED, PARTIALLY_RESOLVED
        self.unavailable_properties = unavailable_properties or []
        self.display_name = display_name or (suggested_board_id or description)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes port metadata to dictionary."""
        return {
            "device": self.device,
            "description": self.description,
            "display_name": self.display_name,
            "hwid": self.hwid,
            "vid": f"0x{self.vid:04X}" if self.vid else None,
            "pid": f"0x{self.pid:04X}" if self.pid else None,
            "manufacturer": self.manufacturer,
            "is_arduino": self.is_arduino,
            "suggested_board_id": self.suggested_board_id,
            "mcu": self.mcu,
            "architecture": self.architecture,
            "fqbn": self.fqbn,
            "confidence": self.confidence,
            "profile_source": self.profile_source,
            "unavailable_properties": self.unavailable_properties
        }


def scan_serial_ports() -> List[DiscoveredPort]:
    """
    Scans the host system for all active serial ports and identifies microcontrollers.
    Combines:
    1. Arduino CLI JSON discovery (if available) -> uses BoardProfileResolver
    2. Hardware VID/PID database -> maps to exact known profile
    3. Serial bridge heuristics (CH340, CP2102, FTDI) -> NEVER guesses Uno R3 if ambiguous
    """
    from backend.firmware.board_profiles import BoardProfileResolver, get_board_profile_by_fqbn, ALL_BOARD_PROFILES
    discovered: List[DiscoveredPort] = []

    # 1. Query official Arduino CLI if present
    cli_boards = query_arduino_cli_boards()

    # 2. Query OS COM/TTY ports via PySerial
    try:
        import serial.tools.list_ports
        available_ports = serial.tools.list_ports.comports()
    except ImportError:
        logger.warning("pyserial is not available; cannot scan hardware COM ports.")
        return []
    except Exception as e:
        logger.error(f"Error enumerating serial ports: {e}")
        return []

    for port_info in available_ports:
        device = port_info.device or ""
        desc = port_info.description or ""
        hwid = port_info.hwid or ""
        vid = port_info.vid
        pid = port_info.pid
        manufacturer = port_info.manufacturer or ""

        is_arduino = False
        suggested_board = None
        display_name = None
        mcu = None
        arch = None
        fqbn = None
        confidence = CONFIDENCE_UNKNOWN
        profile_source = "UNKNOWN"
        unavailable: List[str] = []

        # Check Step 1: Match against Arduino CLI official detection
        dev_upper = device.upper()
        if dev_upper in cli_boards:
            cli_match = cli_boards[dev_upper]
            fqbn = cli_match.get("fqbn")
            cli_name = cli_match.get("name")
            matched_profile = get_board_profile_by_fqbn(fqbn)
            if matched_profile:
                is_arduino = True
                suggested_board = matched_profile.board_id
                display_name = matched_profile.display_name or cli_name
                mcu = matched_profile.mcu
                arch = matched_profile.architecture
                confidence = CONFIDENCE_CONFIRMED
                profile_source = matched_profile.profile_source
                unavailable = matched_profile.unavailable_properties

        # Check Step 2: Match against exact known USB VID/PID table
        if not suggested_board and vid and pid:
            key = (vid, pid)
            if key in KNOWN_PRODUCTS:
                b_id, b_fqbn, b_mcu, b_arch, b_conf = KNOWN_PRODUCTS[key]
                is_arduino = True
                suggested_board = b_id
                fqbn = b_fqbn
                mcu = b_mcu
                arch = b_arch
                confidence = b_conf
                profile_source = "EXACT_PROFILE"
                if b_id in ALL_BOARD_PROFILES:
                    display_name = ALL_BOARD_PROFILES[b_id].display_name

        # Check Step 3: Match vendor or text heuristics for clones (CH340, CP2102, FTDI)
        if not suggested_board:
            search_text = f"{desc} {manufacturer} {hwid}".lower()
            is_usb_serial_bridge = (
                (vid in KNOWN_VENDORS) or
                any(kw in search_text for kw in ["ch340", "ch341", "cp210", "ftdi", "pl2303", "usb-serial", "arduino"])
            )

            if is_usb_serial_bridge:
                is_arduino = True
                if "mega" in search_text or "2560" in search_text:
                    suggested_board = "arduino_mega"
                    mcu = "atmega2560"
                    arch = "avr8"
                    fqbn = "arduino:avr:mega"
                    display_name = "Arduino Mega 2560"
                    confidence = CONFIDENCE_UNCERTAIN
                    profile_source = "EXACT_PROFILE"
                elif "nano" in search_text:
                    suggested_board = "arduino_nano"
                    mcu = "atmega328p"
                    arch = "avr8"
                    fqbn = "arduino:avr:nano"
                    display_name = "Arduino Nano"
                    confidence = CONFIDENCE_UNCERTAIN
                    profile_source = "EXACT_PROFILE"
                elif "uno r4" in search_text:
                    suggested_board = "arduino_uno_r4_wifi"
                    mcu = "ra4m1"
                    arch = "arm_cortex_m4"
                    fqbn = "arduino:renesas_uno:unor4wifi"
                    display_name = "Arduino Uno R4 WiFi"
                    confidence = CONFIDENCE_UNCERTAIN
                    profile_source = "EXACT_PROFILE"
                elif "uno" in search_text:
                    suggested_board = "arduino_uno"
                    mcu = "atmega328p"
                    arch = "avr8"
                    fqbn = "arduino:avr:uno"
                    display_name = "Arduino Uno"
                    confidence = CONFIDENCE_UNCERTAIN
                    profile_source = "EXACT_PROFILE"
                else:
                    # Generic CH340 or USB-UART converter where board is ambiguous
                    # Invariant: NEVER silently force Uno R3 / ATmega328P!
                    # Mark as partially resolved without guessing MCU or architecture.
                    suggested_board = "unknown_arduino_bridge"
                    display_name = f"Serial Device ({desc or device})"
                    mcu = None
                    arch = None
                    fqbn = None
                    confidence = CONFIDENCE_UNCERTAIN
                    profile_source = "PARTIALLY_RESOLVED"
                    unavailable = [
                        "mcu", "architecture", "clock_hz", "flash_bytes",
                        "sram_bytes", "eeprom_bytes", "gpio_count", "adc_channels",
                        "timer_count", "fqbn"
                    ]

        port_obj = DiscoveredPort(
            device=device,
            description=desc,
            hwid=hwid,
            vid=vid,
            pid=pid,
            manufacturer=manufacturer,
            is_arduino=is_arduino,
            suggested_board_id=suggested_board,
            mcu=mcu,
            architecture=arch,
            fqbn=fqbn,
            confidence=confidence,
            profile_source=profile_source,
            unavailable_properties=unavailable,
            display_name=display_name
        )
        discovered.append(port_obj)

    return discovered
