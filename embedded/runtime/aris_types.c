#include "aris_types.h"

static const char* const METRIC_NAMES[ARIS_METRIC_COUNT] = {
    "cpu_load",
    "loop_time",
    "loop_frequency",
    "loop_jitter",
    "sram_used",
    "sram_free",
    "stack_used",
    "stack_high_water_mark",
    "interrupt_count",
    "interrupt_rate",
    "gpio_activity",
    "adc_activity",
    "uart_activity",
    "spi_activity",
    "i2c_activity",
    "timer_activity",
    "reset_event",
    "watchdog_event",
    "runtime_fault",
    "instrumentation_overhead"
};

static const char* const METRIC_UNITS[ARIS_METRIC_COUNT] = {
    "%",
    "ms",
    "Hz",
    "ms",
    "bytes",
    "bytes",
    "bytes",
    "bytes",
    "count",
    "Hz",
    "events",
    "conversions",
    "bytes",
    "transfers",
    "transactions",
    "events",
    "flags",
    "events",
    "code",
    "us"
};

static const ArisClassification METRIC_DEFAULT_CLASSES[ARIS_METRIC_COUNT] = {
    ARIS_CLASS_ESTIMATED, // cpu_load MUST be ESTIMATED on AVR
    ARIS_CLASS_MEASURED,  // loop_time
    ARIS_CLASS_DERIVED,   // loop_frequency
    ARIS_CLASS_DERIVED,   // loop_jitter
    ARIS_CLASS_DERIVED,   // sram_used
    ARIS_CLASS_MEASURED,  // sram_free
    ARIS_CLASS_DERIVED,   // stack_used
    ARIS_CLASS_ESTIMATED, // stack_high_water_mark
    ARIS_CLASS_MEASURED,  // interrupt_count
    ARIS_CLASS_DERIVED,   // interrupt_rate
    ARIS_CLASS_MEASURED,  // gpio_activity
    ARIS_CLASS_MEASURED,  // adc_activity
    ARIS_CLASS_MEASURED,  // uart_activity
    ARIS_CLASS_MEASURED,  // spi_activity
    ARIS_CLASS_MEASURED,  // i2c_activity
    ARIS_CLASS_MEASURED,  // timer_activity
    ARIS_CLASS_MEASURED,  // reset_event
    ARIS_CLASS_MEASURED,  // watchdog_event
    ARIS_CLASS_MEASURED,  // runtime_fault
    ARIS_CLASS_MEASURED   // instrumentation_overhead
};

static const float METRIC_DEFAULT_CONFIDENCES[ARIS_METRIC_COUNT] = {
    0.85f, // cpu_load
    1.0f,  // loop_time
    1.0f,  // loop_frequency
    0.95f, // loop_jitter
    1.0f,  // sram_used
    1.0f,  // sram_free
    1.0f,  // stack_used
    0.95f, // stack_high_water_mark
    1.0f,  // interrupt_count
    0.95f, // interrupt_rate
    1.0f,  // gpio_activity
    1.0f,  // adc_activity
    1.0f,  // uart_activity
    1.0f,  // spi_activity
    1.0f,  // i2c_activity
    1.0f,  // timer_activity
    1.0f,  // reset_event
    1.0f,  // watchdog_event
    1.0f,  // runtime_fault
    1.0f   // instrumentation_overhead
};

const char* aris_metric_name(ArisMetricType metric) {
    if (metric < ARIS_METRIC_COUNT) {
        return METRIC_NAMES[metric];
    }
    return "unknown";
}

const char* aris_metric_default_unit(ArisMetricType metric) {
    if (metric < ARIS_METRIC_COUNT) {
        return METRIC_UNITS[metric];
    }
    return "";
}

const char* aris_classification_name(ArisClassification classification) {
    switch (classification) {
        case ARIS_CLASS_MEASURED: return "MEASURED";
        case ARIS_CLASS_ESTIMATED: return "ESTIMATED";
        case ARIS_CLASS_DERIVED: return "DERIVED";
        case ARIS_CLASS_PREDICTED: return "PREDICTED";
        default: return "MEASURED";
    }
}

ArisClassification aris_metric_default_classification(ArisMetricType metric) {
    if (metric < ARIS_METRIC_COUNT) {
        return METRIC_DEFAULT_CLASSES[metric];
    }
    return ARIS_CLASS_MEASURED;
}

float aris_metric_default_confidence(ArisMetricType metric) {
    if (metric < ARIS_METRIC_COUNT) {
        return METRIC_DEFAULT_CONFIDENCES[metric];
    }
    return 1.0f;
}
