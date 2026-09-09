#include "board_nano.h"

#if defined(__AVR__)
#include <avr/io.h>
#include <avr/wdt.h>

extern uint8_t _end;
extern uint8_t __bss_end;
extern uint8_t *__brkval;

#define STACK_SENTINEL 0x5A
#else
static uint16_t mock_free_sram_nano = 1480;
static uint16_t mock_stack_watermark_nano = 160;
#define STACK_SENTINEL 0x5A
#endif

NanoBoardAdapter::NanoBoardAdapter() 
    : BoardAdapter(&PROFILE_ARDUINO_NANO), stack_high_water(0) {}

void NanoBoardAdapter::init() {
#if defined(__AVR__)
    reset_flags = MCUSR;
    MCUSR = 0;

    uint8_t *p = &__bss_end;
    uint8_t *sp = (uint8_t *)SP;
    while (p < sp - 32) {
        *p++ = STACK_SENTINEL;
    }
#else
    reset_flags = 0x01;
    stack_high_water = mock_stack_watermark_nano;
#endif
}

uint16_t NanoBoardAdapter::get_sram_free() {
#if defined(__AVR__)
    uint8_t free_memory_marker;
    if (__brkval == 0) {
        return (uint16_t)((uint8_t*)&free_memory_marker - &__bss_end);
    } else {
        return (uint16_t)((uint8_t*)&free_memory_marker - __brkval);
    }
#else
    return mock_free_sram_nano;
#endif
}

uint16_t NanoBoardAdapter::get_stack_used() {
#if defined(__AVR__)
    return (uint16_t)((uint8_t*)RAMEND - (uint8_t*)SP);
#else
    return 80;
#endif
}

uint16_t NanoBoardAdapter::get_stack_high_water_mark() {
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

bool NanoBoardAdapter::is_watchdog_reset() const {
#if defined(__AVR__)
    return (reset_flags & (1 << WDRF)) != 0;
#else
    return false;
#endif
}

bool NanoBoardAdapter::validate_adc_channel(uint8_t channel) const {
    // Nano exposes 8 channels (A0-A7)
    return channel < 8;
}
