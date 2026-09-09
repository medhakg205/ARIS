#include "memory_probe.h"

uint16_t MemoryProbe::get_sram_free() {
    if (!adapter) return 0;
    return adapter->get_sram_free();
}

uint16_t MemoryProbe::get_sram_used() {
    if (!adapter) return 0;
    uint16_t total = adapter->get_sram_total();
    uint16_t free_mem = adapter->get_sram_free();
    return (total >= free_mem) ? (total - free_mem) : 0;
}

uint16_t MemoryProbe::get_stack_used() {
    if (!adapter) return 0;
    return adapter->get_stack_used();
}

uint16_t MemoryProbe::get_stack_high_water_mark() {
    if (!adapter) return 0;
    return adapter->get_stack_high_water_mark();
}
