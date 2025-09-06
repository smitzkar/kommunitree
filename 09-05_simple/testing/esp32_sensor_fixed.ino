// ESP32 Sensor Node - Fixed for BME280 only setup
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_BME280.h>
#include <Adafruit_Sensor.h>

// Hardware Setup  
#define LED_PIN 2  // Built-in LED (most ESP32 boards)
#define MOTION_PIN 4
#define BATTERY_PIN A0
#define SDA_PIN 21  // ESP32 default SDA
#define SCL_PIN 22  // ESP32 default SCL

Adafruit_BME280 bme; // I2C BME280 sensor
unsigned long lastSensorRead = 0;
unsigned long sensorInterval = 5000;  // 5 seconds
bool ledState = false;
bool bmeConnected = false;
bool batteryConnected = false;  // Set to false since no battery sensor

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
  
  // Turn off LED initially
  digitalWrite(LED_PIN, LOW);
  
  // Send initial status
  Serial.println("{\"type\": \"status\", \"message\": \"System ready\"}");
}

void loop() {
  // Check for commands from Pi
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();  // Remove any whitespace
    if (command.length() > 0) {
      handleCommand(command);
    }
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
  DeserializationError error = deserializeJson(doc, command);
  
  if (error) {
    Serial.println("{\"type\": \"error\", \"message\": \"Invalid JSON command\"}");
    return;
  }
  
  String type = doc["type"];
  
  if (type == "led") {
    String state = doc["state"];
    if (state == "on") {
      ledState = true;
      digitalWrite(LED_PIN, HIGH);
      Serial.println("{\"type\": \"ack\", \"message\": \"LED on\", \"led_state\": true}");
    } else if (state == "off") {
      ledState = false;
      digitalWrite(LED_PIN, LOW);
      Serial.println("{\"type\": \"ack\", \"message\": \"LED off\", \"led_state\": false}");
    }
  }
  else if (type == "config") {
    if (doc.containsKey("sleep_interval")) {
      sensorInterval = doc["sleep_interval"].as<int>() * 1000;
      Serial.println("{\"type\": \"ack\", \"message\": \"Config updated\"}");
    }
  }
  else if (type == "reset") {
    ESP.restart();
  }
  else if (type == "status") {
    // Send immediate status update
    sendSensorData();
  }
  else {
    Serial.println("{\"type\": \"error\", \"message\": \"Unknown command type\"}");
  }
}

void sendSensorData() {
  float temp, humidity, pressure;
  bool motion = digitalRead(MOTION_PIN);
  float battery = batteryConnected ? analogRead(BATTERY_PIN) * (3.3 / 4095.0) * 2 : 0; // Only read if connected
  
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
  doc["battery_connected"] = batteryConnected;
  doc["led_state"] = ledState;
  
  String output;
  serializeJson(doc, output);
  Serial.println(output);
  
  // Only send alerts for connected sensors
  if (batteryConnected && battery < 3.3) {
    Serial.println("{\"type\": \"alert\", \"message\": \"Low battery\"}");
  }
  if (temp > 35) {
    Serial.println("{\"type\": \"alert\", \"message\": \"High temperature\"}");
  }
  if (pressure < 980 || pressure > 1050) {
    Serial.println("{\"type\": \"alert\", \"message\": \"Unusual pressure reading\"}");
  }
}
