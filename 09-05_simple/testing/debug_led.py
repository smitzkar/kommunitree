#!/usr/bin/env python3
"""
Debug LED commands sent to ESP32
"""
import serial
import json
import time

def debug_led_commands():
    print("🔍 Debugging LED commands...")
    
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        time.sleep(1)
        
        # Test different command formats
        commands = [
            {"type": "led", "state": "on"},
            {"type": "led", "state": "off"},
            '{"type": "led", "state": "on"}',  # Send as string directly
        ]
        
        for i, cmd in enumerate(commands):
            print(f"\n🧪 Test {i+1}: Sending command: {cmd}")
            
            if isinstance(cmd, str):
                ser.write(f"{cmd}\n".encode())
            else:
                json_str = json.dumps(cmd)
                print(f"   JSON string: {json_str}")
                ser.write(f"{json_str}\n".encode())
            
            # Wait for response
            time.sleep(0.5)
            responses = []
            while ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                if response:
                    responses.append(response)
            
            if responses:
                for resp in responses:
                    print(f"📥 Response: {resp}")
            else:
                print("📭 No response received")
            
            time.sleep(1)
        
        ser.close()
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    debug_led_commands()
