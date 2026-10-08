#include "instrumentation_manager.h"

InstrumentationManager::InstrumentationManager(BoardAdapter* board_adapter)
    : adapter(board_adapter),
      timing_probe(),
      memory_probe(board_adapter),
      interrupt_probe(),
      peripheral_probe(),
      cpu_estimator() {}

void InstrumentationManager::init() {
    if (adapter) adapter->init();
    timing_probe.init();
    interrupt_probe.init();
    peripheral_probe.init();
    cpu_estimator.init();
}

void InstrumentationManager::on_loop_enter(uint32_t now_us) {
    timing_probe.enter_loop(now_us);
}

void InstrumentationManager::on_loop_exit(uint32_t now_us) {
    timing_probe.exit_loop(now_us);
}

void InstrumentationManager::on_idle_record(uint32_t idle_us) {
    cpu_estimator.record_idle_us(idle_us);
}

void InstrumentationManager::end_epoch(uint32_t epoch_duration_ms) {
    cpu_estimator.record_active_us(timing_probe.get_total_active_us());
    cpu_estimator.end_epoch(epoch_duration_ms);
    interrupt_probe.end_epoch();
    peripheral_probe.end_epoch();
    timing_probe.reset_epoch();
}
