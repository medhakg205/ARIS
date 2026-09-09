#ifndef ARIS_RUNTIME_H
#define ARIS_RUNTIME_H

#include "aris_types.h"
#include "aris_config.h"
#include "../boards/board_adapter.h"
#include "../instrumentation/instrumentation_manager.h"
#include "../telemetry/telemetry_collector.h"
#include "../telemetry/telemetry_encoder.h"
#include <stdint.h>

#if defined(ARDUINO) || defined(__AVR__)
#include <Arduino.h>
#endif

class ArisRuntime {
private:
    BoardAdapter* adapter;
    InstrumentationManager* manager;
    TelemetryCollector* collector;
    ArisConfig config;
    uint32_t last_epoch_ms;
    bool initialized;

    // Buffer for serial transmissions
    char transmit_buffer[ARIS_BUFFER_SIZE];

public:
    ArisRuntime();
    ~ArisRuntime();

    void init(
        const char* board_id = nullptr,
        uint32_t baud_rate = 115200UL,
        const char* run_id = ARIS_DEFAULT_RUN_ID,
        ArisInstrumentationMode mode = ARIS_MODE_BALANCED
    );

    void set_mode(ArisInstrumentationMode mode);
    void set_run_id(const char* run_id);

    // Primary Loop Instrumentation Hooks
    void loop_enter();
    void loop_exit();

    // Event and Peripheral Activity Recording
    void record_isr();
    void record_gpio(uint16_t count = 1);
    void record_adc(uint16_t count = 1);
    void record_uart(uint16_t count = 1);
    void record_spi(uint16_t count = 1);
    void record_i2c(uint16_t count = 1);
    void record_timer(uint16_t count = 1);
    void record_idle(uint32_t idle_us);

    // Telemetry Generation & Transmission
    void dispatch_telemetry(uint32_t now_ms);

    // Getters for internal components (for testing and verification)
    BoardAdapter* get_adapter() { return adapter; }
    InstrumentationManager* get_manager() { return manager; }
    TelemetryCollector* get_collector() { return collector; }
    const ArisConfig& get_config() const { return config; }
    bool is_initialized() const { return initialized; }

    // Direct helper to fetch last formatted packet string
    const char* get_last_packet() const { return transmit_buffer; }
};

extern ArisRuntime ARIS;

#endif // ARIS_RUNTIME_H
