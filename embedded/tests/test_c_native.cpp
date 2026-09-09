#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "../boards/board_profile.h"
#include "../boards/board_adapter.h"
#include "../boards/board_uno.h"
#include "../boards/board_nano.h"
#include "../boards/board_mega.h"
#include "../boards/board_factory.h"
#include "../instrumentation/timing_probe.h"
#include "../instrumentation/memory_probe.h"
#include "../instrumentation/interrupt_probe.h"
#include "../instrumentation/peripheral_probe.h"
#include "../instrumentation/cpu_estimator.h"
#include "../instrumentation/instrumentation_manager.h"
#include "../telemetry/telemetry_collector.h"
#include "../telemetry/telemetry_encoder.h"
#include "../runtime/aris_runtime.h"

void test_board_profiles() {
    printf("[TEST] Checking BoardProfiles...\n");
    const BoardProfile* uno = aris_get_board_profile("arduino_uno");
    assert(uno != NULL);
    assert(strcmp(uno->board_id, "arduino_uno") == 0);
    assert(strcmp(uno->mcu, "atmega328p") == 0);
    assert(strcmp(uno->architecture, "avr8") == 0);
    assert(uno->clock_hz == 16000000UL);
    assert(uno->flash_bytes == 32768UL);
    assert(uno->sram_bytes == 2048UL);
    assert(uno->gpio_count == 14);
    assert(uno->adc_channels == 6);
    assert(uno->uart_count == 1);
    assert(uno->spi_available == true);
    assert(uno->i2c_available == true);
    assert(uno->timer_count == 3);

    const BoardProfile* nano = aris_get_board_profile("arduino_nano");
    assert(nano != NULL);
    assert(strcmp(nano->board_id, "arduino_nano") == 0);
    assert(nano->adc_channels == 8);

    const BoardProfile* mega = aris_get_board_profile("arduino_mega");
    assert(mega != NULL);
    assert(strcmp(mega->board_id, "arduino_mega") == 0);
    assert(strcmp(mega->mcu, "atmega2560") == 0);
    assert(mega->sram_bytes == 8192UL);
    assert(mega->gpio_count == 54);
    assert(mega->adc_channels == 16);
    assert(mega->uart_count == 4);
    assert(mega->timer_count == 6);

    printf("  -> BoardProfiles passed.\n");
}

void test_board_adapters() {
    printf("[TEST] Checking BoardAdapters...\n");
    UnoBoardAdapter uno_adapter;
    uno_adapter.init();
    assert(strcmp(uno_adapter.get_board_id(), "arduino_uno") == 0);
    assert(uno_adapter.get_sram_total() == 2048);
    assert(uno_adapter.get_sram_free() > 0);
    assert(uno_adapter.validate_pin(13) == true);
    assert(uno_adapter.validate_pin(20) == false);
    assert(uno_adapter.validate_adc_channel(5) == true);
    assert(uno_adapter.validate_adc_channel(6) == false); // Uno only has 6

    NanoBoardAdapter nano_adapter;
    nano_adapter.init();
    assert(nano_adapter.validate_adc_channel(7) == true); // Nano has 8 (A0-A7)

    MegaBoardAdapter mega_adapter;
    mega_adapter.init();
    assert(mega_adapter.get_sram_total() == 8192);
    assert(mega_adapter.validate_pin(53) == true);
    assert(mega_adapter.validate_pin(54) == false);
    assert(mega_adapter.validate_adc_channel(15) == true);

    printf("  -> BoardAdapters passed.\n");
}

void test_timing_probe() {
    printf("[TEST] Checking TimingProbe...\n");
    TimingProbe probe;
    probe.init();

    probe.enter_loop(1000);
    probe.exit_loop(5000); // 4000 us elapsed

    // 4000 us - 2 us overhead = 3998 us = ~3.998 ms
    float loop_t = probe.get_loop_time_ms();
    assert(loop_t > 3.9f && loop_t < 4.1f);
    assert(probe.get_loop_count() == 1);
    assert(probe.get_instrumentation_overhead_us() == 2.0f);

    float freq = probe.get_loop_frequency_hz(100);
    assert(freq == 10.0f); // 1 iteration in 100ms = 10 Hz

    printf("  -> TimingProbe passed.\n");
}

