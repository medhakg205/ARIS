#include "board_uno.h"

#if defined(__AVR__)
#include <avr/io.h>
#include <avr/wdt.h>

extern uint8_t _end;
extern uint8_t __bss_end;
extern uint8_t *__brkval;

#define STACK_SENTINEL 0x5A
#else
// Mock declarations for host testing
static uint16_t mock_free_sram = 1536;
static uint16_t mock_stack_watermark = 142;
#define STACK_SENTINEL 0x5A
#endif

UnoBoardAdapter::UnoBoardAdapter() 
    : BoardAdapter(&PROFILE_ARDUINO_UNO), stack_high_water(0) {}

void UnoBoardAdapter::init() {
#if defined(__AVR__)
    // Capture reset flags from MCUSR
    reset_flags = MCUSR;
    MCUSR = 0; // Clear reset flags

    // Paint stack watermark from end of BSS to current SP - safety margin
    uint8_t *p = &__bss_end;
    uint8_t *sp = (uint8_t *)SP;
    while (p < sp - 32) {
        *p++ = STACK_SENTINEL;
    }
#else
    reset_flags = 0x01; // Power-on reset mock
    stack_high_water = mock_stack_watermark;
#endif
}

uint16_t UnoBoardAdapter::get_sram_free() {
#if defined(__AVR__)
    uint8_t free_memory_marker;
    if (__brkval == 0) {
        return (uint16_t)((uint8_t*)&free_memory_marker - &__bss_end);
    } else {
        return (uint16_t)((uint8_t*)&free_memory_marker - __brkval);
    }
#else
    return mock_free_sram;
#endif
}

uint16_t UnoBoardAdapter::get_stack_used() {
#if defined(__AVR__)
    return (uint16_t)((uint8_t*)RAMEND - (uint8_t*)SP);
#else
    return 64; // Mock stack used
#endif
}

uint16_t UnoBoardAdapter::get_stack_high_water_mark() {
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

bool UnoBoardAdapter::is_watchdog_reset() const {
#if defined(__AVR__)
    return (reset_flags & (1 << WDRF)) != 0;
#else
    return false;
#endif
}
