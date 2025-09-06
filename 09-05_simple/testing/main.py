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
                    try:
                        data = json.loads(line)
                        self.last_data = data
                        print(f"📥 Received from ESP32: {data.get('type', 'unknown')}")
                        return data
                    except json.JSONDecodeError:
                        print(f"📥 ESP32 sent non-JSON: {line}")
                        # Still return the last valid data we had
                        return self.last_data
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
        self.last_sensor_data = None
    
    def get_current_sensor_data(self) -> Optional[Dict[str, Any]]:
        """Get the most recent sensor data from ESP32"""
        # First try to get any available data
        data = self.esp32.get_latest_data()
        if data and data.get("type") == "sensor":
            self.last_sensor_data = data
            return data
        
        # If no recent sensor data, request it
        if not self.last_sensor_data:
            cmd = DeviceCommand("esp32", "status", {})
            self.esp32.send_command(cmd)
            time.sleep(0.2)  # Give ESP32 time to respond
            data = self.esp32.get_latest_data()
            if data and data.get("type") == "sensor":
                self.last_sensor_data = data
                return data
        
        return self.last_sensor_data
    
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
                "What's the humidity?", 
                "What's the pressure?",
                "Turn on the LED",
                "Turn off the LED",
                "Give me a status report",
                "What sensors are connected?"
            ])
        
        return None
    
    def handle_voice_command(self, text: str) -> str:
        """Handle voice command, return response"""
        text_lower = text.lower()
        
        # If this is just the wake word, acknowledge it
        if "hey treebot" in text_lower and len(text_lower.split()) <= 2:
            return "Hello! How can I help you?"
        
        # Get latest sensor data
        sensor_data = self.get_current_sensor_data()
        
        if "temperature" in text_lower:
            if sensor_data and "temp" in sensor_data:
                temp = sensor_data["temp"]
                bme_status = "from BME280 sensor" if sensor_data.get("bme_connected") else "simulated"
                return f"The temperature is {temp:.1f} degrees Celsius ({bme_status})"
            else:
                return "I couldn't get the temperature reading"
        
        elif "motion" in text_lower:
            return "Motion sensor is not currently connected to this system"
        
        elif "led" in text_lower and "on" in text_lower:
            cmd = DeviceCommand("esp32", "led", {"state": "on", "color": "blue"})
            success = self.esp32.send_command(cmd)
            return "LED turned on" if success else "Failed to control LED"
        
        elif "led" in text_lower and "off" in text_lower:
            cmd = DeviceCommand("esp32", "led", {"state": "off"})
            success = self.esp32.send_command(cmd)
            return "LED turned off" if success else "Failed to control LED"
        
        elif "battery" in text_lower:
            return "Battery monitoring is not currently connected to this system"
        
        elif "pressure" in text_lower:
            if sensor_data and "pressure" in sensor_data:
                pressure = sensor_data["pressure"]
                bme_status = "from BME280 sensor" if sensor_data.get("bme_connected") else "simulated"
                return f"Atmospheric pressure is {pressure:.1f} hectopascals ({bme_status})"
            else:
                return "I couldn't check pressure"
        
        elif "humidity" in text_lower:
            if sensor_data and "humidity" in sensor_data:
                humidity = sensor_data["humidity"]
                bme_status = "from BME280 sensor" if sensor_data.get("bme_connected") else "simulated"
                return f"Humidity is {humidity:.1f} percent ({bme_status})"
            else:
                return "I couldn't check humidity"
        
        elif "status" in text_lower or "report" in text_lower:
            if sensor_data:
                temp = sensor_data.get("temp", "unknown")
                humidity = sensor_data.get("humidity", "unknown")
                pressure = sensor_data.get("pressure", "unknown")
                bme_connected = sensor_data.get("bme_connected", False)
                sensor_status = "BME280 connected" if bme_connected else "BME280 not found, using simulated data"
                
                return f"Environmental report: {temp:.1f}°C, {humidity:.1f}% humidity, {pressure:.1f} hPa. {sensor_status}. Motion and battery sensors not connected."
            else:
                return "I couldn't get a status report"
        
        elif "sensor" in text_lower or "connected" in text_lower:
            if sensor_data:
                bme_connected = sensor_data.get("bme_connected", False)
                if bme_connected:
                    return "BME280 environmental sensor is connected and working. Motion and battery sensors are not connected."
                else:
                    return "BME280 sensor not detected. System is using simulated environmental data. Motion and battery sensors are not connected."
            else:
                return "I couldn't check sensor status"
        
        else:
            return "I didn't understand that command. Try asking about temperature, humidity, pressure, LED control, or sensor status."
    
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
            humidity = data.get("humidity", 0)
            pressure = data.get("pressure", 0)
            battery_connected = data.get("battery_connected", False)
            
            # Temperature alerts
            if temp > 35:
                self.voice.speak_response(f"High temperature alert: {temp:.1f} degrees!")
            elif temp < 5:
                self.voice.speak_response(f"Low temperature alert: {temp:.1f} degrees!")
            
            # Humidity alerts
            if humidity > 80:
                self.voice.speak_response(f"High humidity alert: {humidity:.1f} percent!")
            elif humidity < 20:
                self.voice.speak_response(f"Low humidity alert: {humidity:.1f} percent!")
            
            # Pressure alerts (unusual weather patterns)
            if pressure < 980:
                self.voice.speak_response(f"Low pressure alert: {pressure:.1f} hPa - storm incoming!")
            elif pressure > 1050:
                self.voice.speak_response(f"High pressure alert: {pressure:.1f} hPa!")
            
            # Only check battery if it's actually connected
            if battery_connected:
                battery = data.get("battery", 0)
                if battery < 3.3:
                    self.voice.speak_response(f"Low battery alert: {battery:.2f} volts!")
        
        # Handle LED acknowledgments
        elif data and data.get("type") == "ack":
            message = data.get("message", "")
            if "LED" in message:
                print(f"✅ ESP32 confirmed: {message}")
    
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