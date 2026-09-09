#ifndef ARIS_INSTRUMENTATION_MANAGER_H
#define ARIS_INSTRUMENTATION_MANAGER_H

#include "timing_probe.h"
#include "memory_probe.h"
#include "interrupt_probe.h"
#include "peripheral_probe.h"
#include "cpu_estimator.h"
#include "../boards/board_adapter.h"

class InstrumentationManager {
private:
    BoardAdapter* adapter;
    TimingProbe timing_probe;
    MemoryProbe memory_probe;
    InterruptProbe interrupt_probe;
    PeripheralProbe peripheral_probe;
    CpuEstimator cpu_estimator;

public:
    explicit InstrumentationManager(BoardAdapter* board_adapter);

    void init();
    void on_loop_enter(uint32_t now_us);
    void on_loop_exit(uint32_t now_us);
    void on_idle_record(uint32_t idle_us);
    void end_epoch(uint32_t epoch_duration_ms);

    BoardAdapter* get_adapter() { return adapter; }
    TimingProbe& get_timing_probe() { return timing_probe; }
    MemoryProbe& get_memory_probe() { return memory_probe; }
    InterruptProbe& get_interrupt_probe() { return interrupt_probe; }
    PeripheralProbe& get_peripheral_probe() { return peripheral_probe; }
    CpuEstimator& get_cpu_estimator() { return cpu_estimator; }
};

#endif // ARIS_INSTRUMENTATION_MANAGER_H
