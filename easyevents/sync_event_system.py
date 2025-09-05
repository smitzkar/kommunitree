"""
Easy Event System - Synchronous Interface

This module provides a simple way to add event-driven patterns to your synchronous Python code.
No asyncio knowledge required! Just register functions and publish events.

Quick Start:
    from sync_event_system import EasyEvents, shared_state
    
    events = EasyEvents()
    
    @events.on('user_login')
    def handle_login(username):
        print(f"Welcome {username}!")
    
    events.publish('user_login', 'Alice')
    events.run_for(seconds=1)  # Process events for 1 second
"""
#MARK: how it works
# empty placeholders that do nothing (just for the interpreter to be happy)
def some_function(): pass
def events(self):
    def on(): pass
# what goes on behind @events.on('some_function')
original_function = some_function
# Step 1: call method
decorator = events.on('user_login')
# Step 2: apply decorator
result_function = decorator(original_function)  # registers + returns original
# Step 3: function unchanged
some_function = result_function  # still same function (as opposed to how it worked with decorator->wrapper)
# => it registers the function in the eventbus to be called later, but doesn't change the function


# =================================================================================

import asyncio
import threading
import time
import logging
from typing import Callable, Any, Dict, Optional
from collections import deque, defaultdict
from functools import wraps

#MARK: original EventBus
# Import the original EventBus from your code
from collections import deque
import asyncio
import time

class EventBus:
    def __init__(self):
        self._topics: dict[str, set[asyncio.Queue]] = {}
        self._retained: dict[str, deque[tuple[str, object, float]]] = {}
        self._retain_limit: int = 10

    async def publish(self, topic: str, data=None, *, retain: bool = False):
        if retain:
            dq = self._retained.setdefault(topic, deque(maxlen=self._retain_limit))
            dq.append((topic, data, time.time()))
        queues = self._topics.get(topic, set()).copy()
        for q in queues:
            await q.put((topic, data))

    async def subscribe(self, topic: str, *, replay_retained: bool = True):
        q: asyncio.Queue = asyncio.Queue()
        subs = self._topics.setdefault(topic, set())
        subs.add(q)
        if replay_retained and topic in self._retained:
            for (t, data, _ts) in self._retained[topic]:
                await q.put((t, data))
        try:
            while True:
                yield await q.get()
        finally:
            subs.discard(q)
            if not subs:
                self._topics.pop(topic, None)


class SharedState:
    """
    A simple shared state container that multiple event handlers can access.
    
    Usage:
        state = SharedState()
        state.counter = 0
        
        @events.on('increment')
        def increment():
            state.counter += 1
    """
    def __init__(self):
        self._data = {}
    
    def __getattr__(self, name):
        return self._data.get(name)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value
    
    def __repr__(self):
        return f"SharedState({self._data})"

#MARK: EasyEvents
class EasyEvents:
    """
    A synchronous interface to the event system. No asyncio knowledge needed!
    
    Features:
    - Register synchronous functions as event handlers
    - Publish events from synchronous code  
    - Automatic background processing
    - Shared state management
    - Periodic tasks (timers)
    """
    
    def __init__(self, debug: bool = False):
        self.bus = EventBus()
        self.handlers: Dict[str, list[Callable]] = defaultdict(list)
        self.periodic_tasks: list[tuple[Callable, float]] = []
        self.is_running = False
        self.debug = debug
        self._background_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        if debug:
            logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    
    def on(self, topic: str, *, retain: bool = False):
        """
        Decorator to register a synchronous function as an event handler.
        
        Usage:
            @events.on('user_click')
            def handle_click(x, y):
                print(f"Clicked at {x}, {y}")
                
            @events.on('status_update', retain=True)  # This handler will see retained messages
            def show_status(status):
                print(f"Status: {status}")
        """
        def decorator(func: Callable):
            self.handlers[topic].append((func, retain))
            if self.debug:
                logging.info(f"Registered handler {func.__name__} for topic '{topic}'")
            return func
        return decorator
    
    def every(self, seconds: float):
        """
        Decorator to register a function to run periodically.
        
        Usage:
            @events.every(5.0)  # Run every 5 seconds
            def heartbeat():
                print("System alive")
        """
        def decorator(func: Callable):
            self.periodic_tasks.append((func, seconds))
            if self.debug:
                logging.info(f"Registered periodic task {func.__name__} every {seconds}s")
            return func
        return decorator
    
    def publish(self, topic: str, data=None, *, retain: bool = False):
        """
        Publish an event from synchronous code.
        
        Usage:
            events.publish('user_login', {'username': 'Alice'})
            events.publish('system_status', 'healthy', retain=True)  # This will be retained
        """
        if self._loop and self._loop.is_running():
            # If we're already running, schedule the publish
            future = asyncio.run_coroutine_threadsafe(
                self.bus.publish(topic, data, retain=retain), 
                self._loop
            )
            # Don't wait for it - fire and forget for better performance
        else:
            # If not running yet, we'll need to start the system
            if self.debug:
                logging.info(f"Publishing '{topic}' - will start system if needed")
    
    async def _async_handler_wrapper(self, topic: str, func: Callable, replay_retained: bool):
        """Wraps synchronous handlers to work with async subscribe"""
        async for (_topic, data) in self.bus.subscribe(topic, replay_retained=replay_retained):
            try:
                if data is None:
                    func()
                elif isinstance(data, dict):
                    func(**data)  # Unpack dict as keyword arguments
                elif isinstance(data, (list, tuple)):
                    func(*data)   # Unpack sequence as positional arguments
                else:
                    func(data)    # Pass single argument
            except Exception as e:
                if self.debug:
                    logging.error(f"Error in handler {func.__name__}: {e}")
    
    async def _periodic_wrapper(self, func: Callable, interval: float):
        """Wraps periodic functions to run on schedule"""
        while True:
            try:
                await asyncio.sleep(interval)
                func()
            except Exception as e:
                if self.debug:
                    logging.error(f"Error in periodic task {func.__name__}: {e}")
    
    async def _run_async(self):
        """Internal async main loop"""
        try:
            async with asyncio.TaskGroup() as tg:
                # Start all event handlers
                for topic, handlers_list in self.handlers.items():
                    for func, replay_retained in handlers_list:
                        tg.create_task(self._async_handler_wrapper(topic, func, replay_retained))
                
                # Start all periodic tasks  
                for func, interval in self.periodic_tasks:
                    tg.create_task(self._periodic_wrapper(func, interval))
                
                # Keep running until stopped
                while self.is_running:
                    await asyncio.sleep(0.1)
                    
        except* Exception as excs:
            if self.debug:
                logging.error(f"Exceptions in event system: {excs}")
    
    def run_forever(self):
        """
        Start the event system and run forever (until Ctrl+C).
        
        Usage:
            events = EasyEvents()
            
            @events.on('test')
            def handler():
                print("Got test event!")
                
            events.publish('test')
            events.run_forever()  # Blocks here
        """
        if self.is_running:
            return
            
        self.is_running = True
        try:
            asyncio.run(self._run_async())
        except KeyboardInterrupt:
            print("\nStopping event system...")
        finally:
            self.is_running = False
    
    def run_for(self, seconds: float):
        """
        Start the event system for a specific duration.
        
        Usage:
            events.publish('some_event', 'data')
            events.run_for(seconds=2)  # Process events for 2 seconds
        """
        if self.is_running:
            return
            
        async def timed_run():
            self.is_running = True
            
            # Get the current loop to enable publish() to work
            self._loop = asyncio.get_event_loop()
            
            # Start the event system
            run_task = asyncio.create_task(self._run_async())
            
            # Wait for the specified time
            await asyncio.sleep(seconds)
            
            # Stop the system
            self.is_running = False
            await asyncio.sleep(0.2)  # Give tasks time to finish
            run_task.cancel()
            try:
                await run_task
            except asyncio.CancelledError:
                pass
        
        asyncio.run(timed_run())
    
    def run_in_background(self):
        """
        Start the event system in a background thread.
        Returns a function to call when you want to stop it.
        
        Usage:
            stop_func = events.run_in_background()
            # ... do other work ...
            stop_func()  # Stop the event system
        """
        if self.is_running:
            return lambda: None
            
        self.is_running = True
        
        def background_worker():
            try:
                asyncio.run(self._run_async())
            except Exception as e:
                if self.debug:
                    logging.error(f"Background event system error: {e}")
        
        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()
        
        def stop():
            self.is_running = False
            thread.join(timeout=2.0)
        
        return stop


