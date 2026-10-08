#include "telemetry_collector.h"
#include <string.h>

TelemetryCollector::TelemetryCollector(InstrumentationManager* mgr)
    : manager(mgr), sequence_number(1), mode(ARIS_MODE_BALANCED) {
    strncpy(current_run_id, ARIS_DEFAULT_RUN_ID, ARIS_RUN_ID_MAX_LEN - 1);
    current_run_id[ARIS_RUN_ID_MAX_LEN - 1] = '\0';
}

void TelemetryCollector::set_run_id(const char* run_id) {
    if (run_id && strlen(run_id) > 0) {
        strncpy(current_run_id, run_id, ARIS_RUN_ID_MAX_LEN - 1);
        current_run_id[ARIS_RUN_ID_MAX_LEN - 1] = '\0';
    }
}

bool TelemetryCollector::collect_sample(ArisMetricType metric, uint32_t now_ms, uint32_t epoch_ms, ArisTelemetrySample* out_sample) {
    if (!manager || !out_sample) return false;

    BoardAdapter* adapter = manager->get_adapter();
    const char* board_id = adapter ? adapter->get_board_id() : "unknown";
    const char* mcu = adapter ? adapter->get_mcu() : "unknown";

    out_sample->protocol_version = ARIS_PROTOCOL_VERSION;
    out_sample->run_id = current_run_id;
    out_sample->board_id = board_id;
    out_sample->mcu = mcu;
    out_sample->timestamp_ms = now_ms;
    out_sample->sequence = get_next_sequence();
    out_sample->metric = aris_metric_name(metric);
    out_sample->unit = aris_metric_default_unit(metric);
    out_sample->classification = aris_classification_name(aris_metric_default_classification(metric));
    out_sample->confidence = aris_metric_default_confidence(metric);

    switch (metric) {
        case ARIS_METRIC_CPU_LOAD:
            out_sample->value = manager->get_cpu_estimator().get_cpu_load();
            out_sample->classification = "ESTIMATED"; // Strictly ESTIMATED
            out_sample->confidence = manager->get_cpu_estimator().get_confidence();
            break;

        case ARIS_METRIC_LOOP_TIME:
            out_sample->value = manager->get_timing_probe().get_loop_time_ms();
            break;

        case ARIS_METRIC_LOOP_FREQUENCY:
            out_sample->value = manager->get_timing_probe().get_loop_frequency_hz(epoch_ms);
            break;

        case ARIS_METRIC_LOOP_JITTER:
            out_sample->value = manager->get_timing_probe().get_loop_jitter_ms();
            break;

        case ARIS_METRIC_SRAM_USED:
            out_sample->value = (float)manager->get_memory_probe().get_sram_used();
            break;

        case ARIS_METRIC_SRAM_FREE:
            out_sample->value = (float)manager->get_memory_probe().get_sram_free();
            break;

        case ARIS_METRIC_STACK_USED:
            out_sample->value = (float)manager->get_memory_probe().get_stack_used();
            break;

        case ARIS_METRIC_STACK_HIGH_WATER_MARK:
            out_sample->value = (float)manager->get_memory_probe().get_stack_high_water_mark();
            break;

        case ARIS_METRIC_INTERRUPT_COUNT:
            out_sample->value = (float)manager->get_interrupt_probe().get_interrupt_count();
            break;

        case ARIS_METRIC_INTERRUPT_RATE:
            out_sample->value = manager->get_interrupt_probe().get_interrupt_rate_hz(epoch_ms);
            break;

        case ARIS_METRIC_GPIO_ACTIVITY:
            out_sample->value = (float)manager->get_peripheral_probe().get_gpio_activity();
            break;

        case ARIS_METRIC_ADC_ACTIVITY:
            out_sample->value = (float)manager->get_peripheral_probe().get_adc_activity();
            break;

        case ARIS_METRIC_UART_ACTIVITY:
            out_sample->value = (float)manager->get_peripheral_probe().get_uart_activity();
            break;

        case ARIS_METRIC_SPI_ACTIVITY:
            out_sample->value = (float)manager->get_peripheral_probe().get_spi_activity();
            break;

        case ARIS_METRIC_I2C_ACTIVITY:
            out_sample->value = (float)manager->get_peripheral_probe().get_i2c_activity();
            break;

        case ARIS_METRIC_TIMER_ACTIVITY:
            out_sample->value = (float)manager->get_peripheral_probe().get_timer_activity();
            break;

        case ARIS_METRIC_RESET_EVENT:
            out_sample->value = (float)(adapter ? adapter->get_reset_flags() : 0);
            break;

        case ARIS_METRIC_WATCHDOG_EVENT:
            out_sample->value = (adapter && adapter->is_watchdog_reset()) ? 1.0f : 0.0f;
            break;

        case ARIS_METRIC_RUNTIME_FAULT:
            out_sample->value = 0.0f; // 0 = no fault
            break;

        case ARIS_METRIC_INSTRUMENTATION_OVERHEAD:
            out_sample->value = manager->get_timing_probe().get_instrumentation_overhead_us();
            break;

        default:
            return false;
    }

    return true;
}

uint8_t TelemetryCollector::collect_all_samples(uint32_t now_ms, uint32_t epoch_ms, ArisTelemetrySample* out_samples, uint8_t max_samples) {
    uint8_t count = 0;

    // Filter metrics according to mode
    // LOW: cpu_load, loop_time, sram_free, instrumentation_overhead
    // BALANCED: adds loop_frequency, loop_jitter, sram_used, stack_high_water_mark, interrupt_count, interrupt_rate
    // FULL: all 20 metrics
    for (int m = 0; m < ARIS_METRIC_COUNT && count < max_samples; m++) {
        ArisMetricType metric = (ArisMetricType)m;
        bool include = false;

        if (mode == ARIS_MODE_LOW) {
            include = (metric == ARIS_METRIC_CPU_LOAD ||
                       metric == ARIS_METRIC_LOOP_TIME ||
                       metric == ARIS_METRIC_SRAM_FREE ||
                       metric == ARIS_METRIC_INSTRUMENTATION_OVERHEAD);
        } else if (mode == ARIS_MODE_BALANCED) {
            include = (metric == ARIS_METRIC_CPU_LOAD ||
                       metric == ARIS_METRIC_LOOP_TIME ||
                       metric == ARIS_METRIC_LOOP_FREQUENCY ||
                       metric == ARIS_METRIC_LOOP_JITTER ||
                       metric == ARIS_METRIC_SRAM_USED ||
                       metric == ARIS_METRIC_SRAM_FREE ||
                       metric == ARIS_METRIC_STACK_HIGH_WATER_MARK ||
                       metric == ARIS_METRIC_INTERRUPT_COUNT ||
                       metric == ARIS_METRIC_INTERRUPT_RATE ||
                       metric == ARIS_METRIC_INSTRUMENTATION_OVERHEAD);
        } else { // FULL
            include = true;
        }

        if (include) {
            if (collect_sample(metric, now_ms, epoch_ms, &out_samples[count])) {
                count++;
            }
        }
    }

    return count;
}
