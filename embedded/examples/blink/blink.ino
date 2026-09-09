/**
 * ARIS Example: Clean Blink
 * Demonstrates non-blocking state machine with ARIS runtime instrumentation.
 */

#include "../../runtime/aris_runtime.h"

const int LED_PIN = 13;
unsigned long last_toggle_ms = 0;
const unsigned long BLINK_INTERVAL_MS = 500;
bool led_state = false;

void setup() {
    pinMode(LED_PIN, OUTPUT);

    // Initialize ARIS Embedded Intelligence Layer
    ARIS.init("arduino_uno", 115200, "ARIS-BLINK-001", ARIS_MODE_BALANCED);
}

void loop() {
    ARIS.loop_enter();

    unsigned long current_ms = millis();
    if (current_ms - last_toggle_ms >= BLINK_INTERVAL_MS) {
        last_toggle_ms = current_ms;
        led_state = !led_state;
        digitalWrite(LED_PIN, led_state ? HIGH : LOW);
        ARIS.record_gpio(1);
    }

    ARIS.loop_exit();
}
