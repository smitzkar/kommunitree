# 📁 Simple File Structure (Minimal but Organized)

"""
treebot_simple/
├── main.py              # Pi main program - the only file you run
├── devices.py           # Device abstractions (Pi + ESP32)
├── voice.py             # Voice assistant logic
└── esp32/
    └── sensor_node.ino  # ESP32 Arduino code
"""

# 🧱 Core Abstractions - Black Box Design

from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
import json
import serial
import time
from abc import ABC, abstractmethod

@dataclass
class SensorReading:
    """Simple sensor data container"""
    temperature: float
    humidity: float
    motion: bool
    battery: float
    timestamp: float

@dataclass
class DeviceCommand:
    """Simple command container"""
    target: str  # "esp32" or "pi"
    action: str  # "led", "config", "reset", etc.
    data: Dict[str, Any]

class Device(ABC):
    """Abstract device - every device looks the same from outside"""
    
    @abstractmethod
    def send_command(self, command: DeviceCommand) -> bool:
        """Send command to device, return success"""
        pass
    
    @abstractmethod
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Get latest data from device"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if device is responding"""
        pass

class ESP32Device(Device):
    """ESP32 connected via serial - black box interface"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 115200):
        self.port = port
        self.baud = baud
        self.serial_conn = None
        self.last_data = None
        self.connect()
    
    def connect(self):
        """Establish serial connection"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baud, timeout=1)
            print(f"📱 ESP32 connected on {self.port}")
            return True
        except Exception as e:
            print(f"❌ ESP32 connection failed: {e}")
            return False
    
    def send_command(self, command: DeviceCommand) -> bool:
        """Send JSON command to ESP32"""
        if not self.serial_conn:
            return False
        
        try:
            cmd_json = json.dumps({
                "type": command.action,
                **command.data
            })
            self.serial_conn.write(f"{cmd_json}\n".encode())
            print(f"📤 Sent to ESP32: {command.action}")
            return True
        except Exception as e:
            print(f"❌ ESP32 command failed: {e}")
            return False
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Read latest data from ESP32"""
        if not self.serial_conn:
            return None
        
        try:
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode().strip()
                if line:
                    data = json.loads(line)
                    self.last_data = data
                    print(f"📥 Received from ESP32: {data.get('type', 'unknown')}")
                    return data
        except Exception as e:
            print(f"❌ ESP32 read error: {e}")
        
        return self.last_data
    
    def is_connected(self) -> bool:
        """Check ESP32 connection"""
        return self.serial_conn and self.serial_conn.is_open

class VoiceAssistant:
    """Voice assistant - black box interface"""
    
    def __init__(self, esp32: ESP32Device):
        self.esp32 = esp32
        self.wake_word_detected = False
        self.conversation_active = False
    
    def process_audio_input(self, audio_data: bytes) -> Optional[str]:
        """Process audio, return text if speech detected"""
        # Simulate voice processing
        import random
        
        if random.random() < 0.3:  # 30% chance of wake word (increased for demo)
            self.wake_word_detected = True
            return "Hey TreeBot"
        
        if self.wake_word_detected and random.random() < 0.8:  # 80% chance of command (increased for demo)
            self.wake_word_detected = False
            return random.choice([
                "What's the temperature?",
                "Is there motion detected?",
                "Turn on the LED",
                "What's the battery level?"
            ])
        
        return None
    
    def handle_voice_command(self, text: str) -> str:
        """Handle voice command, return response"""
        text_lower = text.lower()
        
        # Get latest sensor data
        sensor_data = self.esp32.get_latest_data()
        
        if "temperature" in text_lower:
            if sensor_data and "temp" in sensor_data:
                temp = sensor_data["temp"]
                return f"The temperature is {temp} degrees Celsius"
            else:
                return "I couldn't get the temperature reading"
        
        elif "motion" in text_lower:
            if sensor_data and "motion" in sensor_data:
                motion = sensor_data["motion"]
                return "Motion is detected" if motion else "No motion detected"
            else:
                return "I couldn't check motion status"
        
        elif "led" in text_lower and "on" in text_lower:
            cmd = DeviceCommand("esp32", "led", {"state": "on", "color": "blue"})
            success = self.esp32.send_command(cmd)
            return "LED turned on" if success else "Failed to control LED"
        
        elif "battery" in text_lower:
            if sensor_data and "battery" in sensor_data:
                battery = sensor_data["battery"]
                return f"Battery level is {battery} volts"
            else:
                return "I couldn't check battery level"
        
        else:
            return "I didn't understand that command"
    
    def speak_response(self, text: str):
        """Convert text to speech"""
        print(f"🗣️ TreeBot: {text}")
        # In real implementation: TTS synthesis

class TreeBotMain:
    """Main application - orchestrates everything"""
    
    def __init__(self):
        self.esp32 = ESP32Device()
        self.voice = VoiceAssistant(self.esp32)
        self.running = True
    
    def run(self):
        """Main application loop - simple and clear"""
        print("🌳 TreeBot Simple starting...")
        
        if not self.esp32.is_connected():
            print("❌ ESP32 not connected, running in demo mode")
        
        while self.running:
            try:
                # 1. Check for sensor data from ESP32
                self.check_sensor_updates()
                
                # 2. Process audio input
                self.process_voice_input()
                
                # 3. Handle any alerts
                self.check_alerts()
                
                time.sleep(0.1)  # 100ms main loop
                
            except KeyboardInterrupt:
                print("\n🛑 TreeBot stopping...")
                self.running = False
            except Exception as e:
                print(f"❌ Main loop error: {e}")
    
    def check_sensor_updates(self):
        """Check for new sensor data"""
        data = self.esp32.get_latest_data()
        if data and data.get("type") == "sensor":
            # Log or process sensor data
            temp = data.get("temp", 0)
            if temp > 35:  # Hot temperature alert
                self.voice.speak_response(f"Temperature alert: {temp} degrees!")
    
    def process_voice_input(self):
        """Simulate audio input processing"""
        # Simulate audio capture
        import random
        if random.random() < 0.3:  # 30% chance of voice input (increased for demo)
            fake_audio = b"audio_data"
            text = self.voice.process_audio_input(fake_audio)
            
            if text:
                print(f"👂 Heard: {text}")
                response = self.voice.handle_voice_command(text)
                self.voice.speak_response(response)
    
    def check_alerts(self):
        """Check for system alerts"""
        data = self.esp32.get_latest_data()
        if data and data.get("type") == "alert":
            message = data.get("message", "Unknown alert")
            self.voice.speak_response(f"Alert: {message}")

# 🚀 Simple Demo Function
def run_treebot_simple():
    """Run the simple TreeBot system"""
    treebot = TreeBotMain()
    treebot.run()

print("🏗️ TreeBot Simple architecture defined!")
print("Run with: run_treebot_simple()")
print()
print("🎯 Key Design Principles:")
print("• Black box abstraction - simple interfaces")
print("• Minimal files - everything you need in 3 Python files")
print("• Serial communication - just plug ESP32 into Pi")
print("• JSON messages - human readable, easy to debug")
print("• One main loop - easy to understand and modify")


def main():
    run_treebot_simple()
    

if __name__ == "__main__":
    main()