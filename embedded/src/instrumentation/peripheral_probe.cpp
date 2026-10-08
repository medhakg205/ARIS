#include "peripheral_probe.h"

PeripheralProbe::PeripheralProbe()
    : gpio_counter(0), adc_counter(0), uart_counter(0), spi_counter(0), i2c_counter(0), timer_counter(0),
      last_gpio(0), last_adc(0), last_uart(0), last_spi(0), last_i2c(0), last_timer(0) {}

void PeripheralProbe::init() {
    gpio_counter = adc_counter = uart_counter = spi_counter = i2c_counter = timer_counter = 0;
    last_gpio = last_adc = last_uart = last_spi = last_i2c = last_timer = 0;
}

void PeripheralProbe::record_gpio(uint16_t count) { gpio_counter += count; }
void PeripheralProbe::record_adc(uint16_t count) { adc_counter += count; }
void PeripheralProbe::record_uart(uint16_t count) { uart_counter += count; }
void PeripheralProbe::record_spi(uint16_t count) { spi_counter += count; }
void PeripheralProbe::record_i2c(uint16_t count) { i2c_counter += count; }
void PeripheralProbe::record_timer(uint16_t count) { timer_counter += count; }

void PeripheralProbe::end_epoch() {
    last_gpio = gpio_counter;
    last_adc = adc_counter;
    last_uart = uart_counter;
    last_spi = spi_counter;
    last_i2c = i2c_counter;
    last_timer = timer_counter;

    gpio_counter = 0;
    adc_counter = 0;
    uart_counter = 0;
    spi_counter = 0;
    i2c_counter = 0;
    timer_counter = 0;
}
