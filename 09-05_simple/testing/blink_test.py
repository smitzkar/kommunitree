#!/usr/bin/env python3
"""
LED blink test - Make it obvious if the LED is working
"""
import serial
import json
import time

def blink_test():
    print("💡 LED Blink Test - Watch for blinking LED!")
    print("   (Look for a small LED on the ESP32 board)")
    
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        time.sleep(1)
        
        print("\n🔄 Starting blink sequence...")
        
        for i in range(10):  # Blink 10 times
            # LED ON
            cmd_on = {"type": "led", "state": "on"}
            ser.write(f"{json.dumps(cmd_on)}\n".encode())
            print(f"💡 Blink {i+1}: LED ON")
            time.sleep(0.5)
            
            # LED OFF  
            cmd_off = {"type": "led", "state": "off"}
            ser.write(f"{json.dumps(cmd_off)}\n".encode())
            print(f"🌑 Blink {i+1}: LED OFF")
            time.sleep(0.5)
            
            # Read any responses (but don't wait for them)
            while ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                if "led_state" in response:
                    data = json.loads(response)
                    state = data.get("led_state", "unknown")
                    print(f"   ✅ ESP32 confirmed: LED = {state}")
        
        # Final OFF
        cmd_off = {"type": "led", "state": "off"}
        ser.write(f"{json.dumps(cmd_off)}\n".encode())
        print("\n🔚 Test complete - LED should be OFF")
        
        ser.close()
        
    except Exception as e:
        print(f"❌ Blink test failed: {e}")

if __name__ == "__main__":
    blink_test()
