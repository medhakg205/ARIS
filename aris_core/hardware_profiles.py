"""
Hardware Profiles Database for ARIS (Arduino Runtime Intelligence System).
Defines comprehensive architecture specifications, register maps, memory boundaries,
and hardware constraints for all supported microcontrollers.
"""

from typing import Dict, List, Any
from pydantic import BaseModel

class PinMapping(BaseModel):
    pin_name: str
    pin_type: str  # "digital", "analog", "pwm", "power", "communication"
    port_register: str  # e.g., "PORTB"
    pin_bit: int  # e.g., 5 for PB5 (Digital Pin 13 on Uno)
    timer_channel: str | None = None  # e.g., "OC0A", "OC1A"
    interrupt_num: int | None = None

class HardwareProfile(BaseModel):
    id: str
    name: str
    mcu_model: str
    architecture: str  # "AVR 8-bit", "ARM Cortex-M3 32-bit", "Xtensa 32-bit Dual-Core"
    core_frequency_hz: int
    flash_bytes: int
    sram_bytes: int
    eeprom_bytes: int
    operating_voltage: float
    active_power_ma: float
    sleep_power_ma: float
    hardware_uarts: int
    adc_channels: int
    adc_resolution_bits: int
    timer_count: int
    direct_port_registers: List[str]
    pin_count: int
    pins: Dict[str, PinMapping]
    hardware_notes: str

