"""
Unit tests for ARIS Serial Communication Layer.
Verifies:
- Dynamic port scanning without hardcoded port paths
- Discovered port metadata parsing
- Connection error handling with canonical ARIS_SERIAL_DISCONNECTED error
"""

import pytest
from backend.serial.serial_discovery import scan_serial_ports, DiscoveredPort
from backend.serial.serial_manager import SerialManager
from backend.telemetry.telemetry_schema import ArisException


def test_scan_serial_ports():
    """Verify scanning returns list of DiscoveredPort instances."""
    ports = scan_serial_ports()
    assert isinstance(ports, list)
    for p in ports:
        assert isinstance(p, DiscoveredPort)
        d = p.to_dict()
        assert "device" in d
        assert "is_arduino" in d


def test_serial_manager_invalid_port_raises_canonical_error(ingestor):
    """Verify connecting to a nonexistent port raises ARIS_SERIAL_DISCONNECTED."""
    mgr = SerialManager(ingestor)
    with pytest.raises(ArisException) as exc:
        mgr.connect(port="NONEXISTENT_PORT_XYZ", baud_rate=115200)

    err = exc.value
    assert err.error_code == "ARIS_SERIAL_DISCONNECTED"
    assert err.recoverable is True
    assert mgr.connected is False


def test_serial_manager_status(ingestor):
    """Verify serial status representation."""
    mgr = SerialManager(ingestor)
    status = mgr.get_status()
    assert status["connected"] is False
    assert status["port"] is None
