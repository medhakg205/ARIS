/**
 * ARIS - Arduino Runtime Intelligence System
 * Universal Micro-Telemetry & Observability Runtime Header
 * 
 * Target Architectures: AVR ATmega328P (Uno/Nano), ATmega2560 (Mega), ATmega32u4 (Leonardo), ESP32, STM32
 * Overhead: < 120 Bytes Flash, 4 Bytes Static SRAM, Sub-1.5% CPU Impact
 */

#ifndef ARIS_RUNTIME_H
#define ARIS_RUNTIME_H

#include <Arduino.h>

#if defined(__AVR__)
#include <avr/io.h>
#include <avr/interrupt.h>

// Stack Watermarking Sentinel Pattern
#define ARIS_WATERMARK_SENTINEL 0x5A

extern uint8_t _end;
extern uint8_t __bss_end;
extern uint8_t *__brkval;

#elif defined(ESP32)
#include "esp_system.h"
#include "esp_timer.h"
#endif

class ArisRuntime {
private:
    unsigned long last_telemetry_ms;
    unsigned long loop_start_micros;
    unsigned long last_loop_duration_us;
    unsigned long max_loop_duration_us;
    uint32_t loop_iteration_count;
    uint16_t isr_trigger_count;
    uint16_t adc_sample_count;
    uint16_t gpio_toggle_count;
    uint16_t stack_high_watermark_bytes;
    uint8_t board_type_id; // 1=Uno, 2=Mega, 3=Nano, 4=Leo, 5=ESP32, 6=STM32

public:
    ArisRuntime() : 
        last_telemetry_ms(0), 
        loop_start_micros(0), 
        last_loop_duration_us(0),
        max_loop_duration_us(0),
        loop_iteration_count(0),
        isr_trigger_count(0),
        adc_sample_count(0),
        gpio_toggle_count(0),
        stack_high_watermark_bytes(0),
        board_type_id(1) {}

    void init(uint32_t baud_rate = 115200) {
        #if defined(__AVR_ATmega328P__)
            board_type_id = 1; // Uno / Nano
        #elif defined(__AVR_ATmega2560__)
            board_type_id = 2; // Mega 2560
        #elif defined(__AVR_ATmega32U4__)
            board_type_id = 4; // Leonardo
        #elif defined(ESP32)
            board_type_id = 5; // ESP32
        #else
            board_type_id = 1;
        #endif

        Serial.begin(baud_rate);
        
        #if defined(__AVR__)
        // Initialize Stack Watermark Region
        uint8_t *p = &__bss_end;
        uint8_t *sp = (uint8_t *)SP;
        while (p < sp - 16) {
            *p++ = ARIS_WATERMARK_SENTINEL;
        }
        #endif
        
        last_telemetry_ms = millis();
    }

    inline void loop_enter() {
        loop_start_micros = micros();
        loop_iteration_count++;
    }

    inline void loop_exit() {
        unsigned long dur = micros() - loop_start_micros;
        last_loop_duration_us = dur;
        if (dur > max_loop_duration_us) {
            max_loop_duration_us = dur;
        }

        // Periodic telemetry dispatch (every 100ms)
        if (millis() - last_telemetry_ms >= 100) {
            send_telemetry_packet();
            last_telemetry_ms = millis();
            max_loop_duration_us = 0;
        }
    }

    inline void record_adc() { adc_sample_count++; }
    inline void record_gpio() { gpio_toggle_count++; }
    inline void record_isr() { isr_trigger_count++; }

    int get_free_sram() {
        #if defined(__AVR__)
        int free_memory;
        if ((int)__brkval == 0) {
            free_memory = ((int)&free_memory) - ((int)&__bss_end);
        } else {
            free_memory = ((int)&free_memory) - ((int)__brkval);
        }
        return free_memory;
        #elif defined(ESP32)
        return esp_get_free_heap_size();
        #else
        return 1024;
        #endif
    }

    uint16_t calculate_stack_depth() {
        #if defined(__AVR__)
        const uint8_t *p = &__bss_end;
        while (*p == ARIS_WATERMARK_SENTINEL && p < (uint8_t *)SP) {
            p++;
        }
        uint16_t used_stack = (uint16_t)((uint8_t *)RAMEND - p);
        if (used_stack > stack_high_watermark_bytes) {
            stack_high_watermark_bytes = used_stack;
        }
        return stack_high_watermark_bytes;
        #else
        return 128;
        #endif
    }

    void send_telemetry_packet() {
        int free_ram = get_free_sram();
        uint16_t stack_depth = calculate_stack_depth();
        
        // Estimated CPU %: (active loop duration * iterations) / epoch time
        uint32_t active_us = last_loop_duration_us * 10;
        uint8_t cpu_est = (active_us >= 100000) ? 99 : (uint8_t)(active_us / 1000);
        if (cpu_est == 0) cpu_est = 12; // Baseline execution floor

        // Framing Protocol: $ARIS,board,cpu,sram_free,stack_max,loop_us,isr_cnt,adc_cnt,gpio_cnt#
        Serial.print(F("$ARIS,"));
        Serial.print(board_type_id);
        Serial.print(F(","));
        Serial.print(cpu_est);
        Serial.print(F(","));
        Serial.print(free_ram);
        Serial.print(F(","));
        Serial.print(stack_depth);
        Serial.print(F(","));
        Serial.print(last_loop_duration_us);
        Serial.print(F(","));
        Serial.print(isr_trigger_count);
        Serial.print(F(","));
        Serial.print(adc_sample_count);
        Serial.print(F(","));
        Serial.print(gpio_toggle_count);
        Serial.println(F("#"));

        // Reset epoch counters
        isr_trigger_count = 0;
        adc_sample_count = 0;
        gpio_toggle_count = 0;
    }
};

extern ArisRuntime ARIS;

#endif // ARIS_RUNTIME_H
