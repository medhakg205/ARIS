/**
 * ARIS Example: Sensor Monitor
 * Demonstrates analog sampling, filtering, and telemetry integration.
 */

#include "../../runtime/aris_runtime.h"

const int SENSOR_PIN = A0;
const int ALERT_PIN = 12;
const int THRESHOLD = 512;
unsigned long last_sample_ms = 0;
const unsigned long SAMPLE_INTERVAL_MS = 50;

void setup() {
    pinMode(ALERT_PIN, OUTPUT);

    // Initialize ARIS for Arduino Uno in FULL mode
    ARIS.init("arduino_uno", 115200, "ARIS-SENSOR-001", ARIS_MODE_FULL);
}

void loop() {
    ARIS.loop_enter();

    unsigned long now = millis();
    if (now - last_sample_ms >= SAMPLE_INTERVAL_MS) {
        last_sample_ms = now;

        int raw_value = analogRead(SENSOR_PIN);
        ARIS.record_adc(1);

        if (raw_value > THRESHOLD) {
            digitalWrite(ALERT_PIN, HIGH);
            ARIS.record_gpio(1);
        } else {
            digitalWrite(ALERT_PIN, LOW);
            ARIS.record_gpio(1);
        }
    }

    ARIS.loop_exit();
}
