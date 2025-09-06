#!/usr/bin/env python3
"""
ESP32 I2C Debug Tool
Helps diagnose BME280 connection issues
"""

import serial
import time
import json

def monitor_esp32(port="/dev/ttyUSB0", duration=10):
    """Monitor ESP32 output and send test commands"""
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        print(f"🔍 Connected to ESP32 on {port}")
        print(f"📡 Monitoring for {duration} seconds...")
        print("=" * 50)
        
        # Send a status request
        print("📤 Requesting status...")
        ser.write(b'{"type": "status"}\n')
        
        start_time = time.time()
        messages_received = 0
        bme_status = None
        
        while time.time() - start_time < duration:
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                if line:
                    messages_received += 1
                    print(f"📥 [{messages_received:2d}] {line}")
                    
                    # Try to parse JSON and extract BME status
                    try:
                        data = json.loads(line)
                        if data.get("type") == "status":
                            print(f"🔧 Status message: {data.get('message', 'Unknown')}")
                        elif data.get("type") == "sensor":
                            bme_connected = data.get("bme_connected", False)
                            if bme_status != bme_connected:
                                bme_status = bme_connected
                                status_text = "✅ CONNECTED" if bme_connected else "❌ NOT DETECTED"
                                print(f"🌡️  BME280 Status: {status_text}")
                    except json.JSONDecodeError:
                        print(f"📝 Non-JSON message: {line}")
            
            time.sleep(0.1)
        
        print("=" * 50)
        print(f"📊 Summary: Received {messages_received} messages")
        if bme_status is not None:
            if bme_status:
                print("✅ BME280 sensor is connected and working!")
            else:
                print("❌ BME280 sensor not detected - check I2C wiring:")
                print("   • SDA (data) should go to GPIO 21")
                print("   • SCL (clock) should go to GPIO 22") 
                print("   • VCC to 3.3V")
                print("   • GND to GND")
                print("   • Try swapping SDA and SCL if still not working")
        else:
            print("⚠️  No sensor data received - ESP32 might not be responding")
        
        ser.close()
        
    except serial.SerialException as e:
        print(f"❌ Serial connection error: {e}")
        print("💡 Make sure ESP32 is connected to /dev/ttyUSB0")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🌡️  ESP32 BME280 Debug Tool")
    print("🔧 This will help diagnose I2C connection issues")
    print()
    monitor_esp32()
