// ARIS Benchmark Example 01: Blocking Delay & Sensor Polling Antipattern
// Target: Arduino Uno / Nano (ATmega328P)

void setup() {
  Serial.begin(115200);
  pinMode(13, OUTPUT);
}

void loop() {
  // Synchronous ADC reading
  int sensorValue = analogRead(A0);
  
  // High-overhead RAM string literals (consumes SRAM)
  Serial.print("Sensor Raw ADC Reading: ");
  Serial.println(sensorValue);
  
  // Toggle LED using slow HAL function
  digitalWrite(13, HIGH);
  
  // Severe blocking busy-wait stalls MCU execution for 20ms (320,000 clock cycles)
  delay(20);
  
  digitalWrite(13, LOW);
  delay(20);
}