void test_cpu_estimator() {
    printf("[TEST] Checking CpuEstimator...\n");
    CpuEstimator cpu;
    cpu.init();

    // 50ms active time in 100ms epoch
    cpu.record_active_us(50000);
    cpu.end_epoch(100);

    float load = cpu.get_cpu_load();
    assert(load >= 49.9f && load <= 50.1f);
    assert(cpu.get_classification() == ARIS_CLASS_ESTIMATED);
    assert(cpu.get_confidence() == 0.85f);

    // Over-budget clamping
    cpu.record_active_us(200000);
    cpu.end_epoch(100);
    assert(cpu.get_cpu_load() == 100.0f);

    printf("  -> CpuEstimator passed.\n");
}

void test_telemetry_encoding() {
    printf("[TEST] Checking TelemetryEncoder...\n");
    ArisTelemetrySample sample;
    sample.protocol_version = "1.0";
    sample.run_id = "ARIS-TEST-999";
    sample.board_id = "arduino_uno";
    sample.mcu = "atmega328p";
    sample.timestamp_ms = 12345;
    sample.sequence = 1;
    sample.metric = "loop_time";
    sample.value = 4.25f;
    sample.unit = "ms";
    sample.classification = "MEASURED";
    sample.confidence = 1.0f;

    char buf[256];
    int len = TelemetryEncoder::encode_json(&sample, buf, sizeof(buf));
    assert(len > 0);
    assert(strstr(buf, "\"protocol_version\":\"1.0\"") != NULL);
    assert(strstr(buf, "\"run_id\":\"ARIS-TEST-999\"") != NULL);
    assert(strstr(buf, "\"board_id\":\"arduino_uno\"") != NULL);
    assert(strstr(buf, "\"mcu\":\"atmega328p\"") != NULL);
    assert(strstr(buf, "\"metric\":\"loop_time\"") != NULL);
    assert(strstr(buf, "\"classification\":\"MEASURED\"") != NULL);

    int compact_len = TelemetryEncoder::encode_compact_frame(
        "ARIS-TEST-999", "arduino_uno", "atmega328p",
        12345, 1, 35.5f, 4.25f, 235.0f, 0.1f,
        500, 1548, 64, 128, 5, 50.0f,
        10, 2, 25, 0, 0, 10,
        1, 0, 0, 1.5f,
        buf, sizeof(buf)
    );
    assert(compact_len > 0);
    assert(strncmp(buf, "$ARIS1,", 7) == 0);
    assert(buf[compact_len - 1] == '#');

    printf("  -> TelemetryEncoder passed.\n");
}

void test_runtime_agent() {
    printf("[TEST] Checking ArisRuntime Agent...\n");
    ARIS.init("arduino_uno", 115200, "ARIS-NATIVE-TEST", ARIS_MODE_BALANCED);
    assert(ARIS.is_initialized() == true);
    assert(strcmp(ARIS.get_collector()->get_run_id(), "ARIS-NATIVE-TEST") == 0);

    ARIS.loop_enter();
    ARIS.record_gpio(2);
    ARIS.record_adc(1);
    ARIS.record_isr();
    ARIS.loop_exit();

    ARIS.dispatch_telemetry(100);
    const char* packet = ARIS.get_last_packet();
    assert(strlen(packet) > 0);
    assert(strncmp(packet, "$ARIS1,", 7) == 0);

    printf("  -> ArisRuntime Agent passed.\n");
}

int main() {
    printf("===========================================\n");
    printf("ARIS Embedded Native C++ Verification Suite\n");
    printf("===========================================\n");

    test_board_profiles();
    test_board_adapters();
    test_timing_probe();
    test_cpu_estimator();
    test_telemetry_encoding();
    test_runtime_agent();

    printf("===========================================\n");
    printf("ALL NATIVE C++ VERIFICATION TESTS PASSED!\n");
    printf("===========================================\n");
    return 0;
}
