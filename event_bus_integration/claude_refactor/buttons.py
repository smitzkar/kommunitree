
# ==========================
# buttons.py
# ==========================
"""
buttons.py - gpio button handling
manages all button interactions
"""

import threading
import random
import logging

from config import config
from events import ButtonPressEvent
from event_bus import EventBus

#MARK: ButtonMonitor
class ButtonMonitor(threading.Thread):
    """
    monitors gpio buttons for presses
    uses interrupts on real hardware
    """
    def __init__(self, bus: EventBus):
        super().__init__(daemon=True)
        self.bus = bus
        self.running = True
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # setup gpio if not simulating
        if not config.simulate_hardware:
            self._setup_gpio()
    
    def _setup_gpio(self):
        """configure gpio pins for buttons"""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            
            for button_name, pin in config.button_pins.items():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(
                    pin, 
                    GPIO.FALLING,
                    callback=lambda p, name=button_name: self._button_callback(name),
                    bouncetime=200  # debounce 200ms
                )
            
            self.logger.info("gpio buttons configured")
        except ImportError:
            self.logger.warning("RPi.GPIO not available, using simulation mode")
            config.simulate_hardware = True
    
    def _button_callback(self, button_name: str):
        """called when button pressed (from gpio interrupt)"""
        self.logger.info(f"button pressed: {button_name}")
        self.bus.publish(ButtonPressEvent(button_name))
    
    def run(self):
        """main thread loop"""
        self.logger.info("button monitor started")
        
        if config.simulate_hardware:
            # simulation mode - randomly press buttons
            while self.running:
                threading.Event().wait(10)
                
                # occasionally simulate a button press
                if random.random() > 0.95:
                    button = random.choice(list(config.button_pins.keys()))
                    self._button_callback(button)
        else:
            # real hardware - just keep thread alive
            while self.running:
                threading.Event().wait(1)
    
    def stop(self):
        """cleanup gpio and stop thread"""
        self.running = False
        
        if not config.simulate_hardware:
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup()
            except:
                pass
        
        self.logger.info("button monitor stopped")
