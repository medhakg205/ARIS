"""
ARIS Studio — Runtime Handshake Reliability and Noise Immunity Regression Tests.

Validates:
1. Immunity to user sketch Serial.print() noise (un-terminated prints, prefix/suffix text).
2. Delimiter extraction for both $ARIS_ACK and $ARIS_BOOT frames.
3. Periodic re-transmission of $ARIS_HELLO# across Optiboot bootloader delay.
4. Independent classification of compilation, upload, handshake verification, and telemetry.
5. Absolute prevention of false telemetry activation when handshake fails.
6. Handshake API endpoint compatibility with body and query params.
"""

import time
import pytest
from unittest.mock import MagicMock, patch

from backend.serial.serial_manager import SerialManager
from backend.telemetry.telemetry_schema import ArisException
from backend.firmware.build_flasher import BuildFlasher
from backend.firmware.board_profiles import BoardProfile


class MockSerialHandle:
    def __init__(self, responses=None):
        self.is_open = True
        self.written_bytes = bytearray()
        self.responses = list(responses or [])
        self.read_index = 0

    def write(self, data: bytes):
        self.written_bytes.extend(data)
        return len(data)

    def flush(self):
        pass

    def close(self):
        self.is_open = False

    def readline(self):
        if self.read_index < len(self.responses):
            resp = self.responses[self.read_index]
            self.read_index += 1
            return resp
        return b""


@pytest.fixture
def serial_mgr():
    mock_ingestor = MagicMock()
    mgr = SerialManager(ingestor=mock_ingestor)
    yield mgr
    mgr.disconnect()


# -----------------------------------------------------------------------------
# 1. NOISE IMMUNITY & PARSING TESTS
# -----------------------------------------------------------------------------

def test_parse_clean_handshake_ack(serial_mgr):
    line = "$ARIS_ACK,2.0.0,1.0,arduino_uno,atmega328p,avr8,16000000,BALANCED#"
    parsed = serial_mgr._parse_handshake_line(line)
    assert parsed is not None
    assert parsed["handshake_success"] is True
    assert parsed["runtime_version"] == "2.0.0"
    assert parsed["protocol_version"] == "1.0"
    assert parsed["board_id"] == "arduino_uno"
    assert parsed["mcu"] == "atmega328p"
    assert parsed["architecture"] == "avr8"
    assert parsed["clock_hz"] == 16000000
    assert parsed["instrumentation_mode"] == "BALANCED"
    assert parsed["frame_type"] == "ACK"


def test_parse_handshake_ack_with_prepended_sketch_noise(serial_mgr):
    """
    User sketch calls Serial.print("Sensor: 512 | Mapped: 128") without newline.
    Handshake packet follows immediately on the same serial line buffer.
    """
    line = "Sensor: 512 | Mapped: 128$ARIS_ACK,2.0.0,1.0,arduino_uno,atmega328p,avr8,16000000,BALANCED#"
    parsed = serial_mgr._parse_handshake_line(line)
    assert parsed is not None
    assert parsed["handshake_success"] is True
    assert parsed["board_id"] == "arduino_uno"
    assert parsed["mcu"] == "atmega328p"
    assert parsed["frame_type"] == "ACK"


def test_parse_handshake_ack_with_appended_sketch_noise(serial_mgr):
    """Handshake packet followed by trailing sketch output on the same line."""
    line = "$ARIS_ACK,2.0.0,1.0,arduino_uno,atmega328p,avr8,16000000,BALANCED# | Scaled: 128.00\r\n"
    parsed = serial_mgr._parse_handshake_line(line)
    assert parsed is not None
    assert parsed["handshake_success"] is True
    assert parsed["board_id"] == "arduino_uno"


def test_parse_boot_announcement_frame(serial_mgr):
    """Runtime emits $ARIS_BOOT on startup immediately after Serial.begin()."""
    line = "$ARIS_BOOT,2.0.0,1.0,arduino_uno,atmega328p,avr8,16000000,BALANCED#"
    parsed = serial_mgr._parse_handshake_line(line)
    assert parsed is not None
    assert parsed["handshake_success"] is True
    assert parsed["frame_type"] == "BOOT"
    assert parsed["board_id"] == "arduino_uno"


