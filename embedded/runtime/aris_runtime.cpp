#include "aris_runtime.h"
#include "../boards/board_factory.h"
#include <string.h>
#include <stdio.h>

#if !defined(ARDUINO) && !defined(__AVR__)
// Host test environment time stubs
static uint32_t mock_system_ms = 1000;
static uint32_t mock_system_us = 1000000;

static uint32_t host_millis() { return mock_system_ms; }
static uint32_t host_micros() { return mock_system_us; }
#define millis host_millis
#define micros host_micros
#endif

ArisRuntime::ArisRuntime()
    : adapter(nullptr),
      manager(nullptr),
      collector(nullptr),
      config(aris_default_config()),
      last_epoch_ms(0),
      initialized(false) {
    transmit_buffer[0] = '\0';
}

ArisRuntime::~ArisRuntime() {
    delete collector;
    delete manager;
    delete adapter;
}

void ArisRuntime::init(
    const char* board_id,
    uint32_t baud_rate,
    const char* run_id,
    ArisInstrumentationMode mode
) {
    // Detect board if not explicitly provided
    if (!board_id) {
#if defined(__AVR_ATmega328P__)
        board_id = "arduino_uno";
#elif defined(__AVR_ATmega2560__)
        board_id = "arduino_mega";
#else
        board_id = "arduino_uno";
#endif
    }

    delete collector;
    delete manager;
    delete adapter;

    adapter = aris_create_board_adapter(board_id);
    manager = new InstrumentationManager(adapter);
    collector = new TelemetryCollector(manager);

    config.serial_baud_rate = baud_rate;
    config.mode = mode;
    collector->set_mode(mode);
    collector->set_run_id(run_id);

    manager->init();

#if defined(ARDUINO)
    Serial.begin(baud_rate);
#endif

    last_epoch_ms = millis();
    initialized = true;
}

void ArisRuntime::set_mode(ArisInstrumentationMode mode) {
    config.mode = mode;
    if (collector) collector->set_mode(mode);
}

void ArisRuntime::set_run_id(const char* run_id) {
    if (collector) collector->set_run_id(run_id);
}

void ArisRuntime::loop_enter() {
    if (!initialized) return;
    manager->on_loop_enter(micros());
}

void ArisRuntime::loop_exit() {
    if (!initialized) return;
    manager->on_loop_exit(micros());

    uint32_t now = millis();
    if (now - last_epoch_ms >= config.epoch_interval_ms) {
        dispatch_telemetry(now);
        last_epoch_ms = now;
    }
}

void ArisRuntime::record_isr() {
    if (manager) manager->get_interrupt_probe().record_interrupt();
}

void ArisRuntime::record_gpio(uint16_t count) {
    if (manager) manager->get_peripheral_probe().record_gpio(count);
}

void ArisRuntime::record_adc(uint16_t count) {
    if (manager) manager->get_peripheral_probe().record_adc(count);
}

void ArisRuntime::record_uart(uint16_t count) {
    if (manager) manager->get_peripheral_probe().record_uart(count);
}

void ArisRuntime::record_spi(uint16_t count) {
    if (manager) manager->get_peripheral_probe().record_spi(count);
}

void ArisRuntime::record_i2c(uint16_t count) {
    if (manager) manager->get_peripheral_probe().record_i2c(count);
}

void ArisRuntime::record_timer(uint16_t count) {
    if (manager) manager->get_peripheral_probe().record_timer(count);
}

void ArisRuntime::record_idle(uint32_t idle_us) {
    if (manager) manager->on_idle_record(idle_us);
}

void ArisRuntime::dispatch_telemetry(uint32_t now_ms) {
    if (!initialized || !manager || !collector) return;

    uint32_t epoch_duration = now_ms - last_epoch_ms;
    if (epoch_duration == 0) epoch_duration = config.epoch_interval_ms;

    manager->end_epoch(epoch_duration);

    if (config.enable_compact_framing) {
        // Fast framing packet
        TelemetryEncoder::encode_compact_frame(
            collector->get_run_id(),
            adapter ? adapter->get_board_id() : "unknown",
            adapter ? adapter->get_mcu() : "unknown",
            now_ms,
            collector->get_next_sequence(),
            manager->get_cpu_estimator().get_cpu_load(),
            manager->get_timing_probe().get_loop_time_ms(),
            manager->get_timing_probe().get_loop_frequency_hz(epoch_duration),
            manager->get_timing_probe().get_loop_jitter_ms(),
            manager->get_memory_probe().get_sram_used(),
            manager->get_memory_probe().get_sram_free(),
            manager->get_memory_probe().get_stack_used(),
            manager->get_memory_probe().get_stack_high_water_mark(),
            manager->get_interrupt_probe().get_interrupt_count(),
            manager->get_interrupt_probe().get_interrupt_rate_hz(epoch_duration),
            manager->get_peripheral_probe().get_gpio_activity(),
            manager->get_peripheral_probe().get_adc_activity(),
            manager->get_peripheral_probe().get_uart_activity(),
            manager->get_peripheral_probe().get_spi_activity(),
            manager->get_peripheral_probe().get_i2c_activity(),
            manager->get_peripheral_probe().get_timer_activity(),
            adapter ? adapter->get_reset_flags() : 0,
            (adapter && adapter->is_watchdog_reset()) ? 1 : 0,
            0, // runtime_fault = 0
            manager->get_timing_probe().get_instrumentation_overhead_us(),
            transmit_buffer,
            ARIS_BUFFER_SIZE
        );

#if defined(ARDUINO)
        Serial.println(transmit_buffer);
#endif
    } else if (config.enable_json_stream) {
        // Line-delimited canonical JSON stream
        ArisTelemetrySample samples[ARIS_METRIC_COUNT];
        uint8_t count = collector->collect_all_samples(now_ms, epoch_duration, samples, ARIS_METRIC_COUNT);
        for (uint8_t i = 0; i < count; i++) {
            TelemetryEncoder::encode_json(&samples[i], transmit_buffer, ARIS_BUFFER_SIZE);
#if defined(ARDUINO)
            Serial.println(transmit_buffer);
#endif
        }
    }
}

// Global ARIS Singleton Instance
ArisRuntime ARIS;
