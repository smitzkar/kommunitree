"""
2025-09-05 
once again, fallen into the complexity hole  
once again, overwhelmed  
once again, starting from scratch  

testing this guy's implementation: https://python.plainenglish.io/simple-yet-powerful-building-an-in-memory-async-event-bus-in-python-f87e3d505bdd


"""

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List
from dataclasses import dataclass

@dataclass
class Event:
    event_type: str
    
class SimpleEventBus:
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
        
    def publish(self, event: Event) -> None:
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                # Fire-and-forget execution
                self._executor.submit(handler, event) # This is the key!
                
    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)