/**
 * ARIS Example: Interrupt Instrumentation
 * Demonstrates safe, atomic interrupt counting and rate tracking.
 */

#include "../../runtime/aris_runtime.h"

const byte INTERRUPT_PIN = 2; // INT0 on Uno / Nano
volatile unsigned long isr_tick = 0;

void handle_external_interrupt() {
    isr_tick++;
    // Safe, non-blocking single atomic call inside ISR
    ARIS.record_isr();
}

void setup() {
    pinMode(INTERRUPT_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), handle_external_interrupt, FALLING);

    // Initialize ARIS in FULL mode to track interrupt counts and rates
    ARIS.init("arduino_uno", 115200, "ARIS-ISR-001", ARIS_MODE_FULL);
}

void loop() {
    ARIS.loop_enter();

    // Background work
    delay(20);

    ARIS.loop_exit();
}
