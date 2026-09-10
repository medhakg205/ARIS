"""
ARIS Board Profiles & Architecture Specifications.
Defines canonical hardware profiles for all supported microcontroller boards:
- Arduino Uno (ATmega328P, AVR8)
- Arduino Nano (ATmega328P, AVR8)
- Arduino Mega 2560 (ATmega2560, AVR8)
Adheres strictly to the canonical contract and register/timer capabilities.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from backend.database.models import BoardRecord


@dataclass
class BoardProfile:
    """
    In-memory canonical Board Profile representation.
    Enforces required physical constraints and peripheral counts.
    """
    board_id: str                      # Canonical ID (e.g. "arduino_uno", "arduino_nano", "arduino_mega")
    display_name: str                  # Human-readable display label
    mcu: str                           # Microcontroller chip part name
    architecture: str                  # Core architecture (always "avr8" for these boards)
    clock_hz: int                      # System clock frequency in Hz
    flash_bytes: int                   # Total non-volatile Flash memory
    sram_bytes: int                    # Total static RAM
    eeprom_bytes: int                  # Total EEPROM
    gpio_count: int                    # Accessible digital GPIO lines
    adc_channels: int                  # Analog ADC channels
    uart_count: int                    # Hardware UART count
    spi_available: bool                # SPI bus support
    i2c_available: bool                # I2C (Two-Wire Interface) support
    timer_count: int                   # Hardware timers count
    interrupt_capabilities: List[str] = field(default_factory=list) # Hardware interrupt vector list

    def to_record(self) -> BoardRecord:
        """Converts profile to persistent database BoardRecord."""
        return BoardRecord(
            board_id=self.board_id,
            display_name=self.display_name,
            mcu=self.mcu,
            architecture=self.architecture,
            clock_hz=self.clock_hz,
            flash_bytes=self.flash_bytes,
            sram_bytes=self.sram_bytes,
            eeprom_bytes=self.eeprom_bytes,
            gpio_count=self.gpio_count,
            adc_channels=self.adc_channels,
            uart_count=self.uart_count,
            spi_available=self.spi_available,
            i2c_available=self.i2c_available,
            timer_count=self.timer_count,
            interrupt_capabilities=list(self.interrupt_capabilities)
        )

    def to_dict(self) -> Dict:
        """Serializes to dictionary representation."""
        return asdict(self)


# Canonical registry of supported Arduino boards
CANONICAL_BOARD_PROFILES: Dict[str, BoardProfile] = {
    # -------------------------------------------------------------------------
    # 1. Arduino Uno R3
    # -------------------------------------------------------------------------
    "arduino_uno": BoardProfile(
        board_id="arduino_uno",
        display_name="Arduino Uno",
        mcu="atmega328p",
        architecture="avr8",
        clock_hz=16_000_000,
        flash_bytes=32_768,      # 32 KB Flash
        sram_bytes=2_048,        # 2 KB SRAM
        eeprom_bytes=1_024,      # 1 KB EEPROM
        gpio_count=14,           # D0 - D13
        adc_channels=6,          # A0 - A5
        uart_count=1,            # 1 hardware UART (Serial on pins 0, 1)
        spi_available=True,      # MOSI 11, MISO 12, SCK 13
        i2c_available=True,      # SDA A4, SCL A5
        timer_count=3,           # Timer0 (8-bit), Timer1 (16-bit), Timer2 (8-bit)
        interrupt_capabilities=[
            "INT0", "INT1",
            "PCINT0", "PCINT1", "PCINT2",
            "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF"
        ]
    ),

    # -------------------------------------------------------------------------
    # 2. Arduino Nano
    # -------------------------------------------------------------------------
    "arduino_nano": BoardProfile(
        board_id="arduino_nano",
        display_name="Arduino Nano",
        mcu="atmega328p",
        architecture="avr8",
        clock_hz=16_000_000,
        flash_bytes=32_768,      # 32 KB Flash
        sram_bytes=2_048,        # 2 KB SRAM
        eeprom_bytes=1_024,      # 1 KB EEPROM
        gpio_count=14,           # D0 - D13
        adc_channels=8,          # A0 - A7 (Nano has 2 additional analog inputs A6, A7)
        uart_count=1,            # 1 hardware UART (Serial on pins 0, 1)
        spi_available=True,      # MOSI 11, MISO 12, SCK 13
        i2c_available=True,      # SDA A4, SCL A5
        timer_count=3,           # Timer0 (8-bit), Timer1 (16-bit), Timer2 (8-bit)
        interrupt_capabilities=[
            "INT0", "INT1",
            "PCINT0", "PCINT1", "PCINT2",
            "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF"
        ]
    ),

    # -------------------------------------------------------------------------
    # 3. Arduino Mega 2560 R3
    # -------------------------------------------------------------------------
    "arduino_mega": BoardProfile(
        board_id="arduino_mega",
        display_name="Arduino Mega 2560",
        mcu="atmega2560",
        architecture="avr8",
        clock_hz=16_000_000,
        flash_bytes=262_144,     # 256 KB Flash
        sram_bytes=8_192,        # 8 KB SRAM
        eeprom_bytes=4_096,      # 4 KB EEPROM
        gpio_count=54,           # D0 - D53
        adc_channels=16,         # A0 - A15
        uart_count=4,            # 4 hardware UARTs (Serial, Serial1, Serial2, Serial3)
        spi_available=True,      # MOSI 51, MISO 50, SCK 52, SS 53
        i2c_available=True,      # SDA 20, SCL 21
        timer_count=6,           # Timer0, Timer1, Timer2, Timer3, Timer4, Timer5
        interrupt_capabilities=[
            "INT0", "INT1", "INT2", "INT3", "INT4", "INT5",
            "PCINT0", "PCINT1", "PCINT2",
            "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF",
            "TIMER3_OVF", "TIMER4_OVF", "TIMER5_OVF"
        ]
    )
}


def get_board_profile(board_id: str) -> BoardProfile:
    """
    Retrieves the canonical board profile by board ID.
    Raises KeyError with valid options if unknown.
    """
    if board_id not in CANONICAL_BOARD_PROFILES:
        raise KeyError(
            f"Unsupported ARIS board_id '{board_id}'. "
            f"Supported boards: {list(CANONICAL_BOARD_PROFILES.keys())}"
        )
    return CANONICAL_BOARD_PROFILES[board_id]


def list_board_profiles() -> List[BoardProfile]:
    """Returns a list of all supported canonical board profiles."""
    return list(CANONICAL_BOARD_PROFILES.values())
