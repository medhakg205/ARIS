"""
Regression tests for ARIS firmware deployment sequencing, port ownership,
concurrency control, error categorization, and non-blocking release.
"""

import threading
import pytest
from unittest.mock import MagicMock, patch

from backend.serial.serial_manager import SerialManager
from backend.telemetry.telemetry_schema import ArisException
from backend.firmware.build_flasher import BuildFlasher


class MockIngestor:
    def ingest_raw_line(self, line: str, active_run_id=None):
        pass


def test_serial_handles_released_before_upload():
    """Verify serial handles and reader threads are released before upload."""
    ingestor = MockIngestor()
    sm = SerialManager(ingestor)
    sm.connected = True
    sm.current_port = "COM4"
    mock_handle = MagicMock()
    mock_handle.is_open = True
    sm._serial_handle = mock_handle

    # Begin deployment must release COM4 and set deployment active
    sm.begin_deployment("COM4")
    assert sm.is_deployment_active() is True
    assert sm.connected is False
    assert sm.is_serial_open("COM4") is False
    assert mock_handle.close.called

    sm.end_deployment("COM4")
    assert sm.is_deployment_active() is False


def test_port_polling_and_autodetect_paused_during_deployment():
    """Verify auto-detect and connect are suppressed when deployment is active."""
    ingestor = MockIngestor()
    sm = SerialManager(ingestor)
    sm.begin_deployment("COM4")

    # Connect to same port during deployment must raise ARIS_SERIAL_BUSY
    with pytest.raises(ArisException) as exc_info:
        sm.connect("COM4")
    assert exc_info.value.error_code == "ARIS_SERIAL_BUSY"

    # Connect without port (any) during deployment must also be blocked
    with pytest.raises(ArisException) as exc_info2:
        sm.connect("")
    assert exc_info2.value.error_code == "ARIS_SERIAL_BUSY"

    sm.end_deployment("COM4")


def test_concurrent_deployments_prevented():
    """Verify concurrent deployment requests on the same or different port are rejected."""
    ingestor = MockIngestor()
    sm = SerialManager(ingestor)
    sm.begin_deployment("COM4")

    # Second deployment attempt must raise ARIS_CONCURRENT_DEPLOYMENT
    with pytest.raises(ArisException) as exc_info:
        sm.begin_deployment("COM4")
    assert exc_info.value.error_code == "ARIS_CONCURRENT_DEPLOYMENT"
    assert "already in progress" in str(exc_info.value.message)

    sm.end_deployment("COM4")


def test_detection_restored_after_success_and_failure():
    """Verify deployment lock is always released after success and failure."""
    ingestor = MockIngestor()
    sm = SerialManager(ingestor)

    # Success scenario
    sm.begin_deployment("COM4")
    assert sm.is_deployment_active() is True
    sm.end_deployment("COM4")
    assert sm.is_deployment_active() is False

    # Failure scenario in BuildFlasher
    flasher = BuildFlasher(use_simulated_toolchain_if_missing=True)
    with patch("backend.api.dependencies.get_serial_mgr", return_value=sm):
        with pytest.raises(ArisException):
            flasher.flash_board("arduino_uno", "COM4", fail_simulation=True)

    # Ensure deployment is NOT active after flash_board failure
    assert sm.is_deployment_active() is False


def test_exceptions_and_timeouts_do_not_leave_port_locked():
    """Verify that timeout during upload guarantees deployment mode is terminated."""
    ingestor = MockIngestor()
    sm = SerialManager(ingestor)
    flasher = BuildFlasher(use_simulated_toolchain_if_missing=False)
    flasher.arduino_cli_path = "dummy_cli"

    import subprocess
    with patch("backend.api.dependencies.get_serial_mgr", return_value=sm):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 60.0)):
            with pytest.raises(ArisException) as exc_info:
                flasher.flash_board("arduino_uno", "COM4", source_code="void setup(){}")
            assert exc_info.value.error_code == "ARIS_FLASH_FAILED"
            assert exc_info.value.details.get("failure_category") == "UPLOAD_TIMEOUT"

    # Port lock must be completely cleared
    assert sm.is_deployment_active() is False
    assert not sm._deployment_lock.locked()


