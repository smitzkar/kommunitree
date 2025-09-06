#!/usr/bin/env python3
"""
Simple LED test script for ESP32
"""
import serial
import json
import time

def test_led_control():
    print("🔧 Testing ESP32 LED control...")
    
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        time.sleep(1)  # Let serial connection stabilize
        
        # Test LED ON
        print("\n💡 Testing LED ON...")
        command = {"type": "led", "state": "on"}
        ser.write(f"{json.dumps(command)}\n".encode())
        
        # Wait for response
        for i in range(10):  # Wait up to 1 second
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                if response:
                    print(f"📥 ESP32 response: {response}")
                    break
            time.sleep(0.1)
        
        print("⏳ Waiting 3 seconds (check if LED is on)...")
        time.sleep(3)
        
        # Test LED OFF
        print("\n💡 Testing LED OFF...")
        command = {"type": "led", "state": "off"}
        ser.write(f"{json.dumps(command)}\n".encode())
        
        # Wait for response
        for i in range(10):  # Wait up to 1 second
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                if response:
                    print(f"📥 ESP32 response: {response}")
                    break
            time.sleep(0.1)
        
        print("⏳ Waiting 2 seconds (check if LED is off)...")
        time.sleep(2)
        
        ser.close()
        print("\n✅ LED test completed!")
        
    except Exception as e:
        print(f"❌ LED test failed: {e}")

if __name__ == "__main__":
    test_led_control()
