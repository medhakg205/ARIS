#include "timing_probe.h"
#include <stdlib.h>

TimingProbe::TimingProbe()
    : loop_start_us(0),
      last_loop_time_us(0),
      min_loop_time_us(0xFFFFFFFF),
      max_loop_time_us(0),
      total_active_us(0),
      loop_count(0),
      jitter_ema_us(0.0f),
      calibrated_overhead_us(2) // ~2 us on 16MHz AVR (32 cycles total for enter+exit)
{}

void TimingProbe::init() {
    reset_epoch();
}

void TimingProbe::enter_loop(uint32_t now_us) {
    loop_start_us = now_us;
}

void TimingProbe::exit_loop(uint32_t now_us) {
    uint32_t elapsed_us = (now_us >= loop_start_us) ? (now_us - loop_start_us) : (0xFFFFFFFF - loop_start_us + now_us);
    
    // Cycle-subtraction compensation for probe overhead
    if (elapsed_us > calibrated_overhead_us) {
        elapsed_us -= calibrated_overhead_us;
    }

    // Jitter calculation: Exponential moving average of delta
    if (loop_count > 0) {
        float delta = (float)(elapsed_us > last_loop_time_us ? elapsed_us - last_loop_time_us : last_loop_time_us - elapsed_us);
        jitter_ema_us = (0.2f * delta) + (0.8f * jitter_ema_us);
    }

    last_loop_time_us = elapsed_us;
    total_active_us += elapsed_us;
    loop_count++;

    if (elapsed_us < min_loop_time_us) min_loop_time_us = elapsed_us;
    if (elapsed_us > max_loop_time_us) max_loop_time_us = elapsed_us;
}

void TimingProbe::reset_epoch() {
    total_active_us = 0;
    loop_count = 0;
    min_loop_time_us = 0xFFFFFFFF;
    max_loop_time_us = 0;
}

float TimingProbe::get_loop_time_ms() const {
    return (float)last_loop_time_us / 1000.0f;
}

float TimingProbe::get_loop_frequency_hz(uint32_t epoch_duration_ms) const {
    if (epoch_duration_ms == 0) return 0.0f;
    return ((float)loop_count * 1000.0f) / (float)epoch_duration_ms;
}

float TimingProbe::get_loop_jitter_ms() const {
    return jitter_ema_us / 1000.0f;
}

float TimingProbe::get_instrumentation_overhead_us() const {
    return (float)calibrated_overhead_us;
}
