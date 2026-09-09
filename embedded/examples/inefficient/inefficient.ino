/**
 * ARIS Example: Inefficient Antipattern Sketch
 * 
 * IMPORTANT: This firmware deliberately incorporates severe embedded antipatterns
 * for detection by ARIS static analysis and runtime telemetry:
 * 1. Blocking delays: delay(150) inside the main loop stalling CPU and dropping responsiveness.
 * 2. Unnecessary repeated calculations: redundant floating-point trigonometry & math in every loop.
 * 3. Excessive busy-wait polling: tight while-loops with pin queries without hardware interrupts.
 * 4. Unnecessary verbose serial logging: Serial.print string spam flooding UART output buffers.
 * 5. SRAM string exhaustion: literal strings not wrapped in F() macro eating precious 2KB AVR SRAM.
 */

#include "../../runtime/aris_runtime.h"
#include <math.h>

const int BUTTON_PIN = 7;
const int LED_PIN = 13;
const int SENSOR_PIN = A0;

float cached_result = 0.0;

void setup() {
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    pinMode(LED_PIN, OUTPUT);

    // Initialize ARIS runtime
    ARIS.init("arduino_uno", 115200, "ARIS-INEFFICIENT-001", ARIS_MODE_BALANCED);
}

void loop() {
    ARIS.loop_enter();

    // Antipattern 1: Excessive busy-wait polling on pin with no sleep or timer
    int poll_counter = 0;
    while (digitalRead(BUTTON_PIN) == LOW && poll_counter < 500) {
        poll_counter++;
        ARIS.record_gpio(1);
    }

    // Antipattern 2: Unnecessary repeated 32-bit software floating-point calculations
    // AVR ATmega328P has no FPU; each float sin/cos/sqrt takes hundreds of CPU cycles
    for (int i = 0; i < 25; i++) {
        float angle = (float)i * 0.1234f;
        cached_result += sin(angle) * cos(angle) + sqrt((float)i + 1.0f);
    }

    // Antipattern 3: Unnecessary verbose serial logging in tight loop with uninterned strings
    // Consumes RAM and blocks serial UART buffers
    Serial.println("==================================================");
    Serial.print("Current Sensor Reading: ");
    int val = analogRead(SENSOR_PIN);
    ARIS.record_adc(1);
    Serial.println(val);
    Serial.print("Computed Mathematical Result: ");
    Serial.println(cached_result);
    Serial.println("End of transmission cycle - preparing next iteration");

    // Antipattern 4: Heavy blocking delay stalling the CPU
    // Causes high loop_time, low loop_frequency, and 100% estimated active CPU utilization
    digitalWrite(LED_PIN, HIGH);
    ARIS.record_gpio(1);
    delay(150); // Blocking delay 150ms

    digitalWrite(LED_PIN, LOW);
    ARIS.record_gpio(1);
    delay(150); // Blocking delay 150ms

    ARIS.loop_exit();
}
