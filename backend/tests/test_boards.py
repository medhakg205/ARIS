"""
Unit tests for ARIS Board Profiles Specification.
Verifies:
- arduino_uno, arduino_nano, arduino_mega definitions
- ATmega328P and ATmega2560 hardware parameters
- AVR8 architecture constraints
- Exact flash, SRAM, EEPROM, GPIO, ADC, UART, and timer counts
"""

import pytest
from backend.firmware.board_profiles import (
    CANONICAL_BOARD_PROFILES,
    get_board_profile,
    list_board_profiles,
    BoardProfile
)


def test_supported_boards_exist():
    """Verify all 3 canonical boards are present in the registry."""
    assert "arduino_uno" in CANONICAL_BOARD_PROFILES
    assert "arduino_nano" in CANONICAL_BOARD_PROFILES
    assert "arduino_mega" in CANONICAL_BOARD_PROFILES
    assert len(CANONICAL_BOARD_PROFILES) == 3


def test_arduino_uno_profile():
    """Verify exact Uno hardware specification."""
    uno = get_board_profile("arduino_uno")
    assert uno.board_id == "arduino_uno"
    assert uno.display_name == "Arduino Uno"
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
    assert "TIMER0_OVF" in uno.interrupt_capabilities


def test_arduino_nano_profile():
    """Verify exact Nano hardware specification."""
    nano = get_board_profile("arduino_nano")
    assert nano.board_id == "arduino_nano"
    assert nano.display_name == "Arduino Nano"
    assert nano.mcu == "atmega328p"
    assert nano.architecture == "avr8"
    assert nano.clock_hz == 16_000_000
    assert nano.flash_bytes == 32_768
    assert nano.sram_bytes == 2_048
    assert nano.eeprom_bytes == 1_024
    assert nano.gpio_count == 14
    assert nano.adc_channels == 8  # Nano has 8 analog channels
    assert nano.uart_count == 1
    assert nano.timer_count == 3


def test_arduino_mega_profile():
    """Verify exact Mega 2560 hardware specification."""
    mega = get_board_profile("arduino_mega")
    assert mega.board_id == "arduino_mega"
    assert mega.display_name == "Arduino Mega 2560"
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


def test_unsupported_board_raises():
    """Verify querying an unsupported board raises KeyError."""
    with pytest.raises(KeyError) as exc:
        get_board_profile("esp32_wroom")
    assert "Unsupported ARIS board_id" in str(exc.value)
