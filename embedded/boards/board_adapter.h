#ifndef ARIS_BOARD_ADAPTER_H
#define ARIS_BOARD_ADAPTER_H

#include "board_profile.h"
#include <stdint.h>
#include <stddef.h>

class BoardAdapter {
protected:
    const BoardProfile* profile;
    uint8_t reset_flags;

public:
    explicit BoardAdapter(const BoardProfile* prof) : profile(prof), reset_flags(0) {}
    virtual ~BoardAdapter() = default;

    const BoardProfile* get_profile() const { return profile; }
    const char* get_board_id() const { return profile ? profile->board_id : "unknown"; }
    const char* get_mcu() const { return profile ? profile->mcu : "unknown"; }

    virtual void init() = 0;
    virtual uint16_t get_sram_total() const { return profile ? (uint16_t)profile->sram_bytes : 0; }
    virtual uint16_t get_sram_free() = 0;
    virtual uint16_t get_stack_used() = 0;
    virtual uint16_t get_stack_high_water_mark() = 0;
    virtual uint8_t get_reset_flags() const { return reset_flags; }
    virtual bool is_watchdog_reset() const = 0;
    virtual bool validate_pin(uint8_t pin) const { return profile && (pin < profile->gpio_count); }
    virtual bool validate_adc_channel(uint8_t channel) const { return profile && (channel < profile->adc_channels); }
};

#endif // ARIS_BOARD_ADAPTER_H
