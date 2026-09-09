#ifndef ARIS_PERIPHERAL_PROBE_H
#define ARIS_PERIPHERAL_PROBE_H

#include <stdint.h>

class PeripheralProbe {
private:
    uint16_t gpio_counter;
    uint16_t adc_counter;
    uint16_t uart_counter;
    uint16_t spi_counter;
    uint16_t i2c_counter;
    uint16_t timer_counter;

    uint16_t last_gpio;
    uint16_t last_adc;
    uint16_t last_uart;
    uint16_t last_spi;
    uint16_t last_i2c;
    uint16_t last_timer;

public:
    PeripheralProbe();
    void init();
    void end_epoch();

    void record_gpio(uint16_t count = 1);
    void record_adc(uint16_t count = 1);
    void record_uart(uint16_t count = 1);
    void record_spi(uint16_t count = 1);
    void record_i2c(uint16_t count = 1);
    void record_timer(uint16_t count = 1);

    uint16_t get_gpio_activity() const { return last_gpio; }
    uint16_t get_adc_activity() const { return last_adc; }
    uint16_t get_uart_activity() const { return last_uart; }
    uint16_t get_spi_activity() const { return last_spi; }
    uint16_t get_i2c_activity() const { return last_i2c; }
    uint16_t get_timer_activity() const { return last_timer; }
};

#endif // ARIS_PERIPHERAL_PROBE_H
