#ifndef ARIS_INTERRUPT_PROBE_H
#define ARIS_INTERRUPT_PROBE_H

#include <stdint.h>

class InterruptProbe {
private:
    volatile uint16_t interrupt_counter;
    uint16_t last_epoch_count;

public:
    InterruptProbe();
    void init();
    void record_interrupt();
    void end_epoch();
    
    uint16_t get_interrupt_count() const;
    float get_interrupt_rate_hz(uint32_t epoch_duration_ms) const;
};

#endif // ARIS_INTERRUPT_PROBE_H
