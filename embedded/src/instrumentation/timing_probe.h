#ifndef ARIS_TIMING_PROBE_H
#define ARIS_TIMING_PROBE_H

#include <stdint.h>

class TimingProbe {
private:
    uint32_t loop_start_us;
    uint32_t last_loop_time_us;
    uint32_t min_loop_time_us;
    uint32_t max_loop_time_us;
    uint32_t total_active_us;
    uint32_t loop_count;
    float jitter_ema_us;
    uint16_t calibrated_overhead_us;

public:
    TimingProbe();
    void init();
    void enter_loop(uint32_t now_us);
    void exit_loop(uint32_t now_us);
    void reset_epoch();

    float get_loop_time_ms() const;
    float get_loop_frequency_hz(uint32_t epoch_duration_ms) const;
    float get_loop_jitter_ms() const;
    uint32_t get_total_active_us() const { return total_active_us; }
    uint32_t get_loop_count() const { return loop_count; }
    float get_instrumentation_overhead_us() const;
};

#endif // ARIS_TIMING_PROBE_H
