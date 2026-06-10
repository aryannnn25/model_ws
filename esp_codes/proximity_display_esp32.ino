// ============================================================
// ESP32 — PROXIMITY SENSOR + UART DISPLAY OUTPUT
// Outputs: Raw RPM | Filtered RPM | Speed km/h | Accel m/s²
//
// This version sends data to BOTH:
//   1. USB Serial (Serial Monitor / Plotter) — unchanged
//   2. UART2 → Arduino Uno (for TFT LCD display)
//
// UART2 WIRING (ESP32 → Arduino Uno):
//   ESP32 GPIO 17 (TX2) ──→ Arduino Pin 10 (SoftwareSerial RX)
//   ESP32 GND            ──→ Arduino GND
//   *** DO NOT connect ESP32 TX directly to Arduino RX (pin 0) ***
//   *** Use SoftwareSerial on Arduino to keep hardware Serial free ***
//
// PROTOCOL:
//   Start byte: 0xAA
//   4× float32 (little-endian): rawRpm, filteredRpm, speedKmh, accel
//   Checksum: XOR of all 16 data bytes
//   End byte: 0x55
//   Total: 19 bytes per packet
// ============================================================


// ============================================================
// CONFIGURATION — change these to match your setup
// ============================================================

const int     SENSOR_PIN           = 33;     // GPIO pin connected to sensor output
const int     BOLT_COUNT           = 8;      // Number of bolts on the wheel circle
const float   WHEEL_DIAMETER_INCH  = 23.0f;  // Nominal wheel diameter in inches

// Derived constants (auto-calculated — do not edit)
const float   WHEEL_CIRC_M = 3.14159265f * WHEEL_DIAMETER_INCH * 0.0254f;
const float   KMH_PER_RPM  = WHEEL_CIRC_M * 3.6f / 60.0f;


// ============================================================
// UART2 CONFIGURATION (for Arduino display)
// ============================================================

#define UART2_TX_PIN    17      // ESP32 GPIO 17 = UART2 TX
#define UART2_RX_PIN    16      // ESP32 GPIO 16 = UART2 RX (not used but needed for init)
#define UART2_BAUD      115200  // Baud rate for display link

#define PKT_START       0xAA
#define PKT_END         0x55
#define PKT_SIZE        19      // 1 + 16 + 1 + 1 = 19 bytes


// ============================================================
// TIMING & FILTER SETTINGS
// ============================================================

const unsigned long DEBOUNCE_US     = 2000UL;     // 2 ms  — rejects sensor chatter
const unsigned long ZERO_TIMEOUT_US = 2000000UL;  // 2 s   — no pulse → speed = 0
const unsigned long PRINT_EVERY_MS  = 50UL;       // 50 ms → 20 readings per second

const float RPM_ALPHA   = 0.30f;  // EMA for RPM.   0.1=very smooth, 0.9=very raw
const float ACCEL_ALPHA = 0.15f;  // EMA for accel. Lower = smoother (less jitter)

const float MAX_BELIEVABLE_RPM = 6000.0f;  // Reject sensor spikes above this


// ============================================================
// 4-PULSE AVERAGING BUFFER
// ============================================================

#define NUM_AVG 4

volatile unsigned long pIntervals[NUM_AVG] = {0, 0, 0, 0};
volatile int           pIdx               = 0;
volatile int           pCount             = 0;
volatile unsigned long lastPulseTime_us   = 0;
volatile bool          newPulse           = false;


// ============================================================
// OUTPUT VARIABLES
// ============================================================

float rawRpm      = 0.0f;
float filteredRpm = 0.0f;
float speedKmh    = 0.0f;
float speedMs     = 0.0f;

// Acceleration
float prevSpeedMs     = 0.0f;
unsigned long prevSpeedTime_ms = 0;
float rawAccel_ms2    = 0.0f;
float filtAccel_ms2   = 0.0f;

// Print timer
unsigned long lastPrint_ms = 0;


// ============================================================
// FORWARD DECLARATION
// ============================================================
void IRAM_ATTR sensorISR();
void sendDisplayPacket(float rpm_raw, float rpm_filt, float spd_kmh, float accel);


// ============================================================
// SETUP
// ============================================================

void setup() {
  // USB Serial — for Serial Monitor / Plotter
  Serial.begin(115200);
  while (!Serial) delay(10);

  // UART2 — for Arduino TFT display
  Serial2.begin(UART2_BAUD, SERIAL_8N1, UART2_RX_PIN, UART2_TX_PIN);

  pinMode(SENSOR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(SENSOR_PIN), sensorISR, RISING);

  // ---- Startup banner ----
  Serial.println();
  Serial.println("============================================");
  Serial.println("  ESP32 PROXIMITY SENSOR + DISPLAY — READY ");
  Serial.println("============================================");
  Serial.print  ("  Wheel diameter  : "); Serial.print(WHEEL_DIAMETER_INCH, 1); Serial.println(" inch");
  Serial.print  ("  Circumference   : "); Serial.print(WHEEL_CIRC_M, 4);        Serial.println(" m");
  Serial.print  ("  Bolt count      : "); Serial.println(BOLT_COUNT);
  Serial.print  ("  km/h per RPM    : "); Serial.println(KMH_PER_RPM, 4);
  Serial.print  ("  Sensor pin      : GPIO"); Serial.println(SENSOR_PIN);
  Serial.print  ("  Display UART TX : GPIO"); Serial.println(UART2_TX_PIN);
  Serial.print  ("  Display baud    : "); Serial.println(UART2_BAUD);
  Serial.print  ("  Debounce        : "); Serial.print(DEBOUNCE_US / 1000.0f, 1); Serial.println(" ms");
  Serial.print  ("  Print rate      : "); Serial.print(1000UL / PRINT_EVERY_MS); Serial.println(" Hz");
  Serial.println("============================================");
  Serial.println();
  Serial.println("  Rotate the wheel and compare RPM_RAW");
  Serial.println("  with your tachometer reading.");
  Serial.println("============================================");
  Serial.println();

  delay(2000);

  // Print column header (Arduino Serial Plotter reads this as legend)
  Serial.println("RPM_RAW:0 RPM_FILT:0 SPD_kmh:0 ACCEL_ms2:0");
}


