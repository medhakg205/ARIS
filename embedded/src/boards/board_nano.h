#ifndef ARIS_BOARD_NANO_H
#define ARIS_BOARD_NANO_H

#include "board_adapter.h"

class NanoBoardAdapter : public BoardAdapter {
private:
    uint16_t stack_high_water;

public:
    NanoBoardAdapter();
    void init() override;
    uint16_t get_sram_free() override;
    uint16_t get_stack_used() override;
    uint16_t get_stack_high_water_mark() override;
    bool is_watchdog_reset() const override;
    bool validate_adc_channel(uint8_t channel) const override;
};

#endif // ARIS_BOARD_NANO_H
