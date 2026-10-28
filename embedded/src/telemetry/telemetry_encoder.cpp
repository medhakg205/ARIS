#include "telemetry_encoder.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int TelemetryEncoder::encode_json(const ArisTelemetrySample* sample, char* buffer, size_t buffer_size) {
    if (!sample || !buffer || buffer_size == 0) return -1;

#if defined(ARDUINO) || defined(__AVR__)
    char val_buf[16];
    char conf_buf[16];
    dtostrf(sample->value, 1, 2, val_buf);
    dtostrf(sample->confidence, 1, 2, conf_buf);
    char* vp = val_buf; while (*vp == ' ') vp++;
    char* cp = conf_buf; while (*cp == ' ') cp++;

    size_t idx = 0;
    auto append_s = [&](const char* s) {
        if (!s) return;
        while (*s && idx < buffer_size - 1) buffer[idx++] = *s++;
    };
    auto append_u = [&](uint32_t val) {
        char nb[12]; int ni = 0;
        if (val == 0) nb[ni++] = '0';
        else {
            while (val > 0) { nb[ni++] = '0' + (val % 10); val /= 10; }
            for (int i = 0; i < ni / 2; i++) { char t = nb[i]; nb[i] = nb[ni - 1 - i]; nb[ni - 1 - i] = t; }
        }
        nb[ni] = '\0'; append_s(nb);
    };

    append_s("{\"protocol_version\":\""); append_s(sample->protocol_version ? sample->protocol_version : ARIS_PROTOCOL_VERSION);
    append_s("\",\"run_id\":\""); append_s(sample->run_id ? sample->run_id : ARIS_DEFAULT_RUN_ID);
    append_s("\",\"board_id\":\""); append_s(sample->board_id ? sample->board_id : "unknown");
    append_s("\",\"mcu\":\""); append_s(sample->mcu ? sample->mcu : "unknown");
    append_s("\",\"timestamp_ms\":"); append_u(sample->timestamp_ms);
    append_s(",\"sequence\":"); append_u(sample->sequence);
    append_s(",\"metric\":\""); append_s(sample->metric ? sample->metric : "unknown");
    append_s("\",\"value\":"); append_s(vp);
    append_s(",\"unit\":\""); append_s(sample->unit ? sample->unit : "");
    append_s("\",\"classification\":\""); append_s(sample->classification ? sample->classification : "MEASURED");
    append_s("\",\"confidence\":"); append_s(cp);
    append_s("}");

    buffer[idx] = '\0';
    return (int)idx;
#else
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
#endif
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

    size_t idx = 0;
    auto append_s = [&](const char* s) {
        if (!s) return;
        while (*s && idx < buffer_size - 1) {
            buffer[idx++] = *s++;
        }
    };
    auto append_u = [&](uint32_t val) {
        char nb[12];
        int ni = 0;
        if (val == 0) {
            nb[ni++] = '0';
        } else {
            while (val > 0) {
                nb[ni++] = '0' + (val % 10);
                val /= 10;
            }
            for (int i = 0; i < ni / 2; i++) {
                char t = nb[i];
                nb[i] = nb[ni - 1 - i];
                nb[ni - 1 - i] = t;
            }
        }
        nb[ni] = '\0';
        append_s(nb);
    };
    auto append_f = [&](float val) {
#if defined(ARDUINO) || defined(__AVR__)
        char fb[16];
        dtostrf(val, 1, 2, fb);
        // Trim leading spaces if any
        char* p = fb;
        while (*p == ' ') p++;
        append_s(p);
#else
        char fb[16];
        snprintf(fb, sizeof(fb), "%.2f", (double)val);
        append_s(fb);
#endif
    };

    append_s("$ARIS1,");
    append_s(run_id ? run_id : ARIS_DEFAULT_RUN_ID); append_s(",");
    append_s(board_id ? board_id : "arduino_uno"); append_s(",");
    append_s(mcu ? mcu : "atmega328p"); append_s(",");
    append_u(timestamp_ms); append_s(",");
    append_u(sequence); append_s(",");
    append_f(cpu_load); append_s(",");
    append_f(loop_time); append_s(",");
    append_f(loop_frequency); append_s(",");
    append_f(loop_jitter); append_s(",");
    append_u(sram_used); append_s(",");
    append_u(sram_free); append_s(",");
    append_u(stack_used); append_s(",");
    append_u(stack_high_water); append_s(",");
    append_u(isr_count); append_s(",");
    append_f(isr_rate); append_s(",");
    append_u(gpio); append_s(",");
    append_u(adc); append_s(",");
    append_u(uart); append_s(",");
    append_u(spi); append_s(",");
    append_u(i2c); append_s(",");
    append_u(timer); append_s(",");
    append_u(reset_event); append_s(",");
    append_u(watchdog_event); append_s(",");
    append_u(runtime_fault); append_s(",");
    append_f(overhead_us);
    append_s("#");

    buffer[idx] = '\0';
    return (int)idx;
}

int TelemetryEncoder::encode_handshake_ack(
    const char* runtime_version,
    const char* protocol_version,
    const char* board_id,
    const char* mcu,
    const char* architecture,
    uint32_t clock_hz,
    const char* mode_name,
    char* buffer,
    size_t buffer_size
) {
    if (!buffer || buffer_size < 40) return -1;

    const char* rv = runtime_version ? runtime_version : "2.0.0";
    const char* pv = protocol_version ? protocol_version : "1.0";
    const char* b = board_id ? board_id : "arduino_uno";
    const char* m = mcu ? mcu : "atmega328p";
    const char* a = architecture ? architecture : "avr8";
    const char* md = mode_name ? mode_name : "BALANCED";
    uint32_t clk = clock_hz ? clock_hz : 16000000UL;

    size_t idx = 0;
    auto append_str = [&](const char* s) {
        while (*s && idx < buffer_size - 1) {
            buffer[idx++] = *s++;
        }
    };

    append_str("$ARIS_ACK,");
    append_str(rv);
    append_str(",");
    append_str(pv);
    append_str(",");
    append_str(b);
    append_str(",");
    append_str(m);
    append_str(",");
    append_str(a);
    append_str(",");

    // Format clk decimal
    char num_buf[12];
    int n_idx = 0;
    if (clk == 0) {
        num_buf[n_idx++] = '0';
    } else {
        uint32_t temp = clk;
        while (temp > 0 && n_idx < 10) {
            num_buf[n_idx++] = '0' + (temp % 10);
            temp /= 10;
        }
        // Reverse
        for (int i = 0; i < n_idx / 2; i++) {
            char t = num_buf[i];
            num_buf[i] = num_buf[n_idx - 1 - i];
            num_buf[n_idx - 1 - i] = t;
        }
    }
    num_buf[n_idx] = '\0';
    append_str(num_buf);

    append_str(",");
    append_str(md);
    append_str("#");

    buffer[idx] = '\0';
    return (int)idx;
}
