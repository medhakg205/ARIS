"""
Unit tests for ARIS Build & Flash Subsystem (BuildFlasher).
Validates:
- Toolchain detection (arduino-cli bundled or fallback)
- Real or simulated compilation of valid Arduino C++ sketches
- Compiler error trapping and ARIS_BUILD_FAILED exception propagation
- Unsupported board rejection (e.g. Renesas RA4M1 on AVR8 engine)
- Flash command execution and simulation failure states
"""

import pytest
from backend.firmware.build_flasher import BuildFlasher
from backend.telemetry.telemetry_schema import ArisException


def test_build_flasher_initialization():
    flasher = BuildFlasher()
    assert flasher is not None
    # We know arduino-cli is installed on this machine, or simulated fallback is active
    if flasher.arduino_cli_path:
        assert "arduino-cli" in flasher.arduino_cli_path.lower()


def test_compile_valid_sketch():
    flasher = BuildFlasher()
    sketch = (
        "void setup() {\n"
        "  pinMode(13, OUTPUT);\n"
        "}\n"
        "void loop() {\n"
        "  digitalWrite(13, HIGH);\n"
        "  delay(50);\n"
        "  digitalWrite(13, LOW);\n"
        "  delay(50);\n"
        "}\n"
    )
    result = flasher.compile_firmware(sketch, board_id="arduino_uno")
    assert result["status"] == "BUILD_SUCCESS"
    assert result["board_id"] == "arduino_uno"
    assert result["mcu"] == "atmega328p"
    assert result["binary_size_bytes"] > 0
    assert result["sram_usage_bytes"] > 0
    assert result["flash_usage_pct"] > 0
    assert result["toolchain"] in ("arduino-cli", "simulated")


def test_compile_syntax_error():
    flasher = BuildFlasher()
    bad_sketch = "void setup() { invalid_token_missing_semicolon } void loop() {}"
    with pytest.raises(ArisException) as exc_info:
        flasher.compile_firmware(bad_sketch, board_id="arduino_uno")
    
    assert exc_info.value.error_code == "ARIS_BUILD_FAILED"
    assert exc_info.value.recoverable is True


def test_compile_empty_code():
    flasher = BuildFlasher()
    with pytest.raises(ArisException) as exc_info:
        flasher.compile_firmware("", board_id="arduino_uno")
    assert exc_info.value.error_code == "ARIS_BUILD_FAILED"


def test_compile_unsupported_board():
    flasher = BuildFlasher()
    sketch = "void setup() {} void loop() {}"
    # Board with no defined FQBN cannot be compiled
    from backend.firmware.board_profiles import BoardProfile
    no_fqbn_prof = BoardProfile(
        board_id="no_fqbn_board",
        display_name="No FQBN Board",
        fqbn="",
        supported=False
    )
    from backend.firmware.board_profiles import ALL_BOARD_PROFILES
    ALL_BOARD_PROFILES["no_fqbn_board"] = no_fqbn_prof

    with pytest.raises(ArisException) as exc_info:
        flasher.compile_firmware(sketch, board_id="no_fqbn_board")
    assert exc_info.value.error_code == "ARIS_UNSUPPORTED_BOARD"

    # Totally unknown board
    with pytest.raises(ArisException) as exc_info2:
        flasher.compile_firmware(sketch, board_id="nonexistent_board_999")
    assert exc_info2.value.error_code == "ARIS_UNSUPPORTED_BOARD"


def test_flash_simulated():
    flasher = BuildFlasher()
    result = flasher.flash_board(
        board_id="arduino_uno",
        port="SIMULATED",
        source_code="void setup(){} void loop(){}"
    )
    assert result["status"] == "FLASH_SUCCESS"
    assert result["verified"] is True


def test_flash_simulated_failure():
    flasher = BuildFlasher()
    with pytest.raises(ArisException) as exc_info:
        flasher.flash_board(
            board_id="arduino_uno",
            port="SIMULATED",
            fail_simulation=True
        )
    assert exc_info.value.error_code == "ARIS_FLASH_FAILED"


def test_compile_physical_toolchain_unavailable():
    """Physical compile request raises ARIS_TOOLCHAIN_UNAVAILABLE when arduino-cli is missing."""
    flasher = BuildFlasher()
    flasher.arduino_cli_path = None  # simulate missing host toolchain
    sketch = "void setup() {} void loop() {}"
    with pytest.raises(ArisException) as exc_info:
        flasher.compile_firmware(sketch, board_id="arduino_uno", is_simulation=False)
    assert exc_info.value.error_code == "ARIS_TOOLCHAIN_UNAVAILABLE"
    assert exc_info.value.status_code == 503


def test_compile_simulated_fallback_explicit():
    """Explicit simulation compile succeeds even when arduino-cli is not present."""
    flasher = BuildFlasher()
    flasher.arduino_cli_path = None
    sketch = "void setup() {} void loop() {}"
    result = flasher.compile_firmware(sketch, board_id="arduino_uno", is_simulation=True)
    assert result["status"] == "BUILD_SUCCESS"
    assert result["toolchain"] == "simulated"
    assert result["binary_size_bytes"] > 0


def test_flash_physical_toolchain_unavailable():
    """Physical port flash raises ARIS_TOOLCHAIN_UNAVAILABLE when arduino-cli is missing."""
    flasher = BuildFlasher()
    flasher.arduino_cli_path = None
    with pytest.raises(ArisException) as exc_info:
        flasher.flash_board(
            board_id="arduino_uno",
            port="COM3",
            source_code="void setup(){} void loop(){}"
        )
    assert exc_info.value.error_code == "ARIS_TOOLCHAIN_UNAVAILABLE"
    assert exc_info.value.status_code == 503


def test_verify_upload_handshake(monkeypatch):
    """Test verify_upload returns True on handshake success and False on failure."""
    flasher = BuildFlasher()
    
    # 1. Simulated port always passes verification
    assert flasher.verify_upload("arduino_uno", "SIMULATED") is True

    # 2. Mock serial manager returning successful handshake
    class MockSerialMgrSuccess:
        connected = True
        current_port = "COM3"
        def connect(self, port, baud_rate):
            pass
        def perform_handshake(self, timeout_sec):
            return {"handshake_success": True, "board_id": "arduino_uno"}

    monkeypatch.setattr("backend.api.dependencies.get_serial_mgr", lambda: MockSerialMgrSuccess())
    monkeypatch.setattr("time.sleep", lambda _: None)
    assert flasher.verify_upload("arduino_uno", "COM3") is True

    # 3. Mock serial manager returning failed handshake
    class MockSerialMgrFail:
        connected = True
        current_port = "COM3"
        def connect(self, port, baud_rate):
            pass
        def perform_handshake(self, timeout_sec):
            return {"handshake_success": False, "message": "No ACK"}

    monkeypatch.setattr("backend.api.dependencies.get_serial_mgr", lambda: MockSerialMgrFail())
    assert flasher.verify_upload("arduino_uno", "COM3") is False

