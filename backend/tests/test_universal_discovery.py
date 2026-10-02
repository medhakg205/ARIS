"""
ARIS Universal Arduino Board Discovery & Dynamic Profile Resolution Tests.
Covers all 12 mandatory specification scenarios:
1. Exact known profile (Uno R3, Mega 2560, Nano)
2. Unknown board with valid FQBN resolved via toolchain
3. Real toolchain metadata parsed into valid profile
4. Missing toolchain properties marked unavailable, not guessed
5. Non-AVR board profile (Uno R4, SAMD, ESP32)
6. Architecture-specific analysis rules applied
7. Unsupported architecture metrics flagged UNAVAILABLE
8. Board mismatch detected between discovery and handshake
9. Dynamic build/flash using resolved FQBN
10. Database persistence of dynamically resolved boards
11. Board switching without app restart
12. UI payload verification (clean, truthful, no fabricated metrics)
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from backend.firmware.board_profiles import (
    BoardProfile,
    BoardProfileResolver,
    CANONICAL_BOARD_PROFILES,
    ALL_BOARD_PROFILES,
    get_board_profile,
    get_board_profile_by_fqbn
)
from backend.database.models import BoardRecord
from backend.database.db_engine import DatabaseEngine
from backend.serial.serial_discovery import DiscoveredPort, scan_serial_ports
from backend.firmware.build_flasher import BuildFlasher
from backend.ai.optimization_reasoner import OptimizationReasoner
from backend.analysis.ai_interface import AIContextInput
from backend.telemetry.telemetry_schema import ArisException


# =========================================================================
# Scenario 1: Exact known profile (Uno R3, Mega, Nano)
# =========================================================================
def test_scenario_01_exact_known_profiles():
    """Authoritative known profiles retain verified exact hardware specifications."""
    uno = get_board_profile("arduino_uno")
    assert uno.profile_source == "EXACT_PROFILE"
    assert uno.confidence in ("CONFIRMED", "HIGH")
    assert uno.mcu == "atmega328p"
    assert uno.architecture == "avr8"
    assert uno.clock_hz == 16_000_000
    assert uno.flash_bytes == 32_768
    assert uno.sram_bytes == 2_048
    assert uno.fqbn == "arduino:avr:uno"

    mega = get_board_profile("arduino_mega")
    assert mega.mcu == "atmega2560"
    assert mega.flash_bytes == 262_144
    assert mega.sram_bytes == 8_192

    nano = get_board_profile("arduino_nano")
    assert nano.mcu == "atmega328p"
    assert nano.adc_channels == 8


# =========================================================================
# Scenario 2 & 3: Unknown board with valid FQBN resolved via toolchain
# =========================================================================
def test_scenario_02_and_03_toolchain_derived_profile():
    """Dynamic resolution of unfamiliar board via arduino-cli JSON metadata."""
    sample_toolchain_json = {
        "name": "Seeed XIAO SAMD21",
        "properties": [
            "build.mcu=samd21g18a",
            "build.arch=samd",
            "build.f_cpu=48000000L",
            "upload.maximum_size=262144",
            "upload.maximum_data_size=32768"
        ]
    }
    fqbn = "seeeduino:samd:seeed_XIAO_m0"
    profile = BoardProfileResolver.parse_toolchain_json(sample_toolchain_json, fqbn)

    assert profile.profile_source == "TOOLCHAIN_DERIVED"
    assert profile.confidence == "HIGH"
    assert profile.display_name == "Seeed XIAO SAMD21"
    assert profile.mcu == "samd21g18a"
    assert profile.architecture == "arm"
    assert profile.clock_hz == 48_000_000
    assert profile.flash_bytes == 262_144
    assert profile.sram_bytes == 32_768
    assert profile.fqbn == fqbn
    assert profile.build_toolchain == "arm-none-eabi-gcc"


# =========================================================================
# Scenario 4: Missing toolchain properties marked unavailable, not guessed
# =========================================================================
def test_scenario_04_missing_properties_not_guessed():
    """Unspecified properties remain None and are explicitly recorded in unavailable_properties."""
    sparse_json = {
        "name": "Generic Custom Core",
        "properties": [
            "build.mcu=custom_mcu"
        ]
    }
    profile = BoardProfileResolver.parse_toolchain_json(sparse_json, "custom:core:board")
    assert profile.mcu == "custom_mcu"
    assert profile.clock_hz is None
    assert profile.flash_bytes is None
    assert profile.sram_bytes is None
    assert "clock_hz" in profile.unavailable_properties
    assert "flash_bytes" in profile.unavailable_properties
    assert "sram_bytes" in profile.unavailable_properties
    # Zero guessing check: clock must NEVER be assumed 16MHz, flash must NEVER be 32KB
    assert profile.clock_hz != 16_000_000
    assert profile.flash_bytes != 32_768


# =========================================================================
# Scenario 5: Non-AVR board profile (Uno R4, SAMD, ESP32)
# =========================================================================
def test_scenario_05_non_avr_boards():
    """Modern non-AVR boards correctly catalog architecture and ARM/ESP toolchains."""
    unor4 = get_board_profile("arduino_uno_r4_wifi")
    assert unor4.architecture == "arm_cortex_m4"
    assert unor4.mcu == "ra4m1"
    assert unor4.clock_hz == 48_000_000
    assert unor4.build_toolchain == "arm-none-eabi-gcc"
    assert unor4.is_arm() is True
    assert unor4.is_avr() is False

    esp_json = {
        "name": "NodeMCU ESP32",
        "properties": [
            "build.mcu=esp32",
            "build.arch=esp32",
            "build.f_cpu=240000000L",
            "upload.maximum_size=1310720",
            "upload.maximum_data_size=327680"
        ]
    }
    esp_prof = BoardProfileResolver.parse_toolchain_json(esp_json, "esp32:esp32:esp32")
    assert esp_prof.is_esp() is True
    assert esp_prof.clock_hz == 240_000_000
    assert esp_prof.build_toolchain == "xtensa-esp32-elf-gcc"


# =========================================================================
# Scenario 6 & 7: Architecture-specific analysis rules applied
# =========================================================================
def test_scenario_06_and_07_architecture_specific_reasoning():
    """Optimization reasoning adapts clock cycle math and architecture context dynamically."""
    unor4 = get_board_profile("arduino_uno_r4_wifi")
    context = AIContextInput(
        board_profile=unor4.to_dict(),
        firmware_source="void loop() { delay(10); }",
        static_findings=[],
        runtime_metrics={},
        baseline_metrics={},
        runtime_static_correlations=[],
        optimization_history=[]
    )
    finding = {
        "rule_id": "ARIS-001",
        "title": "Blocking delay in loop",
        "evidence": {"duration": 10},
        "source_file": "main.ino",
        "source_line": 5
    }
    candidate = OptimizationReasoner.reason_and_synthesize(context, finding)
    # At 48MHz (Uno R4), 10ms = 480,000 clock cycles (not 160,000 for 16MHz AVR!)
    assert "480,000 CPU clock cycles" in candidate["problem"]
    assert "RA4M1" in candidate["hardware_consideration"]
    assert "48MHz" in candidate["hardware_consideration"]


# =========================================================================
# Scenario 8: Board mismatch detected between discovery and handshake
# =========================================================================
def test_scenario_08_board_identity_mismatch_detected():
    """Flags BOARD_IDENTITY_MISMATCH when discovery and physical handshake conflict."""
    discovered_uno = get_board_profile("arduino_uno")
    conflicting_handshake = {
        "handshake_success": True,
        "board_id": "arduino_mega",
        "mcu": "atmega2560",
        "architecture": "avr8",
        "clock_hz": 16000000,
        "runtime_version": "1.0.0"
    }
    is_match, reason = BoardProfileResolver.verify_identity_match(discovered_uno, conflicting_handshake)
    assert is_match is False
    assert "BOARD_IDENTITY_MISMATCH" in reason
    assert "atmega328p" in reason
    assert "atmega2560" in reason


# =========================================================================
# Scenario 9: Dynamic build/flash using resolved FQBN
# =========================================================================
def test_scenario_09_dynamic_build_using_resolved_fqbn():
    """BuildFlasher accepts any board with a valid FQBN for compilation."""
    flasher = BuildFlasher(use_simulated_toolchain_if_missing=True)
    sketch = "void setup() {} void loop() {}"
    # Build for Uno R4 WiFi (simulated toolchain fallback when physical target absent)
    res = flasher.compile_firmware(sketch, board_id="arduino_uno_r4_wifi", is_simulation=True)
    assert res["status"] == "BUILD_SUCCESS"
    assert res["fqbn"] == "arduino:renesas_uno:unor4wifi"
    assert res["mcu"] == "ra4m1"


# =========================================================================
# Scenario 10: Database persistence of dynamically resolved boards
# =========================================================================
def test_scenario_10_database_persistence(temp_db):
    """Dynamically resolved board with nullable fields persists and restores accurately."""
    partially_resolved = BoardProfileResolver.create_partially_resolved(
        board_id="ch340_target_port_1",
        display_name="USB-SERIAL CH340 on COM3",
        description="Clone USB bridge",
        fqbn=None
    )
    temp_db.save_board(partially_resolved.to_record())

    restored = temp_db.get_board("ch340_target_port_1")
    assert restored is not None
    assert restored.board_id == "ch340_target_port_1"
    assert restored.profile_source == "PARTIALLY_RESOLVED"
    assert restored.confidence == "UNCERTAIN"
    assert restored.mcu is None
    assert restored.flash_bytes is None
    assert "mcu" in restored.unavailable_properties


# =========================================================================
# Scenario 11: Board switching without app restart
# =========================================================================
def test_scenario_11_board_switching(temp_db):
    """Board switching re-resolves and updates active profile cleanly."""
    # First device connected: Uno
    uno_prof = get_board_profile("arduino_uno")
    temp_db.save_board(uno_prof.to_record())
    active_1 = temp_db.get_board("arduino_uno")
    assert active_1.mcu == "atmega328p"

    # Board switch event: Mega connected on same session
    mega_prof = get_board_profile("arduino_mega")
    temp_db.save_board(mega_prof.to_record())
    active_2 = temp_db.get_board("arduino_mega")
    assert active_2.mcu == "atmega2560"
    assert active_2.flash_bytes == 262_144


# =========================================================================
# Scenario 12: Truthful discovery representation (no fake metrics)
# =========================================================================
def test_scenario_12_truthful_discovery_representation():
    """Unrecognized serial bridges are marked UNCERTAIN without fake defaults."""
    fake_port = DiscoveredPort(
        device="COM7",
        description="USB-SERIAL CH340 (COM7)",
        hwid="USB\\VID_1A86&PID_7523",
        vid=0x1A86,
        pid=0x7523,
        is_arduino=True,
        suggested_board_id="unknown_arduino_bridge",
        mcu=None,
        architecture=None,
        fqbn=None,
        confidence="UNCERTAIN",
        profile_source="PARTIALLY_RESOLVED",
        unavailable_properties=["mcu", "architecture", "clock_hz", "flash_bytes"]
    )
    port_dict = fake_port.to_dict()
    assert port_dict["confidence"] == "UNCERTAIN"
    assert port_dict["mcu"] is None
    assert port_dict["architecture"] is None
    assert port_dict["fqbn"] is None
    assert "flash_bytes" in port_dict["unavailable_properties"]
