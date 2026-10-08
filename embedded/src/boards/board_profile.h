#ifndef ARIS_BOARD_PROFILE_H
#define ARIS_BOARD_PROFILE_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    const char* board_id;
    const char* display_name;
    const char* mcu;
    const char* architecture;
    uint32_t clock_hz;
    uint32_t flash_bytes;
    uint32_t sram_bytes;
    uint32_t eeprom_bytes;
    uint8_t gpio_count;
    uint8_t adc_channels;
    uint8_t uart_count;
    bool spi_available;
    bool i2c_available;
    uint8_t timer_count;
    const char* const* interrupt_capabilities;
    uint8_t interrupt_capability_count;
} BoardProfile;

/* Static profiles for compile-time or runtime access */
extern const BoardProfile PROFILE_ARDUINO_UNO;
extern const BoardProfile PROFILE_ARDUINO_NANO;
extern const BoardProfile PROFILE_ARDUINO_MEGA;

const BoardProfile* aris_get_board_profile(const char* board_id);

#ifdef __cplusplus
}
#endif

#endif /* ARIS_BOARD_PROFILE_H */
