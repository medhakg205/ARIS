// ARIS Benchmark Example 04: Mega 2560 Multi-ADC & Multi-UART Round-Robin
// Target: Arduino Mega 2560 (ATmega2560 - 16 ADC channels, 4 UARTs)

void setup() {
  Serial.begin(115200);
  Serial1.begin(9600);
  pinMode(13, OUTPUT);
}

void loop() {
  // Reading 4 analog channels in sequence
  int a0 = analogRead(A0);
  int a1 = analogRead(A1);
  int a2 = analogRead(A2);
  int a3 = analogRead(A3);

  Serial.print("A0="); Serial.print(a0);
  Serial.print(" A1="); Serial.print(a1);
  Serial.print(" A2="); Serial.print(a2);
  Serial.print(" A3="); Serial.println(a3);

  digitalWrite(13, HIGH);
  delay(15);
  digitalWrite(13, LOW);
  delay(15);
}
