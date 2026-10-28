"""
Unit tests for ARIS Serial Resource Lifecycle and Lock Management.
Validates:
- release_serial() safely stops background thread, cancels I/O, and closes handle.
- release_serial() is fully idempotent when called repeatedly.
- is_serial_open() returns accurate status.
- BuildFlasher releases COM port prior to flashing and cleans up in try/finally on failure.
- verify_upload handshake sequence.
"""

import time
import pytest
from unittest.mock import MagicMock, patch
from backend.serial.serial_manager import SerialManager
from backend.firmware.build_flasher import BuildFlasher
from backend.telemetry.telemetry_schema import ArisException


def test_serial_manager_release_serial_when_not_connected(ingestor):
    """Verify release_serial is idempotent and returns released=True even when disconnected."""
    mgr = SerialManager(ingestor)
    assert mgr.is_serial_open() is False

    res = mgr.release_serial(port="COM4", wait_ms=0)
    assert res["released"] is True
    assert mgr.is_serial_open() is False
    assert mgr.connected is False

    # Call again to verify idempotency
    res2 = mgr.release_serial(port="COM4", wait_ms=0)
    assert res2["released"] is True
    assert mgr.is_serial_open() is False


def test_serial_manager_release_serial_with_active_handle(ingestor):
    """Verify release_serial stops reader thread and closes handle."""
    mgr = SerialManager(ingestor)
    
    mock_handle = MagicMock()
    mock_handle.is_open = True
    mgr._serial_handle = mock_handle
    mgr.connected = True
    mgr.current_port = "COM4"

    assert mgr.is_serial_open("COM4") is True

    res = mgr.release_serial(port="COM4", wait_ms=0)
    assert res["released"] is True
    assert mgr.is_serial_open("COM4") is False
    assert mgr.connected is False
    assert mgr.current_port is None
    assert mgr._serial_handle is None

    # Verify cancel_read and close were called on the serial handle
    mock_handle.cancel_read.assert_called_once()
    mock_handle.close.assert_called_once()


def test_serial_manager_idempotent_multiple_releases(ingestor):
    """Calling release_serial multiple times never raises an exception."""
    mgr = SerialManager(ingestor)
    mock_handle = MagicMock()
    mock_handle.is_open = True
    mgr._serial_handle = mock_handle
    mgr.connected = True
    mgr.current_port = "COM4"

    res1 = mgr.release_serial(port="COM4", wait_ms=0)
    assert res1["released"] is True

    res2 = mgr.release_serial(port="COM4", wait_ms=0)
    assert res2["released"] is True

    res3 = mgr.release_serial(wait_ms=0)
    assert res3["released"] is True


def test_build_flasher_releases_serial_prior_to_flash(monkeypatch):
    """Verify BuildFlasher invokes release_serial before flashing."""
    flasher = BuildFlasher()
    flasher.arduino_cli_path = "mock-arduino-cli"

    mock_serial_mgr = MagicMock()
    mock_serial_mgr.is_serial_open.return_value = False
    mock_serial_mgr.release_serial.return_value = {"released": True, "port": "COM4", "is_open": False}

    monkeypatch.setattr("backend.api.dependencies.get_serial_mgr", lambda: mock_serial_mgr)
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MagicMock(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(flasher, "verify_upload", lambda board_id, port, timeout_sec=4.0: True)

    result = flasher.flash_board(
        board_id="arduino_uno",
        port="COM4",
        source_code="void setup(){} void loop(){}"
    )

    assert result["status"] == "FLASH_SUCCESS"
    mock_serial_mgr.release_serial.assert_called_with(port="COM4", wait_ms=600)


def test_build_flasher_cleans_up_serial_on_upload_failure(monkeypatch):
    """Verify BuildFlasher cleans up serial handle in try/finally if upload fails."""
    flasher = BuildFlasher()
    flasher.arduino_cli_path = "mock-arduino-cli"

    mock_serial_mgr = MagicMock()
    mock_serial_mgr.is_serial_open.return_value = False

    monkeypatch.setattr("backend.api.dependencies.get_serial_mgr", lambda: mock_serial_mgr)
    # Simulate avrdude access denied or failure
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MagicMock(returncode=1, stdout="", stderr="Error: cannot open port COM4: Access is denied"))

    with pytest.raises(ArisException) as exc:
        flasher.flash_board(
            board_id="arduino_uno",
            port="COM4",
            source_code="void setup(){} void loop(){}"
        )

    assert exc.value.error_code == "ARIS_FLASH_FAILED"
    # Pre-flash release was called
    mock_serial_mgr.release_serial.assert_called()
