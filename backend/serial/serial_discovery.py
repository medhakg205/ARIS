"""
ARIS Automatic Serial Port Discovery.
Dynamically scans all system COM and USB TTY ports to identify connected microcontrollers.
Identifies official Arduino boards, CH340 clones, FTDI serial converters, and CP210x adapters.
Never hardcodes port identifiers (COM3, COM4, /dev/ttyUSB0, etc.).
"""

import sys
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("aris.serial.discovery")

# Known USB Vendor IDs commonly associated with Arduino and USB-Serial bridges
KNOWN_VENDORS = {
    0x2341: "Official Arduino (Arduino SA)",
    0x2A03: "Arduino LLC / dog hunter AG",
    0x1A86: "QinHeng Electronics (CH340 / CH341 USB-Serial)",
    0x0403: "FTDI (Future Technology Devices International)",
    0x10C4: "Silicon Labs (CP210x USB to UART)",
    0x067B: "Prolific Technology (PL2303)"
}

# Known USB Product IDs for specific Arduino models
KNOWN_PRODUCTS = {
    # Arduino Uno R3 & clones
    (0x2341, 0x0043): "arduino_uno",
    (0x2341, 0x0001): "arduino_uno",
    (0x2A03, 0x0043): "arduino_uno",
    (0x1A86, 0x7523): "arduino_uno",  # CH340 Uno / Nano clone default
    (0x1A86, 0x5523): "arduino_uno",  # CH341
    (0x10C4, 0xEA60): "arduino_nano", # CP2102 Nano clone
    # Arduino Mega 2560 R3 & clones
    (0x2341, 0x0010): "arduino_mega",
    (0x2341, 0x0042): "arduino_mega",
    (0x2A03, 0x0042): "arduino_mega",
    # Arduino Nano
    (0x2341, 0x0070): "arduino_nano",
    (0x0403, 0x6001): "arduino_nano",  # Traditional FTDI Nano
}


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
        suggested_board_id: Optional[str] = None
    ):
        self.device = device                        # e.g. "COM5" or "/dev/ttyUSB0"
        self.description = description              # e.g. "USB-SERIAL CH340 (COM5)"
        self.hwid = hwid                            # Hardware ID string
        self.vid = vid                              # USB Vendor ID (hex integer)
        self.pid = pid                              # USB Product ID (hex integer)
        self.manufacturer = manufacturer            # Device manufacturer string
        self.is_arduino = is_arduino                # Flag indicating probable Arduino target
        self.suggested_board_id = suggested_board_id# e.g. "arduino_uno" if recognized

    def to_dict(self) -> Dict[str, Any]:
        """Serializes port metadata to dictionary."""
        return {
            "device": self.device,
            "description": self.description,
            "hwid": self.hwid,
            "vid": f"0x{self.vid:04X}" if self.vid else None,
            "pid": f"0x{self.pid:04X}" if self.pid else None,
            "manufacturer": self.manufacturer,
            "is_arduino": self.is_arduino,
            "suggested_board_id": self.suggested_board_id
        }


def scan_serial_ports() -> List[DiscoveredPort]:
    """
    Scans the host system for all active serial ports and identifies microcontrollers.
    Does not require hardcoded port paths.
    """
    discovered: List[DiscoveredPort] = []

    try:
        import serial.tools.list_ports
        available_ports = serial.tools.list_ports.comports()
    except ImportError:
        logger.warning("pyserial is not installed or available; cannot scan hardware COM ports.")
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

        # Determine if this port matches known Arduino hardware
        is_arduino = False
        suggested_board = None

        # Check VID/PID exact mapping
        if vid and pid and (vid, pid) in KNOWN_PRODUCTS:
            is_arduino = True
            suggested_board = KNOWN_PRODUCTS[(vid, pid)]
        elif vid and vid in KNOWN_VENDORS:
            is_arduino = True

        # Check text heuristics in description and manufacturer
        search_text = f"{desc} {manufacturer} {hwid}".lower()
        if any(keyword in search_text for keyword in ["arduino", "ch340", "ch341", "ftdi", "cp210", "atmega"]):
            is_arduino = True
            if "mega" in search_text or "2560" in search_text:
                suggested_board = "arduino_mega"
            elif "nano" in search_text:
                suggested_board = "arduino_nano"
            elif "uno" in search_text:
                suggested_board = "arduino_uno"

        # If it's an Arduino but board couldn't be distinguished, default suggestion is Uno
        if is_arduino and not suggested_board:
            suggested_board = "arduino_uno"

        port_obj = DiscoveredPort(
            device=device,
            description=desc,
            hwid=hwid,
            vid=vid,
            pid=pid,
            manufacturer=manufacturer,
            is_arduino=is_arduino,
            suggested_board_id=suggested_board
        )
        discovered.append(port_obj)

    return discovered