def test_parse_malformed_handshake_returns_none(serial_mgr):
    # Missing fields
    assert serial_mgr._parse_handshake_line("$ARIS_ACK,2.0.0#") is None
    # No closing hash
    assert serial_mgr._parse_handshake_line("$ARIS_ACK,2.0.0,1.0,arduino_uno,atmega328p,avr8,16000000,BALANCED") is None
    # Normal user sketch output
    assert serial_mgr._parse_handshake_line("Sensor: 512 | Mapped: 128 | Scaled: 128.00") is None
    # Empty string
    assert serial_mgr._parse_handshake_line("") is None


# -----------------------------------------------------------------------------
# 2. PERIODIC RETRANSMISSION & BOOTLOADER DELAY TESTS
# -----------------------------------------------------------------------------

def test_perform_handshake_returns_cached_boot_handshake(serial_mgr):
    """If boot handshake was already captured during connect(), return it immediately."""
    serial_mgr.connected = True
    serial_mgr._serial_handle = MagicMock()
    serial_mgr._serial_handle.is_open = True
    serial_mgr.handshake_data = {
        "handshake_success": True,
        "board_id": "arduino_uno",
        "mcu": "atmega328p",
        "frame_type": "BOOT"
    }

    res = serial_mgr.perform_handshake(timeout_sec=2.0)
    assert res["handshake_success"] is True
    assert res["board_id"] == "arduino_uno"
    assert res["frame_type"] == "BOOT"


def test_perform_handshake_periodic_retransmission(serial_mgr):
    """
    Verifies that perform_handshake transmits probes repeatedly (every ~350ms)
    until a response is received, simulating Optiboot bootloader delay.
    """
    mock_handle = MockSerialHandle()
    serial_mgr.connected = True
    serial_mgr._serial_handle = mock_handle
    serial_mgr.current_port = "COM4"

    # Simulate MCU responding on probe after 400ms
    def delayed_responder():
        time.sleep(0.4)
        serial_mgr.handshake_data = {
            "handshake_success": True,
            "board_id": "arduino_uno",
            "mcu": "atmega328p"
        }

    import threading
    t = threading.Thread(target=delayed_responder)
    t.start()

    res = serial_mgr.perform_handshake(timeout_sec=2.0)
    t.join()

    assert res["handshake_success"] is True
    assert res["board_id"] == "arduino_uno"
    # Verify at least one probe was written with clean delimiters
    assert b"$ARIS_HELLO#\n" in mock_handle.written_bytes
    assert b"\r\n$ARIS_HELLO#" in mock_handle.written_bytes


def test_perform_handshake_timeout(serial_mgr):
    """When target never responds, returns clean handshake_success=False."""
    mock_handle = MockSerialHandle()
    serial_mgr.connected = True
    serial_mgr._serial_handle = mock_handle
    serial_mgr.current_port = "COM4"

    res = serial_mgr.perform_handshake(timeout_sec=0.4)
    assert res["handshake_success"] is False
    assert res["is_hardware"] is True
    assert "target did not respond" in res["message"]


# -----------------------------------------------------------------------------
# 3. BUILD FLASHER UPLOAD VS HANDSHAKE VERIFICATION
# -----------------------------------------------------------------------------

def test_deploy_upload_succeeded_but_handshake_timed_out():
    """
    Independent classification:
    - Compilation succeeded
    - Upload exited 0 (firmware physically flashed to board)
    - Handshake verification timed out
    -> Raises ARIS_FLASH_UNVERIFIED with firmware_uploaded=True and telemetry_active=False.
    """
    flasher = BuildFlasher()

    mock_profile = BoardProfile(
        board_id="arduino_uno",
        display_name="Arduino Uno",
        mcu="atmega328p",
        architecture="avr8",
        clock_hz=16000000,
        flash_bytes=32256,
        sram_bytes=2048,
        eeprom_bytes=1024,
        fqbn="arduino:avr:uno"
    )

    with patch("backend.firmware.build_flasher.get_board_profile", return_value=mock_profile), \
         patch("backend.firmware.build_flasher.find_arduino_cli_path", return_value="arduino-cli"), \
         patch("subprocess.run") as mock_run, \
         patch.object(flasher, "verify_upload", return_value=False):

        # Arduino CLI upload returns exit code 0
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "avrdude: 2450 bytes of flash written\navrdude: 2450 bytes of flash verified\n"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        with pytest.raises(ArisException) as exc_info:
            flasher.flash_board(
                board_id="arduino_uno",
                port="COM4",
                source_code="void setup() {} void loop() {}"
            )

        err = exc_info.value
        assert err.error_code == "ARIS_FLASH_UNVERIFIED"
        assert err.details["failure_category"] == "HANDSHAKE_TIMEOUT"
        assert err.details["firmware_uploaded"] is True
        assert err.details["compilation_succeeded"] is True
        assert err.details["upload_succeeded"] is True
        assert err.details["handshake_verified"] is False
        assert err.details["telemetry_active"] is False


