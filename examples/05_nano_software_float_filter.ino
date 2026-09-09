// ARIS Benchmark Example 05: Nano Software Float Math Filter
// Target: Arduino Nano / Uno (8-bit ALU without FPU)

float raw_sensor = 0.0;
float filtered_voltage = 0.0;
float alpha = 0.15;

void setup() {
  Serial.begin(115200);
}

void loop() {
  raw_sensor = analogRead(A0);
  // Software float emulation costs 200+ cycles per operation
  float voltage = raw_sensor * (5.0 / 1023.0);
  filtered_voltage = (alpha * voltage) + ((1.0 - alpha) * filtered_voltage);
  
  Serial.print("Filtered Voltage: ");
  Serial.println(filtered_voltage);
  delay(10);
}
