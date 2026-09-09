#ifndef ARIS_MEMORY_PROBE_H
#define ARIS_MEMORY_PROBE_H

#include "../boards/board_adapter.h"
#include <stdint.h>

class MemoryProbe {
private:
    BoardAdapter* adapter;

public:
    explicit MemoryProbe(BoardAdapter* board_adapter) : adapter(board_adapter) {}

    uint16_t get_sram_free();
    uint16_t get_sram_used();
    uint16_t get_stack_used();
    uint16_t get_stack_high_water_mark();
};

#endif // ARIS_MEMORY_PROBE_H
