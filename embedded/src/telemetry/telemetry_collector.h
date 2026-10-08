#ifndef ARIS_TELEMETRY_COLLECTOR_H
#define ARIS_TELEMETRY_COLLECTOR_H

#include "../runtime/aris_types.h"
#include "../runtime/aris_config.h"
#include "../instrumentation/instrumentation_manager.h"
#include <stdint.h>

class TelemetryCollector {
private:
    InstrumentationManager* manager;
    char current_run_id[ARIS_RUN_ID_MAX_LEN];
    uint32_t sequence_number;
    ArisInstrumentationMode mode;

public:
    explicit TelemetryCollector(InstrumentationManager* mgr);

    void set_run_id(const char* run_id);
    const char* get_run_id() const { return current_run_id; }
    void set_mode(ArisInstrumentationMode m) { mode = m; }
    ArisInstrumentationMode get_mode() const { return mode; }
    uint32_t get_next_sequence() { return sequence_number++; }

    // Generates a sample for a specific metric
    bool collect_sample(ArisMetricType metric, uint32_t now_ms, uint32_t epoch_ms, ArisTelemetrySample* out_sample);

    // Collects all active metrics for the current mode into a sample array
    uint8_t collect_all_samples(uint32_t now_ms, uint32_t epoch_ms, ArisTelemetrySample* out_samples, uint8_t max_samples);
};

#endif // ARIS_TELEMETRY_COLLECTOR_H