// ============================================================
// MAIN LOOP
// ============================================================

void loop() {

  // ---- 1. CALCULATE SPEED FROM SENSOR PULSES ----
  if (newPulse && pCount >= NUM_AVG) {

    noInterrupts();
    unsigned long buf[NUM_AVG];
    for (int i = 0; i < NUM_AVG; i++) buf[i] = pIntervals[i];
    newPulse = false;
    interrupts();

    unsigned long sum = 0;
    bool valid = true;
    for (int i = 0; i < NUM_AVG; i++) {
      if (buf[i] == 0) { valid = false; break; }
      sum += buf[i];
    }

    if (valid) {
      float avgInterval_us = (float)(sum / NUM_AVG);
      float newRawRpm = 60000000.0f / (avgInterval_us * (float)BOLT_COUNT);

      if (newRawRpm > 0.0f && newRawRpm < MAX_BELIEVABLE_RPM) {

        rawRpm      = newRawRpm;
        filteredRpm = (RPM_ALPHA * rawRpm) + ((1.0f - RPM_ALPHA) * filteredRpm);
        speedKmh    = filteredRpm * KMH_PER_RPM;
        speedMs     = speedKmh / 3.6f;

        // ---- 2. ACCELERATION ----
        unsigned long now_ms = millis();
        float dt = (float)(now_ms - prevSpeedTime_ms) / 1000.0f;

        if (prevSpeedTime_ms > 0 && dt > 0.01f && dt < 1.5f) {
          rawAccel_ms2  = (speedMs - prevSpeedMs) / dt;
          filtAccel_ms2 = (ACCEL_ALPHA * rawAccel_ms2) + ((1.0f - ACCEL_ALPHA) * filtAccel_ms2);
        }

        prevSpeedMs      = speedMs;
        prevSpeedTime_ms = now_ms;
      }
    }
  }


  // ---- 3. ZERO-SPEED TIMEOUT ----
  noInterrupts();
  unsigned long lastT = lastPulseTime_us;
  interrupts();

  if ((micros() - lastT) > ZERO_TIMEOUT_US) {
    if (rawRpm > 0.0f || filteredRpm > 0.0f) {
      rawRpm        = 0.0f;
      filteredRpm   = 0.0f;
      speedKmh      = 0.0f;
      speedMs       = 0.0f;
      rawAccel_ms2  = 0.0f;
      filtAccel_ms2 = 0.0f;
      prevSpeedMs   = 0.0f;
      prevSpeedTime_ms = 0;
    }
  }


  // ---- 4. SERIAL OUTPUT (USB + UART2 to display) ----
  if (millis() - lastPrint_ms >= PRINT_EVERY_MS) {
    lastPrint_ms = millis();

    // USB Serial Monitor / Plotter — unchanged
    Serial.print("RPM_RAW:");   Serial.print(rawRpm,        1);
    Serial.print(" RPM_FILT:"); Serial.print(filteredRpm,   1);
    Serial.print(" SPD_kmh:");  Serial.print(speedKmh,      2);
    Serial.print(" ACCEL_ms2:");Serial.println(filtAccel_ms2, 3);

    // UART2 → Arduino Uno → TFT Display
    sendDisplayPacket(rawRpm, filteredRpm, speedKmh, filtAccel_ms2);
  }
}


// ============================================================
// SEND BINARY PACKET TO ARDUINO DISPLAY
// Packet: [0xAA] [float×4 = 16 bytes] [XOR checksum] [0x55]
// Total: 19 bytes @ 115200 baud ≈ 1.65 ms to transmit
// ============================================================

void sendDisplayPacket(float rpm_raw, float rpm_filt, float spd_kmh, float accel) {
  uint8_t pkt[PKT_SIZE];
  pkt[0] = PKT_START;

  // Pack 4 floats as little-endian bytes
  memcpy(&pkt[1],  &rpm_raw,  4);
  memcpy(&pkt[5],  &rpm_filt, 4);
  memcpy(&pkt[9],  &spd_kmh,  4);
  memcpy(&pkt[13], &accel,    4);

  // XOR checksum over the 16 data bytes
  uint8_t checksum = 0;
  for (int i = 1; i <= 16; i++) {
    checksum ^= pkt[i];
  }
  pkt[17] = checksum;
  pkt[18] = PKT_END;

  Serial2.write(pkt, PKT_SIZE);
}


// ============================================================
// INTERRUPT SERVICE ROUTINE
// ============================================================

void IRAM_ATTR sensorISR() {
  unsigned long t  = micros();
  unsigned long dt = t - lastPulseTime_us;

  if (dt < DEBOUNCE_US) return;

  pIntervals[pIdx % NUM_AVG] = dt;
  pIdx++;
  if (pCount < NUM_AVG) pCount++;

  lastPulseTime_us = t;
  newPulse = true;
}
