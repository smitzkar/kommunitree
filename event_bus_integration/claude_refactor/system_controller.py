
# ==========================
# system_controller.py
# ==========================
"""
system_controller.py - main system coordinator
ties everything together
"""

import asyncio
import subprocess
import logging

from config import config
from events import *
from event_bus import EventBus
from state import StateManager, SystemState
from sensors import SensorReader
from buttons import ButtonMonitor
from mmwave_sensor import MMWaveSensor
from audio_manager import AudioManager
from conversation import ConversationManager

#MARK: SystemController
class SystemController:
    """
    main controller that starts and manages all components
    handles system-level operations
    """
    def __init__(self):
        # create event bus first
        self.bus = EventBus()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # create components
        self.state = StateManager(self.bus)
        self.sensors = SensorReader(self.bus)
        self.buttons = ButtonMonitor(self.bus)
        self.mmwave = MMWaveSensor(self.bus)
        self.audio = AudioManager(self.bus)
        self.conversation = ConversationManager(self.bus, self.audio)
        
        # subscribe to system events
        self.bus.subscribe(ButtonPressEvent, self._handle_button)
        self.bus.subscribe(ShutdownRequestEvent, self._handle_shutdown)
        
        self.running = True
    
    def _handle_button(self, event: ButtonPressEvent):
        """handle button presses"""
        button = event.data
        
        if button == 'shutdown':
            self.bus.publish(ShutdownRequestEvent())
        elif button == 'stop_start':
            self.toggle()
        elif button == 'force_chat':
            self.bus.publish(ConversationStartEvent())
    
    def _handle_shutdown(self, event: ShutdownRequestEvent):
        """shutdown the system"""
        self.logger.info("shutdown requested")
        
        # end conversation gracefully
        self.bus.publish(ConversationEndEvent())
        self.state.change_state(SystemState.SHUTTING_DOWN)
        
        if not config.simulate_hardware:
            # shutdown raspberry pi
            subprocess.run(['sudo', 'shutdown', '-h', 'now'])
        
        self.stop()
    
    def toggle(self):
        """pause/resume the system"""
        self.running = not self.running
        self.logger.info(f"system {'running' if self.running else 'paused'}")
    
    async def run(self):
        """
        main run loop
        starts all components and keeps system running
        """
        # start hardware threads
        self.sensors.start()
        self.buttons.start()
        self.mmwave.start()
        
        self.logger.info("system controller started")
        
        # start event processor
        event_task = asyncio.create_task(self.bus.process_events())
        
        try:
            # main loop
            while self.running:
                await asyncio.sleep(1)
                
                # could add health checks here
                # if self.state.get_state() == SystemState.ERROR:
                #     self.handle_error()
            
        except KeyboardInterrupt:
            self.logger.info("interrupted by user")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """cleanup all components gracefully"""
        self.logger.info("cleaning up...")
        
        # stop hardware threads
        self.sensors.stop()
        self.buttons.stop()
        self.mmwave.running = False
        
        # final state
        self.state.change_state(SystemState.IDLE)
        
        self.logger.info("cleanup complete")
    
    def stop(self):
        """stop the system"""
        self.running = False
