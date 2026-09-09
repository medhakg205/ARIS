"""
Unit tests for ARIS Board Profiles and Constraints.
"""

import pytest
from embedded.boards.board_profile import (
    BoardProfile,
    BOARD_PROFILES,
    get_board_profile,
    list_supported_boards
)

REQUIRED_BOARD_FIELDS = [
    "board_id",
    "display_name",
    "mcu",
    "architecture",
    "clock_hz",
    "flash_bytes",
    "sram_bytes",
    "eeprom_bytes",
    "gpio_count",
    "adc_channels",
    "uart_count",
    "spi_available",
    "i2c_available",
    "timer_count",
    "interrupt_capabilities"
]

def test_supported_boards_list():
    boards = list_supported_boards()
    assert "arduino_uno" in boards
    assert "arduino_nano" in boards
    assert "arduino_mega" in boards

def test_board_profile_has_all_required_fields():
    for board_id, profile in BOARD_PROFILES.items():
        data = profile.to_dict()
        for req_field in REQUIRED_BOARD_FIELDS:
            assert req_field in data, f"Board '{board_id}' missing required field '{req_field}'"

def test_arduino_uno_specs():
    uno = get_board_profile("arduino_uno")
    assert uno.board_id == "arduino_uno"
    assert uno.mcu == "atmega328p"
    assert uno.architecture == "avr8"
    assert uno.clock_hz == 16_000_000
    assert uno.flash_bytes == 32_768
    assert uno.sram_bytes == 2_048
    assert uno.eeprom_bytes == 1_024
    assert uno.gpio_count == 14
    assert uno.adc_channels == 6
    assert uno.uart_count == 1
    assert uno.spi_available is True
    assert uno.i2c_available is True
    assert uno.timer_count == 3
    assert "INT0" in uno.interrupt_capabilities
    assert "TIMER0_OVF" in uno.interrupt_capabilities

def test_arduino_nano_specs():
    nano = get_board_profile("arduino_nano")
    assert nano.board_id == "arduino_nano"
    assert nano.mcu == "atmega328p"
    assert nano.architecture == "avr8"
    assert nano.clock_hz == 16_000_000
    assert nano.flash_bytes == 32_768
    assert nano.sram_bytes == 2_048
    assert nano.gpio_count == 14
    assert nano.adc_channels == 8  # Nano has A0-A7

def test_arduino_mega_specs():
    mega = get_board_profile("arduino_mega")
    assert mega.board_id == "arduino_mega"
    assert mega.mcu == "atmega2560"
    assert mega.architecture == "avr8"
    assert mega.clock_hz == 16_000_000
    assert mega.flash_bytes == 262_144
    assert mega.sram_bytes == 8_192
    assert mega.eeprom_bytes == 4_096
    assert mega.gpio_count == 54
    assert mega.adc_channels == 16
    assert mega.uart_count == 4
    assert mega.timer_count == 6

def test_unknown_board_raises():
    with pytest.raises(KeyError):
        get_board_profile("arduino_esp32_unknown")
