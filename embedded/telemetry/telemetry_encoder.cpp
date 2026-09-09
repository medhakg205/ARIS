#include "telemetry_encoder.h"
#include <stdio.h>
#include <string.h>

int TelemetryEncoder::encode_json(const ArisTelemetrySample* sample, char* buffer, size_t buffer_size) {
    if (!sample || !buffer || buffer_size == 0) return -1;

    // Canonical JSON format:
    // {
    //     "protocol_version": "1.0",
    //     "run_id": "ARIS-000001",
    //     "board_id": "arduino_uno",
    //     "mcu": "atmega328p",
    //     "timestamp_ms": 123456,
    //     "sequence": 42,
    //     "metric": "loop_time",
    //     "value": 4.21,
    //     "unit": "ms",
    //     "classification": "MEASURED",
    //     "confidence": 1.0
    // }
    return snprintf(
        buffer,
        buffer_size,
        "{\"protocol_version\":\"%s\",\"run_id\":\"%s\",\"board_id\":\"%s\",\"mcu\":\"%s\","
        "\"timestamp_ms\":%lu,\"sequence\":%lu,\"metric\":\"%s\",\"value\":%.2f,"
        "\"unit\":\"%s\",\"classification\":\"%s\",\"confidence\":%.2f}",
        sample->protocol_version ? sample->protocol_version : ARIS_PROTOCOL_VERSION,
        sample->run_id ? sample->run_id : ARIS_DEFAULT_RUN_ID,
        sample->board_id ? sample->board_id : "unknown",
        sample->mcu ? sample->mcu : "unknown",
        (unsigned long)sample->timestamp_ms,
        (unsigned long)sample->sequence,
        sample->metric ? sample->metric : "unknown",
        (double)sample->value,
        sample->unit ? sample->unit : "",
        sample->classification ? sample->classification : "MEASURED",
        (double)sample->confidence
    );
}

int TelemetryEncoder::encode_compact_frame(
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
) {
    if (!buffer || buffer_size == 0) return -1;

    // Fast framing: $ARIS1,run_id,board_id,mcu,timestamp,seq,cpu,loop_t,loop_f,jitter,s_used,s_free,stk_used,stk_max,isr_c,isr_r,gpio,adc,uart,spi,i2c,timer,reset,wdt,fault,overhead#
    return snprintf(
        buffer,
        buffer_size,
        "$ARIS1,%s,%s,%s,%lu,%lu,%.2f,%.2f,%.2f,%.2f,%u,%u,%u,%u,%u,%.2f,%u,%u,%u,%u,%u,%u,%u,%u,%u,%.2f#",
        run_id ? run_id : ARIS_DEFAULT_RUN_ID,
        board_id ? board_id : "arduino_uno",
        mcu ? mcu : "atmega328p",
        (unsigned long)timestamp_ms,
        (unsigned long)sequence,
        (double)cpu_load,
        (double)loop_time,
        (double)loop_frequency,
        (double)loop_jitter,
        (unsigned int)sram_used,
        (unsigned int)sram_free,
        (unsigned int)stack_used,
        (unsigned int)stack_high_water,
        (unsigned int)isr_count,
        (double)isr_rate,
        (unsigned int)gpio,
        (unsigned int)adc,
        (unsigned int)uart,
        (unsigned int)spi,
        (unsigned int)i2c,
        (unsigned int)timer,
        (unsigned int)reset_event,
        (unsigned int)watchdog_event,
        (unsigned int)runtime_fault,
        (double)overhead_us
    );
}
