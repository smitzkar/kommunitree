
# ==========================
# debug_monitor.py
# ==========================
"""
debug_monitor.py - debugging and monitoring tools
logs all events and provides visibility into system
"""

import json
import logging
from typing import List

from config import config
from events import *
from event_bus import EventBus

#MARK: DebugMonitor
class DebugMonitor:
    """
    monitors all events for debugging
    can output to file, console, leds, web, etc
    """
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # list of all event types to monitor (currently simply includes everything)
        self.event_types = [
            SensorDataEvent, PresenceDetectedEvent, PresenceLostEvent,
            ButtonPressEvent, ConversationStartEvent, ConversationEndEvent,
            UserSpeechEvent, AssistantSpeechEvent, SystemStateChangeEvent,
            ShutdownRequestEvent, InterruptAudioEvent
        ]
        
        # subscribe to all events
        for event_type in self.event_types:
            bus.subscribe(event_type, self._log_event)
        
        self.logger.info("debug monitor started")
    
    def _log_event(self, event: Event):
        """log event to file in json format"""
        try:
            # create log entry
            entry = {
                'timestamp': event.timestamp.isoformat(),
                'type': event.event_type,
                'data': str(event.data)
            }
            
            # append to json lines file
            with open(config.debug_log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
            
            # could also:
            # - update led indicators
            # - send to web dashboard
            # - update metrics display
            
        except Exception as e:
            self.logger.error(f"failed to log event: {e}")
    
    def get_recent_events(self, count: int = 10) -> List[dict]:
        """
        get recent events from log
        useful for debugging and monitoring
        """
        events = []
        try:
            with open(config.debug_log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-count:]:
                    events.append(json.loads(line))
        except Exception as e:
            self.logger.error(f"failed to read events: {e}")
        
        return events
