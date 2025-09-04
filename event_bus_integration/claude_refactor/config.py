
# ==========================
# config.py
# ==========================
"""
config.py - all configuration in one place
makes it easy to adjust settings without diving into code
"""

from dataclasses import dataclass
from typing import Optional

#MARK: Config
@dataclass
class Config:
    """
    central configuration for the voice assistant
    using dataclass for clean, type-checked config
    """
    # sensor settings
    sensor_interval: int = 60  # seconds between sensor readings
    sensor_csv_file: str = "logs/sensor_data.csv"
    
    # mmwave sensor settings (human presence detection)
    presence_check_interval: int = 1 # seconds
    
    # audio settings  
    speech_timeout: int = 10  # seconds to wait for speech
    followup_delay: int = 5  # seconds before followup response
    
    # conversation settings
    max_silence_count: int = 2  # timeouts before ending conversation
    greeting_message: str = "Hello! I noticed you're here. Would you like to chat?"
    goodbye_message: str = "Goodbye!"
    check_presence_message: str = "Are you still there?"
    
    # gpio pins (for raspberry pi)
    button_pins = {
        'shutdown': 17,
        'stop_start': 27,
        'force_chat': 22
    }
    
    # system settings
    event_history_size: int = 100
    debug_log_file: str = "event_log.jsonl" # uses json lines format (each line is a separate json object for easier parsing)
    
    # simulation mode (for testing without hardware)
    simulate_hardware: bool = True  # set False when you have real sensors

# global config instance - easy to import anywhere
config = Config()