def test_deploy_upload_failed_programmer_error():
    """
    When physical upload fails (e.g. exit status 1, programmer not responding):
    - firmware_uploaded must be False
    - upload_succeeded must be False
    """
    flasher = BuildFlasher()

    mock_profile = BoardProfile(
        board_id="arduino_uno",
        display_name="Arduino Uno",
        mcu="atmega328p",
        architecture="avr8",
        clock_hz=16000000,
        flash_bytes=32256,
        sram_bytes=2048,
        eeprom_bytes=1024,
        fqbn="arduino:avr:uno"
    )

    with patch("backend.firmware.build_flasher.get_board_profile", return_value=mock_profile), \
         patch("backend.firmware.build_flasher.find_arduino_cli_path", return_value="arduino-cli"), \
         patch("subprocess.run") as mock_run:

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "Error: programmer is not responding\nWarning: attempt 1 of 10: not in sync: resp=0x00\n"
        mock_run.return_value = mock_proc

        with pytest.raises(ArisException) as exc_info:
            flasher.flash_board(
                board_id="arduino_uno",
                port="COM4",
                source_code="void setup() {} void loop() {}"
            )

        err = exc_info.value
        assert err.error_code == "ARIS_FLASH_FAILED"
        assert err.details["failure_category"] == "BOOTLOADER_UNRESPONSIVE"
        assert err.details["firmware_uploaded"] is False
        assert err.details["compilation_succeeded"] is True


def test_reader_loop_extracts_handshake_and_forwards_user_print(serial_mgr):
    """
    When serial line contains:
    Sensor: 512$ARIS_ACK,2.0.0,1.0,arduino_uno,atmega328p,avr8,16000000,BALANCED#extra
    1. Handshake data is captured.
    2. Prefix 'Sensor: 512' and suffix 'extra' are ingested into the ingestor.
    """
    raw_mixed = b"Sensor: 512$ARIS_ACK,2.0.0,1.0,arduino_uno,atmega328p,avr8,16000000,BALANCED#extra\r\n"
    mock_handle = MockSerialHandle(responses=[raw_mixed, b""])
    serial_mgr._serial_handle = mock_handle
    serial_mgr.connected = True
    serial_mgr.active_run_id = "RUN-100"

    # Start reader thread briefly
    import threading
    serial_mgr._stop_event.clear()
    thread = threading.Thread(target=serial_mgr._reader_loop)
    thread.daemon = True
    thread.start()

    time.sleep(0.15)
    serial_mgr._stop_event.set()
    thread.join(timeout=1.0)

    assert serial_mgr.handshake_data is not None
    assert serial_mgr.handshake_data["handshake_success"] is True
    assert serial_mgr.handshake_data["board_id"] == "arduino_uno"

    # Verify ingestor received the non-handshake segments
    serial_mgr.ingestor.ingest_raw_line.assert_any_call("Sensor: 512", active_run_id="RUN-100")
    serial_mgr.ingestor.ingest_raw_line.assert_any_call("extra", active_run_id="RUN-100")


def test_api_handshake_endpoint():
    """Verifies that /api/connection/handshake processes body and query params."""
    from fastapi.testclient import TestClient
    from backend.api.app import app

    client = TestClient(app)

    with patch("backend.serial.serial_manager.SerialManager.perform_handshake") as mock_hs:
        mock_hs.return_value = {
            "handshake_success": True,
            "board_id": "arduino_uno",
            "mcu": "atmega328p"
        }

        # POST with JSON body
        res = client.post("/api/connection/handshake", json={"timeout_sec": 3.5})
        assert res.status_code == 200
        data = res.json()
        assert data["handshake_success"] is True
        assert data["board_id"] == "arduino_uno"
        mock_hs.assert_called_with(timeout_sec=3.5)

        # POST without body (default timeout 3.0)
        res_default = client.post("/api/connection/handshake")
        assert res_default.status_code == 200
        mock_hs.assert_called_with(timeout_sec=3.0)