HARDWARE_PROFILES: Dict[str, HardwareProfile] = {
    "arduino_uno": HardwareProfile(
        id="arduino_uno",
        name="Arduino UNO R3",
        mcu_model="ATmega328P",
        architecture="AVR 8-bit RISC (Harvard)",
        core_frequency_hz=16_000_000,
        flash_bytes=32_768,  # 32 KB (0.5KB used by bootloader)
        sram_bytes=2_048,    # 2 KB
        eeprom_bytes=1_024,  # 1 KB
        operating_voltage=5.0,
        active_power_ma=46.5,
        sleep_power_ma=15.0,
        hardware_uarts=1,
        adc_channels=6,
        adc_resolution_bits=10,
        timer_count=3,  # Timer0 (8-bit), Timer1 (16-bit), Timer2 (8-bit)
        direct_port_registers=["PORTB", "PORTC", "PORTD"],
        pin_count=28,
        pins={
            "D0": PinMapping(pin_name="D0 (RX)", pin_type="communication", port_register="PORTD", pin_bit=0),
            "D1": PinMapping(pin_name="D1 (TX)", pin_type="communication", port_register="PORTD", pin_bit=1),
            "D2": PinMapping(pin_name="D2", pin_type="digital", port_register="PORTD", pin_bit=2, interrupt_num=0),
            "D3": PinMapping(pin_name="D3", pin_type="pwm", port_register="PORTD", pin_bit=3, timer_channel="OC2B", interrupt_num=1),
            "D4": PinMapping(pin_name="D4", pin_type="digital", port_register="PORTD", pin_bit=4),
            "D5": PinMapping(pin_name="D5", pin_type="pwm", port_register="PORTD", pin_bit=5, timer_channel="OC0B"),
            "D6": PinMapping(pin_name="D6", pin_type="pwm", port_register="PORTD", pin_bit=6, timer_channel="OC0A"),
            "D7": PinMapping(pin_name="D7", pin_type="digital", port_register="PORTD", pin_bit=7),
            "D8": PinMapping(pin_name="D8", pin_type="digital", port_register="PORTB", pin_bit=0),
            "D9": PinMapping(pin_name="D9", pin_type="pwm", port_register="PORTB", pin_bit=1, timer_channel="OC1A"),
            "D10": PinMapping(pin_name="D10", pin_type="pwm", port_register="PORTB", pin_bit=2, timer_channel="OC1B"),
            "D11": PinMapping(pin_name="D11 (MOSI)", pin_type="pwm", port_register="PORTB", pin_bit=3, timer_channel="OC2A"),
            "D12": PinMapping(pin_name="D12 (MISO)", pin_type="digital", port_register="PORTB", pin_bit=4),
            "D13": PinMapping(pin_name="D13 (LED)", pin_type="digital", port_register="PORTB", pin_bit=5),
            "A0": PinMapping(pin_name="A0", pin_type="analog", port_register="PORTC", pin_bit=0),
            "A1": PinMapping(pin_name="A1", pin_type="analog", port_register="PORTC", pin_bit=1),
            "A2": PinMapping(pin_name="A2", pin_type="analog", port_register="PORTC", pin_bit=2),
            "A3": PinMapping(pin_name="A3", pin_type="analog", port_register="PORTC", pin_bit=3),
            "A4": PinMapping(pin_name="A4 (SDA)", pin_type="analog", port_register="PORTC", pin_bit=4),
            "A5": PinMapping(pin_name="A5 (SCL)", pin_type="analog", port_register="PORTC", pin_bit=5),
        },
        hardware_notes="Standard 8-bit AVR microcontroller with 32 general purpose 8-bit registers, 2KB internal SRAM, and single-cycle execution of most instructions at 16MHz."
    ),

    "arduino_mega": HardwareProfile(
        id="arduino_mega",
        name="Arduino MEGA 2560 R3",
        mcu_model="ATmega2560",
        architecture="AVR 8-bit RISC (Harvard)",
        core_frequency_hz=16_000_000,
        flash_bytes=262_144, # 256 KB (8KB used by bootloader)
        sram_bytes=8_192,    # 8 KB
        eeprom_bytes=4_096,  # 4 KB
        operating_voltage=5.0,
        active_power_ma=78.0,
        sleep_power_ma=22.0,
        hardware_uarts=4,
        adc_channels=16,
        adc_resolution_bits=10,
        timer_count=6,  # Timer0, Timer1, Timer2, Timer3, Timer4, Timer5
        direct_port_registers=["PORTA", "PORTB", "PORTC", "PORTD", "PORTE", "PORTF", "PORTG", "PORTH", "PORTJ", "PORTK", "PORTL"],
        pin_count=54,
        pins={
            "D0": PinMapping(pin_name="D0 (RX0)", pin_type="communication", port_register="PORTE", pin_bit=0),
            "D1": PinMapping(pin_name="D1 (TX0)", pin_type="communication", port_register="PORTE", pin_bit=1),
            "D2": PinMapping(pin_name="D2", pin_type="pwm", port_register="PORTE", pin_bit=4, interrupt_num=4),
            "D3": PinMapping(pin_name="D3", pin_type="pwm", port_register="PORTE", pin_bit=5, interrupt_num=5),
            "D13": PinMapping(pin_name="D13 (LED)", pin_type="pwm", port_register="PORTB", pin_bit=7),
            "D14": PinMapping(pin_name="D14 (TX3)", pin_type="communication", port_register="PORTJ", pin_bit=1),
            "D15": PinMapping(pin_name="D15 (RX3)", pin_type="communication", port_register="PORTJ", pin_bit=0),
            "D16": PinMapping(pin_name="D16 (TX2)", pin_type="communication", port_register="PORTH", pin_bit=1),
            "D17": PinMapping(pin_name="D17 (RX2)", pin_type="communication", port_register="PORTH", pin_bit=0),
            "D18": PinMapping(pin_name="D18 (TX1)", pin_type="communication", port_register="PORTD", pin_bit=3, interrupt_num=3),
            "D19": PinMapping(pin_name="D19 (RX1)", pin_type="communication", port_register="PORTD", pin_bit=2, interrupt_num=2),
            "D20": PinMapping(pin_name="D20 (SDA)", pin_type="communication", port_register="PORTD", pin_bit=1),
            "D21": PinMapping(pin_name="D21 (SCL)", pin_type="communication", port_register="PORTD", pin_bit=0),
            "A0": PinMapping(pin_name="A0", pin_type="analog", port_register="PORTF", pin_bit=0),
            "A1": PinMapping(pin_name="A1", pin_type="analog", port_register="PORTF", pin_bit=1),
            "A2": PinMapping(pin_name="A2", pin_type="analog", port_register="PORTF", pin_bit=2),
            "A3": PinMapping(pin_name="A3", pin_type="analog", port_register="PORTF", pin_bit=3),
            "A4": PinMapping(pin_name="A4", pin_type="analog", port_register="PORTF", pin_bit=4),
            "A5": PinMapping(pin_name="A5", pin_type="analog", port_register="PORTF", pin_bit=5),
            "A6": PinMapping(pin_name="A6", pin_type="analog", port_register="PORTF", pin_bit=6),
            "A7": PinMapping(pin_name="A7", pin_type="analog", port_register="PORTF", pin_bit=7),
            "A8": PinMapping(pin_name="A8", pin_type="analog", port_register="PORTK", pin_bit=0),
            "A15": PinMapping(pin_name="A15", pin_type="analog", port_register="PORTK", pin_bit=7),
        },
        hardware_notes="High-pinout 8-bit AVR with 54 digital I/O pins, 16 analog inputs, 4 hardware UART serial ports, and 8KB internal SRAM."
    ),

    "arduino_nano": HardwareProfile(
        id="arduino_nano",
        name="Arduino NANO Classic",
        mcu_model="ATmega328P",
        architecture="AVR 8-bit RISC (Harvard)",
        core_frequency_hz=16_000_000,
        flash_bytes=32_768,
        sram_bytes=2_048,
        eeprom_bytes=1_024,
        operating_voltage=5.0,
        active_power_ma=19.0,
        sleep_power_ma=6.5,
        hardware_uarts=1,
        adc_channels=8,  # Nano exposes A6 and A7 as analog-only
        adc_resolution_bits=10,
        timer_count=3,
        direct_port_registers=["PORTB", "PORTC", "PORTD"],
        pin_count=30,
        pins={
            "D0": PinMapping(pin_name="D0 (RX)", pin_type="communication", port_register="PORTD", pin_bit=0),
            "D1": PinMapping(pin_name="D1 (TX)", pin_type="communication", port_register="PORTD", pin_bit=1),
            "D2": PinMapping(pin_name="D2", pin_type="digital", port_register="PORTD", pin_bit=2, interrupt_num=0),
            "D3": PinMapping(pin_name="D3", pin_type="pwm", port_register="PORTD", pin_bit=3, timer_channel="OC2B", interrupt_num=1),
            "D13": PinMapping(pin_name="D13 (LED)", pin_type="digital", port_register="PORTB", pin_bit=5),
            "A0": PinMapping(pin_name="A0", pin_type="analog", port_register="PORTC", pin_bit=0),
            "A1": PinMapping(pin_name="A1", pin_type="analog", port_register="PORTC", pin_bit=1),
            "A2": PinMapping(pin_name="A2", pin_type="analog", port_register="PORTC", pin_bit=2),
            "A3": PinMapping(pin_name="A3", pin_type="analog", port_register="PORTC", pin_bit=3),
            "A4": PinMapping(pin_name="A4 (SDA)", pin_type="analog", port_register="PORTC", pin_bit=4),
            "A5": PinMapping(pin_name="A5 (SCL)", pin_type="analog", port_register="PORTC", pin_bit=5),
            "A6": PinMapping(pin_name="A6 (Analog-only)", pin_type="analog", port_register="ADC", pin_bit=6),
            "A7": PinMapping(pin_name="A7 (Analog-only)", pin_type="analog", port_register="ADC", pin_bit=7),
        },
        hardware_notes="Breadboard-friendly compact ATmega328P board with 2 extra dedicated analog inputs (A6/A7) compared to Uno."
    ),

    "arduino_leonardo": HardwareProfile(
        id="arduino_leonardo",
        name="Arduino Leonardo",
        mcu_model="ATmega32u4",
        architecture="AVR 8-bit RISC (Harvard)",
        core_frequency_hz=16_000_000,
        flash_bytes=32_768,
        sram_bytes=2_560,    # 2.5 KB
        eeprom_bytes=1_024,
        operating_voltage=5.0,
        active_power_ma=42.0,
        sleep_power_ma=12.0,
        hardware_uarts=1,
        adc_channels=12,
        adc_resolution_bits=10,
        timer_count=4,  # Timer0, Timer1, Timer3, Timer4
        direct_port_registers=["PORTB", "PORTC", "PORTD", "PORTE", "PORTF"],
        pin_count=20,
        pins={
            "D0": PinMapping(pin_name="D0 (RX)", pin_type="communication", port_register="PORTD", pin_bit=2),
            "D1": PinMapping(pin_name="D1 (TX)", pin_type="communication", port_register="PORTD", pin_bit=3),
            "D13": PinMapping(pin_name="D13 (LED)", pin_type="pwm", port_register="PORTC", pin_bit=7),
            "A0": PinMapping(pin_name="A0", pin_type="analog", port_register="PORTF", pin_bit=7),
        },
        hardware_notes="Native USB microcontroller with direct HID capabilities and 2.5KB SRAM."
    ),

    "esp32_devkit": HardwareProfile(
        id="esp32_devkit",
        name="ESP32 WROOM DevKit",
        mcu_model="ESP32-D0WDQ6",
        architecture="Xtensa 32-bit Dual-Core LX6",
        core_frequency_hz=240_000_000,
        flash_bytes=4_194_304, # 4 MB
        sram_bytes=532_480,    # 520 KB
        eeprom_bytes=4_096,
        operating_voltage=3.3,
        active_power_ma=120.0,
        sleep_power_ma=0.8,
        hardware_uarts=3,
        adc_channels=18,
        adc_resolution_bits=12,
        timer_count=4,
        direct_port_registers=["GPIO.out", "GPIO.in", "GPIO.out_w1ts", "GPIO.out_w1tc"],
        pin_count=38,
        pins={
            "GPIO2": PinMapping(pin_name="GPIO2 (LED)", pin_type="digital", port_register="GPIO", pin_bit=2),
            "GPIO4": PinMapping(pin_name="GPIO4", pin_type="analog", port_register="GPIO", pin_bit=4),
            "GPIO21": PinMapping(pin_name="GPIO21 (SDA)", pin_type="communication", port_register="GPIO", pin_bit=21),
            "GPIO22": PinMapping(pin_name="GPIO22 (SCL)", pin_type="communication", port_register="GPIO", pin_bit=22),
        },
        hardware_notes="High-performance dual-core 32-bit SoC with integrated Wi-Fi and Bluetooth, running at 240MHz with FreeRTOS multitasking."
    ),

    "stm32_bluepill": HardwareProfile(
        id="stm32_bluepill",
        name="STM32F103C8T6 (BluePill)",
        mcu_model="STM32F103C8T6",
        architecture="ARM Cortex-M3 32-bit",
        core_frequency_hz=72_000_000,
        flash_bytes=65_536,   # 64 KB (up to 128KB)
        sram_bytes=20_480,    # 20 KB
        eeprom_bytes=0,
        operating_voltage=3.3,
        active_power_ma=36.0,
        sleep_power_ma=2.2,
        hardware_uarts=3,
        adc_channels=10,
        adc_resolution_bits=12,
        timer_count=4,
        direct_port_registers=["GPIOA", "GPIOB", "GPIOC", "GPIOD"],
        pin_count=40,
        pins={
            "PC13": PinMapping(pin_name="PC13 (LED)", pin_type="digital", port_register="GPIOC", pin_bit=13),
            "PA0": PinMapping(pin_name="PA0", pin_type="analog", port_register="GPIOA", pin_bit=0),
            "PA9": PinMapping(pin_name="PA9 (TX1)", pin_type="communication", port_register="GPIOA", pin_bit=9),
            "PA10": PinMapping(pin_name="PA10 (RX1)", pin_type="communication", port_register="GPIOA", pin_bit=10),
        },
        hardware_notes="ARM Cortex-M3 processor running at 72MHz with hardware single-cycle multiplier, nested vector interrupt controller (NVIC), and dual 12-bit ADCs."
    )
}

def get_hardware_profile(board_id: str) -> HardwareProfile:
    """Retrieve hardware profile by board identifier, fallback to Arduino Uno."""
    return HARDWARE_PROFILES.get(board_id, HARDWARE_PROFILES["arduino_uno"])

def list_hardware_profiles() -> List[Dict[str, Any]]:
    """Return summary list of all available hardware profiles."""
    return [
        {
            "id": p.id,
            "name": p.name,
            "mcu": p.mcu_model,
            "arch": p.architecture,
            "clock_mhz": p.core_frequency_hz / 1_000_000,
            "flash_kb": p.flash_bytes / 1024,
            "sram_kb": p.sram_bytes / 1024,
            "adc_channels": p.adc_channels,
            "uarts": p.hardware_uarts
        }
        for p in HARDWARE_PROFILES.values()
    ]
