#include "interrupt_probe.h"

#if defined(__AVR__)
#include <avr/interrupt.h>
#endif

InterruptProbe::InterruptProbe() : interrupt_counter(0), last_epoch_count(0) {}

void InterruptProbe::init() {
    interrupt_counter = 0;
    last_epoch_count = 0;
}

void InterruptProbe::record_interrupt() {
    // Lightweight atomic increment inside ISR
    interrupt_counter++;
}

void InterruptProbe::end_epoch() {
#if defined(__AVR__)
    uint8_t sreg = SREG;
    cli();
    last_epoch_count = interrupt_counter;
    interrupt_counter = 0;
    SREG = sreg;
#else
    last_epoch_count = interrupt_counter;
    interrupt_counter = 0;
#endif
}

uint16_t InterruptProbe::get_interrupt_count() const {
    return last_epoch_count;
}

float InterruptProbe::get_interrupt_rate_hz(uint32_t epoch_duration_ms) const {
    if (epoch_duration_ms == 0) return 0.0f;
    return ((float)last_epoch_count * 1000.0f) / (float)epoch_duration_ms;
}
