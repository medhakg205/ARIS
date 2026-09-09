#include "cpu_estimator.h"

CpuEstimator::CpuEstimator()
    : active_time_us(0),
      idle_time_us(0),
      last_estimated_load_pct(0.0f),
      confidence_factor(0.85f) {}

void CpuEstimator::init() {
    active_time_us = 0;
    idle_time_us = 0;
    last_estimated_load_pct = 0.0f;
    confidence_factor = 0.85f;
}

void CpuEstimator::record_active_us(uint32_t active_us) {
    active_time_us += active_us;
}

void CpuEstimator::record_idle_us(uint32_t idle_us) {
    idle_time_us += idle_us;
}

void CpuEstimator::end_epoch(uint32_t epoch_duration_ms) {
    uint32_t epoch_total_us = epoch_duration_ms * 1000UL;
    if (epoch_total_us == 0) {
        last_estimated_load_pct = 0.0f;
        return;
    }

    if (idle_time_us > 0) {
        // Explicit idle time available
        uint32_t accounted_us = active_time_us + idle_time_us;
        if (accounted_us > 0) {
            float ratio = (float)active_time_us / (float)accounted_us;
            last_estimated_load_pct = ratio * 100.0f;
            confidence_factor = 0.90f;
        }
    } else {
        // Derived from active loop execution window vs epoch time
        float ratio = (float)active_time_us / (float)epoch_total_us;
        last_estimated_load_pct = ratio * 100.0f;
        confidence_factor = 0.85f;
    }

    if (last_estimated_load_pct > 100.0f) {
        last_estimated_load_pct = 100.0f;
    }
    if (last_estimated_load_pct < 0.0f) {
        last_estimated_load_pct = 0.0f;
    }

    active_time_us = 0;
    idle_time_us = 0;
}
