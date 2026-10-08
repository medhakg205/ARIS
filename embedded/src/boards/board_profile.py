"""
ARIS BoardProfile Definition and Registry.
Defines canonical board profile specifications conforming to the ARIS specification.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class BoardProfile:
    board_id: str
    display_name: str
    mcu: str
    architecture: str
    clock_hz: int
    flash_bytes: int
    sram_bytes: int
    eeprom_bytes: int
    gpio_count: int
    adc_channels: int
    uart_count: int
    spi_available: bool
    i2c_available: bool
    timer_count: int
    interrupt_capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

# Canonical Registry
BOARD_PROFILES: Dict[str, BoardProfile] = {
    "arduino_uno": BoardProfile(
        board_id="arduino_uno",
        display_name="Arduino Uno",
        mcu="atmega328p",
        architecture="avr8",
        clock_hz=16_000_000,
        flash_bytes=32_768,
        sram_bytes=2_048,
        eeprom_bytes=1_024,
        gpio_count=14,
        adc_channels=6,
        uart_count=1,
        spi_available=True,
        i2c_available=True,
        timer_count=3,
        interrupt_capabilities=[
            "INT0", "INT1",
            "PCINT0", "PCINT1", "PCINT2",
            "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF"
        ]
    ),
    "arduino_nano": BoardProfile(
        board_id="arduino_nano",
        display_name="Arduino Nano",
        mcu="atmega328p",
        architecture="avr8",
        clock_hz=16_000_000,
        flash_bytes=32_768,
        sram_bytes=2_048,
        eeprom_bytes=1_024,
        gpio_count=14,
        adc_channels=8,
        uart_count=1,
        spi_available=True,
        i2c_available=True,
        timer_count=3,
        interrupt_capabilities=[
            "INT0", "INT1",
            "PCINT0", "PCINT1", "PCINT2",
            "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF"
        ]
    ),
    "arduino_mega": BoardProfile(
        board_id="arduino_mega",
        display_name="Arduino Mega 2560",
        mcu="atmega2560",
        architecture="avr8",
        clock_hz=16_000_000,
        flash_bytes=262_144,
        sram_bytes=8_192,
        eeprom_bytes=4_096,
        gpio_count=54,
        adc_channels=16,
        uart_count=4,
        spi_available=True,
        i2c_available=True,
        timer_count=6,
        interrupt_capabilities=[
            "INT0", "INT1", "INT2", "INT3", "INT4", "INT5",
            "PCINT0", "PCINT1", "PCINT2",
            "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF",
            "TIMER3_OVF", "TIMER4_OVF", "TIMER5_OVF"
        ]
    )
}

def get_board_profile(board_id: str) -> BoardProfile:
    if board_id not in BOARD_PROFILES:
        raise KeyError(f"Unsupported ARIS board_id '{board_id}'. Available: {list(BOARD_PROFILES.keys())}")
    return BOARD_PROFILES[board_id]

def list_supported_boards() -> List[str]:
    return list(BOARD_PROFILES.keys())