def test_error_classification_port_access_denied():
    """Verify access-denied error is classified as PORT_ACCESS_DENIED with actionable advice."""
    flasher = BuildFlasher(use_simulated_toolchain_if_missing=False)
    flasher.arduino_cli_path = "dummy_cli"

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = '{"error": "Failed uploading: uploading error: exit status 1", "output": {"stderr": "Error: cannot open port \\\\\\\\.\\\\COM4: Access is denied.\\r\\n"}}'
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        with pytest.raises(ArisException) as exc_info:
            flasher.flash_board("arduino_uno", "COM4", source_code="void setup(){}")

        assert exc_info.value.error_code == "ARIS_FLASH_FAILED"
        details = exc_info.value.details
        assert details.get("failure_category") == "PORT_ACCESS_DENIED"
        assert "in use" in details.get("error_summary", "") or "access was denied" in details.get("error_summary", "")
        assert any("Serial Monitor" in g for g in details.get("guidance", []))
        assert details.get("firmware_uploaded") is False


def test_error_classification_bootloader_unresponsive():
    """Verify bootloader sync failure is classified as BOOTLOADER_UNRESPONSIVE."""
    flasher = BuildFlasher(use_simulated_toolchain_if_missing=False)
    flasher.arduino_cli_path = "dummy_cli"

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = ""
    mock_proc.stderr = "Error: programmer is not responding\nWarning: attempt 1 of 10: not in sync: resp=0x00"

    with patch("subprocess.run", return_value=mock_proc):
        with pytest.raises(ArisException) as exc_info:
            flasher.flash_board("arduino_uno", "COM4", source_code="void setup(){}")

        assert exc_info.value.error_code == "ARIS_FLASH_FAILED"
        details = exc_info.value.details
        assert details.get("failure_category") == "BOOTLOADER_UNRESPONSIVE"
        assert "bootloader synchronization" in details.get("error_summary", "")
        assert any("RESET button" in g for g in details.get("guidance", []))
        assert details.get("firmware_uploaded") is False


def test_failed_upload_does_not_create_false_run_or_telemetry():
    """Verify failed physical upload preserves compilation but does not create RUNNING run."""
    from backend.api.routes_firmware import instrument_and_build_endpoint, InstrumentAndBuildRequest

    mock_flasher = MagicMock()
    mock_flasher.compile_firmware.return_value = {
        "status": "BUILD_SUCCESS",
        "board_id": "arduino_uno",
        "binary_size_bytes": 15589,
        "flash_usage_pct": 47.57,
        "sram_usage_bytes": 1621,
        "sram_usage_pct": 79.15,
        "compiler_output": "Compilation successful",
        "binary_path": "/tmp/test.hex"
    }
    # Simulate upload failure
    mock_flasher.flash_board.side_effect = ArisException(
        error_code="ARIS_FLASH_FAILED",
        message="Port access denied",
        details={
            "failure_category": "PORT_ACCESS_DENIED",
            "error_summary": "Port COM4 locked by another process",
            "firmware_uploaded": False
        }
    )

    req = InstrumentAndBuildRequest(
        source_code="void setup() { Serial.begin(115200); } void loop() {}",
        board_id="arduino_uno",
        port="COM4",
        execute_upload=True
    )

    with patch("backend.api.routes_firmware.get_build_flasher", return_value=mock_flasher):
        res = instrument_and_build_endpoint(req)

        # Compilation succeeded
        assert res["status"] == "BUILD_SUCCESS"
        assert res["build_result"]["status"] == "BUILD_SUCCESS"

        # Upload failure captured cleanly without crashing endpoint
        assert res["upload_result"]["status"] == "FLASH_FAILED"
        assert res["upload_result"]["failure_category"] == "PORT_ACCESS_DENIED"

        # Telemetry must NOT be active
        assert res["telemetry_active"] is False

        # No run record created
        assert res["run"] is None
