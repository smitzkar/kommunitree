// Minimal ESP32 I2C Scanner + BME280 Test
// Upload this to test I2C connection

#include <Wire.h>
#include <Adafruit_BME280.h>

#define SDA_PIN 21
#define SCL_PIN 22

Adafruit_BME280 bme;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("🔍 ESP32 I2C Scanner + BME280 Test");
  Serial.println("==================================");
  
  // Initialize I2C
  Wire.begin(SDA_PIN, SCL_PIN);
  
  // Scan for I2C devices
  Serial.println("📡 Scanning I2C bus...");
  int devices = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("✅ I2C device found at 0x%02X\n", addr);
      devices++;
    }
  }
  
  if (devices == 0) {
    Serial.println("❌ No I2C devices found! Check wiring:");
    Serial.println("   SDA → GPIO 21");
    Serial.println("   SCL → GPIO 22");
    Serial.println("   VCC → 3.3V");
    Serial.println("   GND → GND");
  } else {
    Serial.printf("📊 Found %d I2C device(s)\n", devices);
  }
  
  Serial.println();
  
  // Test BME280
  Serial.println("🌡️  Testing BME280...");
  if (bme.begin(0x76)) {
    Serial.println("✅ BME280 initialized at address 0x76");
  } else if (bme.begin(0x77)) {
    Serial.println("✅ BME280 initialized at address 0x77");
  } else {
    Serial.println("❌ BME280 initialization failed!");
    Serial.println("💡 Try swapping SDA and SCL wires");
  }
  
  Serial.println("==================================");
}

void loop() {
  // Test BME280 reading
  float temp = bme.readTemperature();
  float humidity = bme.readHumidity();
  float pressure = bme.readPressure() / 100.0F;
  
  if (!isnan(temp)) {
    Serial.printf("📊 Temp: %.1f°C, Humidity: %.1f%%, Pressure: %.1fhPa\n", 
                  temp, humidity, pressure);
  } else {
    Serial.println("❌ Failed to read BME280 data");
  }
  
  delay(2000);
}
