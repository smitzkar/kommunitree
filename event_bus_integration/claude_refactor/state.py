
# ==========================
# state.py
# ==========================
"""
state.py - global state management
provides clean interface to system state
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from events import *
from event_bus import EventBus

#MARK: SystemState
class SystemState(Enum):
    """possible system states"""
    IDLE = "idle"
    LISTENING = "listening"
    SPEAKING = "speaking"
    PROCESSING = "processing"
    CONVERSATION_ACTIVE = "conversation_active"
    SHUTTING_DOWN = "shutting_down"

#MARK: SensorData
@dataclass
class SensorData:
    """container for sensor readings"""
    temperature: float
    humidity: float
    timestamp: datetime
    presence_detected: bool = False

#MARK: StateManager
class StateManager:
    """
    manages global state and notifies about changes
    single source of truth for system state
    """
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.state = SystemState.IDLE
        self.sensor_data: Optional[SensorData] = None
        self.conversation_active = False
        self.presence_detected = False
        self.metrics: Dict[str, Any] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # subscribe to events that affect state
        bus.subscribe(SensorDataEvent, self.handle_sensor_data)
        bus.subscribe(PresenceDetectedEvent, self.handle_presence_detected)
        bus.subscribe(PresenceLostEvent, self.handle_presence_lost)
        bus.subscribe(ConversationStartEvent, self.handle_conversation_start)
        bus.subscribe(ConversationEndEvent, self.handle_conversation_end)
    
    # simple interface methods - hide complexity
    def get_state(self) -> SystemState:
        """get current system state"""
        return self.state
    
    def get_sensor_data(self) -> Optional[SensorData]:
        """get latest sensor reading"""
        return self.sensor_data
    
    def is_conversation_active(self) -> bool:
        """check if conversation is happening"""
        return self.conversation_active
    
    def is_presence_detected(self) -> bool:
        """check if someone is nearby"""
        return self.presence_detected
    
    # event handlers (internal)
    def handle_sensor_data(self, event: SensorDataEvent):
        """update sensor data from event"""
        self.sensor_data = event.data
        self.metrics['last_sensor_update'] = datetime.now()
        self.logger.debug(f"sensor data updated: {self.sensor_data}")
    
    def handle_presence_detected(self, event: PresenceDetectedEvent):
        """someone arrived"""
        self.presence_detected = True
        self.change_state(SystemState.IDLE)
        self.logger.info("presence detected")
    
    def handle_presence_lost(self, event: PresenceLostEvent):
        """someone left"""
        self.presence_detected = False
        if self.conversation_active:
            self.bus.publish(ConversationEndEvent())
        self.logger.info("presence lost")
    
    def handle_conversation_start(self, event: ConversationStartEvent):
        """conversation starting"""
        self.conversation_active = True
        self.change_state(SystemState.CONVERSATION_ACTIVE)
    
    def handle_conversation_end(self, event: ConversationEndEvent):
        """conversation ending"""
        self.conversation_active = False
        self.change_state(SystemState.IDLE)
    
    def change_state(self, new_state: SystemState):
        """change state and notify subscribers"""
        old_state = self.state
        self.state = new_state
        self.bus.publish(SystemStateChangeEvent({
            'old': old_state,
            'new': new_state
        }))
        self.logger.info(f"state changed: {old_state} -> {new_state}")