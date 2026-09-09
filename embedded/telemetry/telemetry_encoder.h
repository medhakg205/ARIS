#ifndef ARIS_TELEMETRY_ENCODER_H
#define ARIS_TELEMETRY_ENCODER_H

#include "../runtime/aris_types.h"
#include <stddef.h>

class TelemetryEncoder {
public:
    // Encodes a single sample into canonical JSON format conforming to the ARIS v1.0 specification
    static int encode_json(const ArisTelemetrySample* sample, char* buffer, size_t buffer_size);

    // Encodes an entire telemetry frame into compact ASCII framing for low-overhead serial transport
    static int encode_compact_frame(
        const char* run_id,
        const char* board_id,
        const char* mcu,
        uint32_t timestamp_ms,
        uint32_t sequence,
        float cpu_load,
        float loop_time,
        float loop_frequency,
        float loop_jitter,
        uint16_t sram_used,
        uint16_t sram_free,
        uint16_t stack_used,
        uint16_t stack_high_water,
        uint16_t isr_count,
        float isr_rate,
        uint16_t gpio,
        uint16_t adc,
        uint16_t uart,
        uint16_t spi,
        uint16_t i2c,
        uint16_t timer,
        uint8_t reset_event,
        uint8_t watchdog_event,
        uint8_t runtime_fault,
        float overhead_us,
        char* buffer,
        size_t buffer_size
    );
};

#endif // ARIS_TELEMETRY_ENCODER_H
