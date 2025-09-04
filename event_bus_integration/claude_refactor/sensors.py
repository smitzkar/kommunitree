
# ==========================
# sensors.py
# ==========================
"""
sensors.py - all sensor reading logic
hides complexity of gpio/hardware interaction
"""

import threading
import random
import csv
from datetime import datetime
import logging
from typing import Optional

from config import config
from events import SensorDataEvent
from event_bus import EventBus
from state import SensorData

#MARK: SensorReader
class SensorReader(threading.Thread):
    """
    reads environmental sensors periodically
    runs in separate thread to avoid blocking
    """
    def __init__(self, bus: EventBus):
        super().__init__(daemon=True)
        self.bus = bus
        self.running = True
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # prepare csv file
        self._init_csv()
    
    def _init_csv(self):
        """create csv file with headers if needed"""
        try:
            # check if file exists and has headers
            with open(config.sensor_csv_file, 'r') as f:
                pass  # file exists
        except FileNotFoundError:
            # create file with headers
            with open(config.sensor_csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'temperature', 'humidity', 'presence'])
            self.logger.info(f"created sensor csv: {config.sensor_csv_file}")
    
    def run(self):
        """main thread loop"""
        self.logger.info(f"sensor reader started, interval={config.sensor_interval}s")
        
        while self.running:
            try:
                # read sensors
                data = self._read_sensors()
                
                # publish to event bus
                self.bus.publish(SensorDataEvent(data))
                
                # save to csv
                self._save_to_csv(data)
                
            except Exception as e:
                self.logger.error(f"error reading sensors: {e}")
            
            # wait for next reading
            threading.Event().wait(config.sensor_interval)
    
    def _read_sensors(self) -> SensorData:
        """
        read actual sensor values
        this is where gpio/i2c/spi code would go
        """
        if config.simulate_hardware:
            # simulation mode for testing
            return SensorData(
                temperature=20 + random.random() * 10,
                humidity=40 + random.random() * 20,
                timestamp=datetime.now(),
                presence_detected=random.random() > 0.8
            )
        else:
            # real hardware reading would go here
            # import RPi.GPIO as GPIO
            # import adafruit_dht
            # etc...
            pass
    
    def _save_to_csv(self, data: SensorData):
        """save reading to csv file"""
        try:
            with open(config.sensor_csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    data.timestamp.isoformat(),
                    round(data.temperature, 2),
                    round(data.humidity, 2),
                    data.presence_detected
                ])
        except Exception as e:
            self.logger.error(f"failed to save to csv: {e}")
    
    def stop(self):
        """stop the sensor thread gracefully"""
        self.running = False
        self.logger.info("sensor reader stopping")

    # simple public interface
    def get_latest_reading(self) -> Optional[SensorData]:
        """
        get the most recent sensor reading
        returns None if no reading available yet
        """
        # would query internal buffer
        # for now, just generate one
        if config.simulate_hardware:
            return self._read_sensors()
        return None
