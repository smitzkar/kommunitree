# 🔧 ESP32 Arduino Code (sensor_node.ino)

// ESP32 Sensor Node - Simple Serial Communication with BME280
#include "ArduinoJson.h"
#include <Wire.h>
#include <Adafruit_BME280.h>
#include <Adafruit_Sensor.h>

// Hardware Setup
#define LED_PIN 2
#define MOTION_PIN 4
#define BATTERY_PIN A0
#define SDA_PIN 21  // ESP32 default SDA
#define SCL_PIN 22  // ESP32 default SCL

Adafruit_BME280 bme; // I2C BME280 sensor
unsigned long lastSensorRead = 0;
unsigned long sensorInterval = 5000;  // 5 seconds
bool ledState = false;
bool bmeConnected = false;

void setup() {
  Serial.begin(115200);
  
  // Initialize I2C
  Wire.begin(SDA_PIN, SCL_PIN);
  
  // Initialize BME280
  if (bme.begin(0x76)) {  // Try address 0x76 first
    bmeConnected = true;
    Serial.println("{\"type\": \"status\", \"message\": \"ESP32 started with BME280\"}");
  } else if (bme.begin(0x77)) {  // Try address 0x77
    bmeConnected = true;
    Serial.println("{\"type\": \"status\", \"message\": \"ESP32 started with BME280 at 0x77\"}");
  } else {
    bmeConnected = false;
    Serial.println("{\"type\": \"status\", \"message\": \"ESP32 started - BME280 not found\"}");
  }
  
  pinMode(LED_PIN, OUTPUT);
  pinMode(MOTION_PIN, INPUT);
  
  // Send initial status
  Serial.println("{\"type\": \"status\", \"message\": \"System ready\"}");
}

void loop() {
  // Check for commands from Pi
  if (Serial.available()) {
    String command = Serial.readStringUntil('\\n');
    handleCommand(command);
  }
  
  // Send sensor data periodically
  if (millis() - lastSensorRead > sensorInterval) {
    sendSensorData();
    lastSensorRead = millis();
  }
  
  delay(100);
}

void handleCommand(String command) {
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, command);
  
  String type = doc["type"];
  
  if (type == "led") {
    String state = doc["state"];
    ledState = (state == "on");
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
    
    Serial.println("{\"type\": \"ack\", \"message\": \"LED " + state + "\"}");
  }
  else if (type == "config") {
    sensorInterval = doc["sleep_interval"].as<int>() * 1000;
    Serial.println("{\"type\": \"ack\", \"message\": \"Config updated\"}");
  }
  else if (type == "reset") {
    ESP.restart();
  }
  else if (type == "status") {
    // Send immediate status update
    sendSensorData();
  }
}

void sendSensorData() {
  float temp, humidity, pressure;
  bool motion = digitalRead(MOTION_PIN);
  float battery = analogRead(BATTERY_PIN) * (3.3 / 4095.0) * 2; // Voltage divider
  
  // Read BME280 data if connected
  if (bmeConnected) {
    temp = bme.readTemperature();
    humidity = bme.readHumidity();
    pressure = bme.readPressure() / 100.0F; // Convert to hPa
  } else {
    // Provide simulated data if sensor not connected
    temp = 20.0 + random(-5, 15);  // Random temp 15-35°C
    humidity = 50.0 + random(-20, 30);  // Random humidity 30-80%
    pressure = 1013.25 + random(-50, 50);  // Random pressure around sea level
  }
  
  // Create JSON response
  DynamicJsonDocument doc(1024);
  doc["type"] = "sensor";
  doc["temp"] = temp;
  doc["humidity"] = humidity;
  doc["pressure"] = pressure;
  doc["motion"] = motion;
  doc["battery"] = battery;
  doc["timestamp"] = millis();
  doc["bme_connected"] = bmeConnected;
  
  String output;
  serializeJson(doc, output);
  Serial.println(output);
  
  // Check for alerts
  if (battery < 3.3) {
    Serial.println("{\"type\": \"alert\", \"message\": \"Low battery\"}");
  }
  if (temp > 35) {
    Serial.println("{\"type\": \"alert\", \"message\": \"High temperature\"}");
  }
  if (pressure < 980 || pressure > 1050) {
    Serial.println("{\"type\": \"alert\", \"message\": \"Unusual pressure reading\"}");
  }
}