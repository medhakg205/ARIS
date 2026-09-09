// ARIS Benchmark Example 03: RAM String Literal Exhaustion (Memory Starvation)
// Target: Arduino Uno / Nano (2KB SRAM limit)

void setup() {
  Serial.begin(115200);
}

void loop() {
  // All these raw string literals are duplicated in 2KB SRAM at startup
  Serial.println("=================================================");
  Serial.println("SYSTEM STATUS: RUNNING ATMEGA328P TELEMETRY");
  Serial.println("INITIALIZING ADC CHANNELS AND ANALOG SENSORS");
  Serial.println("WARNING: HIGH SRAM MEMORY ALLOCATION DETECTED");
  Serial.println("DATA FRAME PACKET DISPATCHED OVER SERIAL UART");
  Serial.println("=================================================");
  delay(100);
}