# Convenience instance for simple usage
shared_state = SharedState()








# ============================================================================================================================


#MARK: Examples
# Example usage patterns
if __name__ == "__main__":
    # Example 1: Simple notification system
    print("=== Example 1: Simple Events ===")
    
    events = EasyEvents(debug=True)
    
    @events.on('user_action')
    def log_action(action, user):
        print(f"🔔 {user} performed: {action}")
    
    @events.on('user_action')  # Multiple handlers for same event!
    def update_stats(action, user):
        shared_state.total_actions = getattr(shared_state, 'total_actions', 0) + 1
        print(f"📊 Total actions: {shared_state.total_actions}")
    
    # Publish some events
    events.publish('user_action', {'action': 'login', 'user': 'Alice'})
    events.publish('user_action', {'action': 'click_button', 'user': 'Bob'})
    
    # Process events
    events.run_for(seconds=1)
    
    print("\n=== Example 2: Periodic Tasks ===")
    
    events2 = EasyEvents(debug=True)
    
    @events2.every(0.5)  # Every 500ms
    def heartbeat():
        shared_state.heartbeat_count = getattr(shared_state, 'heartbeat_count', 0) + 1
        print(f"💓 Heartbeat #{shared_state.heartbeat_count}")
    
    @events2.on('stop_heartbeat')
    def stop():
        print("❌ Stopping...")
        events2.is_running = False
    
    # Let it run for a bit, then stop it
    threading.Timer(2.5, lambda: events2.publish('stop_heartbeat')).start()
    events2.run_forever()
    
    print("\n=== Example 3: Integration with Existing Code ===")
    
    # Imagine you have existing synchronous code:
    class UserManager:
        def __init__(self):
            self.users = {}
        
        def add_user(self, username):
            self.users[username] = {'login_time': time.time()}
            print(f"👤 Added user: {username}")
        
        def remove_user(self, username):
            if username in self.users:
                del self.users[username]
                print(f"👋 Removed user: {username}")
    
    # Now add events to it easily:
    events3 = EasyEvents()
    user_mgr = UserManager()
    
    @events3.on('user_join')
    def handle_join(username):
        user_mgr.add_user(username)
        # Trigger secondary events
        events3.publish('send_welcome_email', username)
    
    @events3.on('user_leave') 
    def handle_leave(username):
        user_mgr.remove_user(username)
        events3.publish('cleanup_user_data', username)
    
    @events3.on('send_welcome_email')
    def send_email(username):
        print(f"📧 Sending welcome email to {username}")
    
    @events3.on('cleanup_user_data')  
    def cleanup(username):
        print(f"🧹 Cleaning up data for {username}")
    
    # Test the flow
    events3.publish('user_join', 'Charlie')
    events3.publish('user_leave', 'Charlie')
    events3.run_for(seconds=0.5)
    
    print(f"\nFinal user count: {len(user_mgr.users)}")
