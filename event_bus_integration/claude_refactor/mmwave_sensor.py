import threading
import random
import logging
from config import config

from event_bus import EventBus, PresenceDetectedEvent, PresenceLostEvent

class MMWaveSensor(threading.Thread):
    """
    Monitors mmWave presence sensor in a separate thread.
    Real implementation would use UART/I2C to communicate with sensor.
    """
    def __init__(self, bus: EventBus):
        super().__init__(daemon=True)
        self.bus = bus
        self.running = True
        self.presence = False
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self):
        """Monitor presence sensor"""
        self.logger.info("MMWave sensor started")
        
        #MARK: simulated
        # just simulates actual sensor readings via random generator
        total_time = 0
        while self.running:
            try:
                if total_time <= 0:
                    # Randomly decide next state and dwell duration
                    new_presence = random.random() > 0.5  # 50% chance to switch
                    if new_presence:
                        total_time = random.randint(5, 15)  # seconds present
                    else:
                        total_time = random.randint(5, 15)  # seconds absent
                    # Only publish on state change
                    if new_presence != self.presence:
                        self.presence = new_presence
                        if self.presence:
                            self.bus.publish(PresenceDetectedEvent())
                        else:
                            self.bus.publish(PresenceLostEvent())
                else:
                    total_time -= config.presence_check_interval
                threading.Event().wait(config.presence_check_interval)
            except Exception as e:
                self.logger.error(f"Error reading mmWave sensor: {e}")
