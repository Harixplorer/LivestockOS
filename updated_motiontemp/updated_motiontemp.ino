#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>

#define ONE_WIRE_PIN 4
#define MPU_ADDR     0x68
#define ACCEL_XOUT_H 0x3B
#define PWR_MGMT_1   0x6B
#define SAMPLE_COUNT 50
#define SAMPLE_DELAY_MS 20

OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature tempSensor(&oneWire);

struct RawAccel { int16_t x, y, z; };

RawAccel readAccelRaw() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(ACCEL_XOUT_H);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 6, true);
  RawAccel a;
  a.x = (Wire.read() << 8) | Wire.read();
  a.y = (Wire.read() << 8) | Wire.read();
  a.z = (Wire.read() << 8) | Wire.read();
  return a;
}

const char* classifyBehaviour(float var, float zcr) {
  if (var > 0.05f && zcr > 6.0f)                                    return "WALKING";
  if (var < 0.001f)                                                  return "RESTING";
  if (var >= 0.002f && var <= 0.02f && zcr >= 1.0f && zcr <= 4.0f) return "RUMINATING";
  if (var >= 0.001f && var < 0.002f)                                 return "IDLE";
  return "ANOMALY";
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("=== LivestockOS Combined Sensor Test ===");

  // DS18B20 init
  tempSensor.begin();
  int count = tempSensor.getDeviceCount();
  Serial.printf("DS18B20: %d device(s) found on GPIO %d\n", count, ONE_WIRE_PIN);
  if (count == 0) Serial.println("  ERROR — check wiring and 4.7k pull-up resistor");

  // MPU-6050 init
  Wire.begin(21, 22);
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(PWR_MGMT_1);
  Wire.write(0x00); // wake from sleep
  Wire.endTransmission(true);
  delay(100);

  // WHO_AM_I check
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x75);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 1, true);
  uint8_t who = Wire.read();
  Serial.printf("MPU-6050: WHO_AM_I = 0x%02X %s\n", who, who == 0x68 ? "OK" : "ERROR — check wiring");

  Serial.println("Starting readings...\n");
}

void loop() {
  Serial.println("========================================");

  // ── DS18B20 ──────────────────────────────────────
  tempSensor.requestTemperatures();
  delay(750);
  float t = tempSensor.getTempCByIndex(0);

  if (t == DEVICE_DISCONNECTED_C) {
    Serial.println("DS18B20 : DISCONNECTED");
  } else {
    Serial.printf("Temp    : %.2f C  →  ", t);
    if      (t > 40.5f) Serial.println("CRITICAL fever");
    else if (t > 39.5f) Serial.println("FEVER — monitor");
    else                Serial.println("Normal");
  }

  // ── MPU-6050 window ───────────────────────────────
  float mags[SAMPLE_COUNT];
  float sumX = 0, sumY = 0, sumZ = 0;

  for (int i = 0; i < SAMPLE_COUNT; i++) {
    RawAccel r = readAccelRaw();
    float ax = r.x / 16384.0f;
    float ay = r.y / 16384.0f;
    float az = r.z / 16384.0f;
    mags[i] = sqrt(ax*ax + ay*ay + az*az);
    sumX += ax; sumY += ay; sumZ += az;
    delay(SAMPLE_DELAY_MS);
  }

  // variance
  float mean = 0;
  for (int i = 0; i < SAMPLE_COUNT; i++) mean += mags[i];
  mean /= SAMPLE_COUNT;
  float var = 0;
  for (int i = 0; i < SAMPLE_COUNT; i++) { float d = mags[i]-mean; var += d*d; }
  var /= SAMPLE_COUNT;

  // zero crossing rate
  int crossings = 0;
  for (int i = 1; i < SAMPLE_COUNT; i++)
    if ((mags[i-1]-mean) * (mags[i]-mean) < 0) crossings++;
  float zcr = crossings / ((SAMPLE_COUNT * SAMPLE_DELAY_MS) / 1000.0f);

  // activity score
  float mx = sumX/SAMPLE_COUNT, my = sumY/SAMPLE_COUNT, mz = sumZ/SAMPLE_COUNT;
  int act = (int)constrain((sqrt(mx*mx + my*my + mz*mz) / 2.0f) * 100.0f, 0, 100);

  Serial.printf("Activity: %d / 100\n", act);
  Serial.printf("Behaviour: %s\n", classifyBehaviour(var, zcr));
  Serial.printf("Variance: %.5f g²  |  ZCR: %.2f /sec\n", var, zcr);

  if      (act < 10) Serial.println("Activity: CRITICAL — barely moving");
  else if (act < 20) Serial.println("Activity: LOW — possible illness");
  else               Serial.println("Activity: Normal");

  Serial.println();
  delay(3000);
}