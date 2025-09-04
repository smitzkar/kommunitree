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
        
        while self.running:
            try:
                # Simulate presence detection
                # Real implementation: read from UART/I2C
                new_presence = random.random() > 0.9 # basically changes 10% of the time
                
                # Only publish on state change to avoid event spam
                if new_presence != self.presence:
                    self.presence = new_presence
                    if self.presence:
                        self.bus.publish(PresenceDetectedEvent())
                    else:
                        self.bus.publish(PresenceLostEvent())
                
                threading.Event().wait(config.presence_check_interval)  
                
            except Exception as e:
                self.logger.error(f"Error reading mmWave sensor: {e}")
