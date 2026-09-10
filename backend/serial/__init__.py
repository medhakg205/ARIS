"""
ARIS Serial Communication Layer.
"""

from .serial_discovery import DiscoveredPort, scan_serial_ports
from .serial_manager import SerialManager

__all__ = [
    "DiscoveredPort",
    "scan_serial_ports",
    "SerialManager"
]
