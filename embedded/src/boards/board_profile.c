#include "board_profile.h"
#include <string.h>

static const char* const UNO_INTERRUPTS[] = {
    "INT0", "INT1",
    "PCINT0", "PCINT1", "PCINT2",
    "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF"
};

static const char* const NANO_INTERRUPTS[] = {
    "INT0", "INT1",
    "PCINT0", "PCINT1", "PCINT2",
    "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF"
};

static const char* const MEGA_INTERRUPTS[] = {
    "INT0", "INT1", "INT2", "INT3", "INT4", "INT5",
    "PCINT0", "PCINT1", "PCINT2",
    "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF",
    "TIMER3_OVF", "TIMER4_OVF", "TIMER5_OVF"
};

const BoardProfile PROFILE_ARDUINO_UNO = {
    .board_id = "arduino_uno",
    .display_name = "Arduino Uno",
    .mcu = "atmega328p",
    .architecture = "avr8",
    .clock_hz = 16000000UL,
    .flash_bytes = 32768UL,
    .sram_bytes = 2048UL,
    .eeprom_bytes = 1024UL,
    .gpio_count = 14,
    .adc_channels = 6,
    .uart_count = 1,
    .spi_available = true,
    .i2c_available = true,
    .timer_count = 3,
    .interrupt_capabilities = UNO_INTERRUPTS,
    .interrupt_capability_count = sizeof(UNO_INTERRUPTS) / sizeof(UNO_INTERRUPTS[0])
};

const BoardProfile PROFILE_ARDUINO_NANO = {
    .board_id = "arduino_nano",
    .display_name = "Arduino Nano",
    .mcu = "atmega328p",
    .architecture = "avr8",
    .clock_hz = 16000000UL,
    .flash_bytes = 32768UL,
    .sram_bytes = 2048UL,
    .eeprom_bytes = 1024UL,
    .gpio_count = 14,
    .adc_channels = 8,
    .uart_count = 1,
    .spi_available = true,
    .i2c_available = true,
    .timer_count = 3,
    .interrupt_capabilities = NANO_INTERRUPTS,
    .interrupt_capability_count = sizeof(NANO_INTERRUPTS) / sizeof(NANO_INTERRUPTS[0])
};

const BoardProfile PROFILE_ARDUINO_MEGA = {
    .board_id = "arduino_mega",
    .display_name = "Arduino Mega 2560",
    .mcu = "atmega2560",
    .architecture = "avr8",
    .clock_hz = 16000000UL,
    .flash_bytes = 262144UL,
    .sram_bytes = 8192UL,
    .eeprom_bytes = 4096UL,
    .gpio_count = 54,
    .adc_channels = 16,
    .uart_count = 4,
    .spi_available = true,
    .i2c_available = true,
    .timer_count = 6,
    .interrupt_capabilities = MEGA_INTERRUPTS,
    .interrupt_capability_count = sizeof(MEGA_INTERRUPTS) / sizeof(MEGA_INTERRUPTS[0])
};

const BoardProfile* aris_get_board_profile(const char* board_id) {
    if (!board_id) return NULL;
    if (strcmp(board_id, "arduino_uno") == 0) return &PROFILE_ARDUINO_UNO;
    if (strcmp(board_id, "arduino_nano") == 0) return &PROFILE_ARDUINO_NANO;
    if (strcmp(board_id, "arduino_mega") == 0) return &PROFILE_ARDUINO_MEGA;
    return NULL;
}
