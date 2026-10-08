#ifndef ARIS_CPU_ESTIMATOR_H
#define ARIS_CPU_ESTIMATOR_H

#include "../runtime/aris_types.h"
#include <stdint.h>

/**
 * CpuEstimator provides a defensible runtime CPU load estimation for AVR microcontrollers.
 * NOTE: ATmega328P/ATmega2560 do NOT have hardware PMU/performance registers.
 * Metric is strictly ESTIMATED, never MEASURED.
 */
class CpuEstimator {
private:
    uint32_t active_time_us;
    uint32_t idle_time_us;
    float last_estimated_load_pct;
    float confidence_factor;

public:
    CpuEstimator();
    void init();
    void record_active_us(uint32_t active_us);
    void record_idle_us(uint32_t idle_us);
    void end_epoch(uint32_t epoch_duration_ms);

    float get_cpu_load() const { return last_estimated_load_pct; }
    ArisClassification get_classification() const { return ARIS_CLASS_ESTIMATED; }
    float get_confidence() const { return confidence_factor; }
};

#endif // ARIS_CPU_ESTIMATOR_H
