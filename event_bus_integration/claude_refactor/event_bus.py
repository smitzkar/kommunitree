import asyncio
import threading
import queue
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Union
from datetime import datetime
import logging
from enum import Enum
import weakref
import random
import json
from events import *

import logging

# use module specific logger (needs to be set up in config)
logger = logging.getLogger(__name__)

#MARK:
class EventBus:
    """
    Central event bus for pub-sub communication.
    
    This is the heart of the system - all components communicate through here.
    Using weakref to avoid memory leaks from forgotten subscriptions.
    """
   
    def __init__(self):
        # Dictionary mapping event types to list of callbacks
        # Using weakref.WeakMethod to automatically clean up when objects are deleted
        self._subscribers: Dict[type, List[weakref.ref]] = {}
        
        # For thread-safe operation between async and sync code
        self._event_queue = queue.Queue()
        
        # For async subscribers
        self._async_subscribers: Dict[type, List[Callable]] = {}
        
        # Event history for debugging
        self.event_history: List[Event] = []
        self.max_history = 100
    
    def subscribe(self, event_type: type, callback: Callable):
        logger.debug(f"Subscribing {callback} to {event_type}")
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The Event class to subscribe to
            callback: Function to call when event occurs
        """
        # Determine if callback is async or sync
        if asyncio.iscoroutinefunction(callback):
            # Async callback
            if event_type not in self._async_subscribers:
                self._async_subscribers[event_type] = []
            self._async_subscribers[event_type].append(callback)
            logger.debug(f"Async subscription: {callback.__name__} -> {event_type.__name__}")
        else:
            # Sync callback - use weakref to avoid memory leaks
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
                
            # Use WeakMethod for bound methods (inside classes like system_controller), weakref.ref for functions
            if hasattr(callback, "__self__") and callback.__self__ is not None:
                # Bound method
                weak_callback = weakref.WeakMethod(callback)
            else:
                # Function
                weak_callback = weakref.ref(callback)
            self._subscribers[event_type].append(weak_callback)
            logger.debug(f"Sync subscription: {callback.__name__} -> {event_type.__name__}")
    
    def publish(self, event: Event):
        logger.debug(f"Publishing event: {event} to subscribers of type {type(event)}")
        """
        Publish an event to all subscribers.
        Can be called from both sync and async contexts.
        """
        # Store in history for debugging
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        logger.info(f"Event published: {event}")
        
        # Handle sync subscribers
        event_type = type(event)
        if event_type in self._subscribers:
            logger.debug(f"Found {len(self._subscribers[event_type])} sync subscribers for {event_type}")
            # Clean up dead references and call alive ones
            alive_callbacks = []
            for weak_callback in self._subscribers[event_type]:
                callback = weak_callback()
                logger.debug(f"Checking callback: {callback}")
                if callback is not None:
                    alive_callbacks.append(weak_callback)
                    try:
                        logger.debug(f"Calling sync callback: {callback} for event: {event}")
                        callback(event)
                    except Exception as e:
                        logger.error(f"Error in sync callback: {e}")
            # Update list with only alive callbacks
            self._subscribers[event_type] = alive_callbacks
        
        # Queue event for async processing
        self._event_queue.put(event)
    
    async def async_publish(self, event: Event):
        """
        Async version of publish - ensures async subscribers are called properly.
        """
        self.publish(event)  # Handle sync subscribers first
        
        # Handle async subscribers
        event_type = type(event)
        if event_type in self._async_subscribers:
            # Create tasks for all async callbacks
            tasks = []
            for callback in self._async_subscribers[event_type]:
                tasks.append(asyncio.create_task(callback(event)))
            
            # Wait for all callbacks to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def process_events(self):
        """
        Process queued events in async context.
        This bridges the sync/async worlds.
        """
        while True:
            try:
                # Non-blocking check for events
                if not self._event_queue.empty():
                    event = self._event_queue.get_nowait()
                    
                    # Process async subscribers
                    event_type = type(event)
                    if event_type in self._async_subscribers:
                        for callback in self._async_subscribers[event_type]:
                            try:
                                await callback(event)
                            except Exception as e:
                                logger.error(f"Error in async callback: {e}")
                
                await asyncio.sleep(0.01)  # Small delay to prevent CPU spinning
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error processing events: {e}")
                
