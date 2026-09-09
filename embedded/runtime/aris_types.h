#ifndef ARIS_TYPES_H
#define ARIS_TYPES_H

#include <stdint.h>
#include <stdbool.h>

#define ARIS_PROTOCOL_VERSION "1.0"
#define ARIS_DEFAULT_RUN_ID "ARIS-2026-000001"

typedef enum {
    ARIS_METRIC_CPU_LOAD = 0,
    ARIS_METRIC_LOOP_TIME,
    ARIS_METRIC_LOOP_FREQUENCY,
    ARIS_METRIC_LOOP_JITTER,
    ARIS_METRIC_SRAM_USED,
    ARIS_METRIC_SRAM_FREE,
    ARIS_METRIC_STACK_USED,
    ARIS_METRIC_STACK_HIGH_WATER_MARK,
    ARIS_METRIC_INTERRUPT_COUNT,
    ARIS_METRIC_INTERRUPT_RATE,
    ARIS_METRIC_GPIO_ACTIVITY,
    ARIS_METRIC_ADC_ACTIVITY,
    ARIS_METRIC_UART_ACTIVITY,
    ARIS_METRIC_SPI_ACTIVITY,
    ARIS_METRIC_I2C_ACTIVITY,
    ARIS_METRIC_TIMER_ACTIVITY,
    ARIS_METRIC_RESET_EVENT,
    ARIS_METRIC_WATCHDOG_EVENT,
    ARIS_METRIC_RUNTIME_FAULT,
    ARIS_METRIC_INSTRUMENTATION_OVERHEAD,
    ARIS_METRIC_COUNT
} ArisMetricType;

typedef enum {
    ARIS_CLASS_MEASURED = 0,
    ARIS_CLASS_ESTIMATED,
    ARIS_CLASS_DERIVED,
    ARIS_CLASS_PREDICTED
} ArisClassification;

typedef enum {
    ARIS_MODE_LOW = 0,
    ARIS_MODE_BALANCED,
    ARIS_MODE_FULL
} ArisInstrumentationMode;

typedef struct {
    const char* protocol_version;
    const char* run_id;
    const char* board_id;
    const char* mcu;
    uint32_t timestamp_ms;
    uint32_t sequence;
    const char* metric;
    float value;
    const char* unit;
    const char* classification;
    float confidence;
} ArisTelemetrySample;

#ifdef __cplusplus
extern "C" {
#endif

const char* aris_metric_name(ArisMetricType metric);
const char* aris_metric_default_unit(ArisMetricType metric);
const char* aris_classification_name(ArisClassification classification);
ArisClassification aris_metric_default_classification(ArisMetricType metric);
float aris_metric_default_confidence(ArisMetricType metric);

#ifdef __cplusplus
}
#endif

#endif // ARIS_TYPES_H
