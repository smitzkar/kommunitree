
# ==========================
# events.py (expanding your event_bus.py)
# ==========================
"""
events.py - all event definitions in one place
separated from event_bus.py for clarity
"""

from datetime import datetime
from typing import Any

#MARK: Event
class Event:
    """base event class - all events inherit from this"""
    def __init__(self, data: Any = None):
        self.timestamp = datetime.now()
        self.data = data
        self.event_type = self.__class__.__name__
    
    def __repr__(self):
        return f"{self.event_type}(data={self.data}, time={self.timestamp})"

# hardware events
class SensorDataEvent(Event):
    """new sensor reading available"""
    pass

class PresenceDetectedEvent(Event):
    """person entered detection range"""
    pass

class PresenceLostEvent(Event):
    """person left detection range"""
    pass

class ButtonPressEvent(Event):
    """gpio button was pressed"""
    pass

# conversation events
class ConversationStartEvent(Event):
    """start a new conversation"""
    pass

class ConversationEndEvent(Event):
    """conversation has ended"""
    pass

class UserSpeechEvent(Event):
    """user said something"""
    pass

class AssistantSpeechEvent(Event):
    """assistant wants to speak"""
    pass

# system events
class SystemStateChangeEvent(Event):
    """system state changed"""
    pass

class ShutdownRequestEvent(Event):
    """shutdown the system"""
    pass
