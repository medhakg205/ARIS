#include "board_mega.h"

#if defined(__AVR__)
#include <avr/io.h>
#include <avr/wdt.h>

extern uint8_t _end;
extern uint8_t __bss_end;
extern uint8_t *__brkval;

#define STACK_SENTINEL 0x5A
#else
static uint16_t mock_free_sram_mega = 7200;
static uint16_t mock_stack_watermark_mega = 310;
#define STACK_SENTINEL 0x5A
#endif

MegaBoardAdapter::MegaBoardAdapter() 
    : BoardAdapter(&PROFILE_ARDUINO_MEGA), stack_high_water(0) {}

void MegaBoardAdapter::init() {
#if defined(__AVR__)
    reset_flags = MCUSR;
    MCUSR = 0;

    // Mega 2560 has 8KB of SRAM up to 0x21FF
    uint8_t *p = &__bss_end;
    uint8_t *sp = (uint8_t *)SP;
    while (p < sp - 64) {
        *p++ = STACK_SENTINEL;
    }
#else
    reset_flags = 0x01;
    stack_high_water = mock_stack_watermark_mega;
#endif
}

uint16_t MegaBoardAdapter::get_sram_free() {
#if defined(__AVR__)
    uint8_t free_memory_marker;
    if (__brkval == 0) {
        return (uint16_t)((uint8_t*)&free_memory_marker - &__bss_end);
    } else {
        return (uint16_t)((uint8_t*)&free_memory_marker - __brkval);
    }
#else
    return mock_free_sram_mega;
#endif
}

uint16_t MegaBoardAdapter::get_stack_used() {
#if defined(__AVR__)
    return (uint16_t)((uint8_t*)RAMEND - (uint8_t*)SP);
#else
    return 120;
#endif
}

uint16_t MegaBoardAdapter::get_stack_high_water_mark() {
#if defined(__AVR__)
    const uint8_t *p = &__bss_end;
    while (p < (const uint8_t *)RAMEND && *p == STACK_SENTINEL) {
        p++;
    }
    uint16_t water_mark = (uint16_t)((const uint8_t *)RAMEND - p);
    if (water_mark > stack_high_water) {
        stack_high_water = water_mark;
    }
    return stack_high_water;
#else
    return stack_high_water;
#endif
}

bool MegaBoardAdapter::is_watchdog_reset() const {
#if defined(__AVR__)
    return (reset_flags & (1 << WDRF)) != 0;
#else
    return false;
#endif
}

bool MegaBoardAdapter::validate_pin(uint8_t pin) const {
    // Mega 2560 has 54 digital IO pins
    return pin < 54;
}

bool MegaBoardAdapter::validate_adc_channel(uint8_t channel) const {
    // Mega 2560 has 16 analog input pins
    return channel < 16;
}
