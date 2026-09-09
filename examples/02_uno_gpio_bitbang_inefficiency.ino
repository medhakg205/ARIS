// ARIS Benchmark Example 02: High-Frequency GPIO Bit-Banging Inefficiency
// Target: Arduino Uno / Mega / Nano

void setup() {
  pinMode(13, OUTPUT);
}

void loop() {
  // Slow HAL digitalWrite takes 56 clock cycles (3.5 µs) per call
  // Bit-banging a clock signal this way yields max ~140 kHz instead of 8 MHz
  digitalWrite(13, HIGH);
  digitalWrite(13, LOW);
  digitalWrite(13, HIGH);
  digitalWrite(13, LOW);
}
