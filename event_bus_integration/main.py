"""
2025-09-03 followup to claude ai: https://claude.ai/public/artifacts/8f6520d3-57cb-463e-a470-7c22b8052678 


Voice Assistant with Event Bus Architecture
==========================================
This version uses a pub-sub event bus pattern for all component communication.
Benefits: 
- Fully decoupled components (they don't know about each other)
- Easy to add new components without modifying existing ones
- Natural for event-driven systems
- Good for debugging (can log all events in one place)

Drawbacks:
- Slightly more complex to understand initially
- Can be harder to trace data flow
- Potential for event storms if not careful
"""

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

from tree_logger import setup_logging, TreeLogger

#MARK: logging
log = setup_logging()  # Only call once, at the start
tree_logger = TreeLogger()

logger = logging.getLogger(__name__)  # really neat! basically creates a little module specific logger, using the root configs
logger.info("This will go to both console and logs/treebot.log")

## use decorator like this: 
# @tree_logger.time_function("some_test_loop", "LOOP")
# def some_test_loop(i: int = 10) -> None:
#     while i > 0:
#         time.sleep(1)
#         i -= 1




# # Set up logging with more detail
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# ============= EVENT SYSTEM CORE =============
#MARK: class Event, specific events
# removed to own file

# ============= EVENT BUS IMPLEMENTATION =============
#MARK: class EventBus
# removed to own file

from event_bus import EventBus, Event, SensorDataEvent, PresenceDetectedEvent,PresenceLostEvent, ConversationStartEvent, ConversationEndEvent, SystemStateChangeEvent, AssistantSpeechEvent, UserSpeechEvent,ButtonPressEvent, ShutdownRequestEvent

# Global event bus instance - this is our communication backbone
event_bus = EventBus()

# ============= SHARED STATE WITH EVENT NOTIFICATIONS =============

@dataclass
#MARK:
class SensorData:
    """Data class for sensor readings"""
    temperature: float
    humidity: float
    timestamp: datetime
    presence_detected: bool = False

#MARK:
class SystemState(Enum):
    """System states"""
    IDLE = "idle"
    LISTENING = "listening"
    SPEAKING = "speaking"
    PROCESSING = "processing"
    CONVERSATION_ACTIVE = "conversation_active"
    SHUTTING_DOWN = "shutting_down"

#MARK:
class StateManager:
    """
    Manages global state and publishes state changes as events.
    This is the "source of truth" for system state.
    """
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.state = SystemState.IDLE
        self.sensor_data: Optional[SensorData] = None
        self.conversation_active = False
        self.presence_detected = False
        self.metrics: Dict[str, Any] = {}
        
        # Subscribe to relevant events to update state
        bus.subscribe(SensorDataEvent, self.handle_sensor_data)
        bus.subscribe(PresenceDetectedEvent, self.handle_presence_detected)
        bus.subscribe(PresenceLostEvent, self.handle_presence_lost)
        bus.subscribe(ConversationStartEvent, self.handle_conversation_start)
        bus.subscribe(ConversationEndEvent, self.handle_conversation_end)
    
    def handle_sensor_data(self, event: SensorDataEvent):
        """Update sensor data from event"""
        self.sensor_data = event.data
        self.metrics['last_sensor_update'] = datetime.now()
    
    def handle_presence_detected(self, event: PresenceDetectedEvent):
        """Update presence state"""
        self.presence_detected = True
        self.change_state(SystemState.IDLE)
    
    def handle_presence_lost(self, event: PresenceLostEvent):
        """Update presence state"""
        self.presence_detected = False
        if self.conversation_active:
            self.bus.publish(ConversationEndEvent())
    
    def handle_conversation_start(self, event: ConversationStartEvent):
        """Update conversation state"""
        self.conversation_active = True
        self.change_state(SystemState.CONVERSATION_ACTIVE)
    
    def handle_conversation_end(self, event: ConversationEndEvent):
        """Update conversation state"""
        self.conversation_active = False
        self.change_state(SystemState.IDLE)
    
    def change_state(self, new_state: SystemState):
        """Change system state and notify subscribers"""
        old_state = self.state
        self.state = new_state
        self.bus.publish(SystemStateChangeEvent({
            'old': old_state,
            'new': new_state
        }))

# ============= HARDWARE COMPONENTS (THREADING) =============
#MARK: class: SensorReader
class SensorReader(threading.Thread):
    """
    Reads sensors in a separate thread and publishes data via event bus.
    This keeps blocking I/O operations from affecting the main event loop.
    """
    def __init__(self, bus: EventBus, interval: int = 60):
        super().__init__(daemon=True)  # Daemon thread dies when main program exits
        self.bus = bus
        self.interval = interval
        self.running = True
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self):
        """Main thread loop"""
        self.logger.info(f"Sensor reader started, interval={self.interval}s")
        
        while self.running:
            try:
                # Simulate sensor reading (replace with actual GPIO code)
                # In real implementation, this would be:
                # - GPIO.setup() for pins
                # - Read from I2C/SPI sensors
                # - Parse sensor data
                data = SensorData(
                    temperature=20 + random.random() * 10,
                    humidity=40 + random.random() * 20,
                    timestamp=datetime.now(),
                    presence_detected=random.random() > 0.7  # Simulate occasional presence
                )
                
                # Publish to event bus
                self.bus.publish(SensorDataEvent(data))
                
                # Also save to CSV (simplified version)
                self.save_to_csv(data)
                
            except Exception as e:
                self.logger.error(f"Error reading sensors: {e}")
            
            # Wait for next reading
            threading.Event().wait(self.interval)
    
    def save_to_csv(self, data: SensorData):
        """Save sensor data to CSV file"""
        # In production, use proper CSV library and handle file locking
        try:
            with open('sensor_data.csv', 'a') as f:
                f.write(f"{data.timestamp},{data.temperature},{data.humidity}\n")
        except Exception as e:
            self.logger.error(f"Failed to save to CSV: {e}")
    
    def stop(self):
        """Stop the sensor reading thread"""
        self.running = False

#MARK: class ButtonMonitor
class ButtonMonitor(threading.Thread):
    """
    Monitors GPIO buttons and publishes button press events.
    Uses interrupts in real implementation.
    """
    def __init__(self, bus: EventBus):
        super().__init__(daemon=True)
        self.bus = bus
        self.running = True
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Button configuration
        # In real implementation: GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.buttons = {
            'shutdown': 17,     # GPIO pin 17
            'stop_start': 27,   # GPIO pin 27
            'force_chat': 22    # GPIO pin 22
        }
    
    def run(self):
        """Setup GPIO interrupts and wait for events"""
        self.logger.info("Button monitor started")
        
        # In real implementation:
        # for button, pin in self.buttons.items():
        #     GPIO.add_event_detect(pin, GPIO.FALLING, 
        #                          callback=lambda p: self.button_pressed(button),
        #                          bouncetime=200)
        
        # Simulation loop
        while self.running:
            threading.Event().wait(10)  # Check every 10 seconds
            
            # Simulate random button press for testing
            if random.random() > 0.9:
                button = random.choice(list(self.buttons.keys()))
                self.button_pressed(button)
    
    def button_pressed(self, button_type: str):
        """Handle button press interrupt"""
        self.logger.info(f"Button pressed: {button_type}")
        self.bus.publish(ButtonPressEvent(button_type))

#MARK: class MMWAVESensor
# moved to own file 
from mmwave_sensor import MMWaveSensor

# ============= AUDIO COMPONENTS =============
#MARK:
class AudioManager:
    """
    Manages audio input/output using event-driven architecture.
    Bridges between blocking audio operations and async world.
    """
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.is_playing = False
        self.is_listening = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Subscribe to speech events
        bus.subscribe(AssistantSpeechEvent, self.handle_assistant_speech)
        
        # Audio threads for blocking operations
        self.play_thread: Optional[threading.Thread] = None
        self.listen_thread: Optional[threading.Thread] = None
    
    def handle_assistant_speech(self, event: AssistantSpeechEvent):
        """Handle request to speak"""
        if not self.is_playing:
            # Start playback in separate thread to avoid blocking
            self.play_thread = threading.Thread(
                target=self._play_audio,
                args=(event.data,)
            )
            self.play_thread.start()
    
    def _play_audio(self, text: str):
        """Blocking audio playback (runs in thread)"""
        self.is_playing = True
        self.logger.info(f"Playing: {text}")
        
        try:
            # Real implementation would:
            # 1. Call TTS API to get audio
            # 2. Play audio through speaker
            # For now, simulate with sleep
            duration = len(text) * 0.05  # Rough estimate
            threading.Event().wait(duration)
            
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
        finally:
            self.is_playing = False
    
    async def listen_for_speech(self, timeout: int = 10) -> Optional[str]:
        """
        Start listening for speech (async wrapper).
        Returns transcribed text or None if timeout.
        """
        if self.is_listening:
            return None
        
        # Use future to bridge threading and async
        future = asyncio.Future()
        
        def _listen():
            """Blocking listen operation"""
            self.is_listening = True
            self.logger.info("Listening for speech...")
            
            try:
                # Real implementation would:
                # 1. Record audio from microphone
                # 2. Send to speech-to-text API
                # For now, simulate
                threading.Event().wait(2)
                
                # Simulate speech detection
                if random.random() > 0.3:
                    text = "Hello, how are you today?"
                    # Set result in main thread
                    asyncio.run_coroutine_threadsafe(
                        self._set_future_result(future, text),
                        asyncio.get_event_loop()
                    )
                else:
                    asyncio.run_coroutine_threadsafe(
                        self._set_future_result(future, None),
                        asyncio.get_event_loop()
                    )
                    
            except Exception as e:
                self.logger.error(f"Error listening: {e}")
                asyncio.run_coroutine_threadsafe(
                    self._set_future_result(future, None),
                    asyncio.get_event_loop()
                )
            finally:
                self.is_listening = False
        
        # Start listening in thread
        self.listen_thread = threading.Thread(target=_listen)
        self.listen_thread.start()
        
        # Wait for result with timeout
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            if result:
                # Publish user speech event
                self.bus.publish(UserSpeechEvent(result))
            return result
        except asyncio.TimeoutError:
            self.logger.info("Listen timeout")
            return None
    
    async def _set_future_result(self, future: asyncio.Future, result: Any):
        """Helper to set future result from thread"""
        if not future.done():
            future.set_result(result)

# ============= CONVERSATION MANAGEMENT =============
#MARK:
class ConversationManager:
    """
    Manages AI conversation flow using event-driven patterns.
    Handles the complex conversation logic and state.
    """
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.active = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Response management
        self.immediate_response: Optional[str] = None
        self.followup_response: Optional[str] = None
        self.last_interaction = datetime.now()
        
        # Subscribe to events
        bus.subscribe(PresenceDetectedEvent, self.handle_presence)
        bus.subscribe(UserSpeechEvent, self.handle_user_speech)
        bus.subscribe(ConversationEndEvent, self.handle_end)
        
        # For async operations
        self.audio_manager = AudioManager(bus)
    
    def handle_presence(self, event: PresenceDetectedEvent):
        """Start conversation when presence detected"""
        if not self.active:
            # Start conversation in async context
            asyncio.create_task(self.start_conversation())
    
    async def handle_user_speech(self, event: UserSpeechEvent):
        """Process user speech"""
        if self.active:
            await self.process_query(event.data)
    
    def handle_end(self, event: ConversationEndEvent):
        """Clean up when conversation ends"""
        self.active = False
        self.logger.info("Conversation ended")
    
    async def start_conversation(self):
        """Initialize a new conversation"""
        self.active = True
        self.bus.publish(ConversationStartEvent())
        
        # Generate greeting (replace with OpenAI call)
        greeting = "Hello! I noticed you're here. Would you like to chat?"
        self.bus.publish(AssistantSpeechEvent(greeting))
        
        # Wait for greeting to finish
        await asyncio.sleep(2)
        
        # Start conversation loop
        await self.conversation_loop()
    
    async def process_query(self, query: str):
        """
        Process user query and generate responses.
        This would integrate with OpenAI API.
        """
        self.logger.info(f"Processing: {query}")
        
        # Simulate API call to generate both responses
        await asyncio.sleep(0.5)
        
        # Generate responses (replace with actual OpenAI call)
        self.immediate_response = f"I heard you say: {query[:30]}..."
        self.followup_response = f"By the way, that reminds me of something interesting..."
        
        # Speak immediate response
        self.bus.publish(AssistantSpeechEvent(self.immediate_response))
        
        # Schedule followup
        asyncio.create_task(self.schedule_followup())
        
        # Update interaction time
        self.last_interaction = datetime.now()
    
    async def schedule_followup(self):
        """Deliver followup response after delay"""
        await asyncio.sleep(5)  # Wait 5 seconds
        
        # Check if still relevant (no new interaction)
        time_since = (datetime.now() - self.last_interaction).seconds
        if time_since >= 5 and self.followup_response and self.active:
            self.bus.publish(AssistantSpeechEvent(self.followup_response))
            self.followup_response = None  # Clear after using
    
    async def conversation_loop(self):
        """Main conversation loop"""
        no_response_count = 0
        
        while self.active:
            # Listen for user input
            user_input = await self.audio_manager.listen_for_speech(timeout=10)
            
            if user_input:
                no_response_count = 0
                await self.process_query(user_input)
            else:
                no_response_count += 1
                
                if no_response_count == 1:
                    # First timeout - check if still there
                    self.bus.publish(AssistantSpeechEvent("Are you still there?"))
                    await asyncio.sleep(2)
                elif no_response_count >= 2:
                    # Second timeout - end conversation
                    self.bus.publish(AssistantSpeechEvent("Goodbye!"))
                    await asyncio.sleep(2)
                    self.bus.publish(ConversationEndEvent())
                    break
            
            await asyncio.sleep(1)  # Small delay between iterations

# ============= SYSTEM CONTROLLER =============
#MARK:
class SystemController:
    """
    Main system controller that coordinates everything.
    Handles system-level events and shutdown procedures.
    """
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Subscribe to system events
        bus.subscribe(ButtonPressEvent, self.handle_button)
        bus.subscribe(ShutdownRequestEvent, self.handle_shutdown)
        
        # State manager
        self.state_manager = StateManager(bus)
        
        # Hardware components
        self.sensor_reader = SensorReader(bus, interval=60)
        self.button_monitor = ButtonMonitor(bus)
        self.mmwave_sensor = MMWaveSensor(bus)
        
        # High-level components
        self.conversation_manager = ConversationManager(bus)
        self.audio_manager = AudioManager(bus)
        
        self.running = True
    
    def handle_button(self, event: ButtonPressEvent):
        """Handle button press events"""
        button_type = event.data
        
        if button_type == 'shutdown':
            self.bus.publish(ShutdownRequestEvent())
        elif button_type == 'stop_start':
            self.toggle_system()
        elif button_type == 'force_chat':
            self.bus.publish(ConversationStartEvent())
    
    def handle_shutdown(self, event: ShutdownRequestEvent):
        """Handle system shutdown request"""
        self.logger.info("Shutdown requested")
        
        # Graceful shutdown sequence
        self.bus.publish(ConversationEndEvent())
        self.state_manager.change_state(SystemState.SHUTTING_DOWN)
        
        # In real implementation:
        # subprocess.run(['sudo', 'shutdown', '-h', 'now'])
        
        self.stop()
    
    def toggle_system(self):
        """Toggle system running state"""
        self.running = not self.running
        self.logger.info(f"System {'started' if self.running else 'stopped'}")
    
    async def run(self):
        """Main run loop"""
        # Start hardware threads
        self.sensor_reader.start()
        self.button_monitor.start()
        self.mmwave_sensor.start()
        
        self.logger.info("System controller started")
        
        # Create event processor task
        event_processor = asyncio.create_task(self.bus.process_events())
        
        try:
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
                
                # Could add periodic health checks here
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up...")
        
        # Stop hardware threads
        self.sensor_reader.stop()
        self.mmwave_sensor.running = False
        self.button_monitor.running = False
        
        # Final state
        self.state_manager.change_state(SystemState.IDLE)
    
    def stop(self):
        """Stop the system"""
        self.running = False

# ============= DEBUGGING AND MONITORING =============
#MARK: 
class DebugMonitor:
    """
    Monitors all events for debugging purposes.
    Can output to console, file, LEDs, web interface, etc.
    """
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Subscribe to ALL events for monitoring
        # In Python, we can't easily subscribe to all events,
        # so we'll subscribe to each type explicitly
        event_types = [
            SensorDataEvent, PresenceDetectedEvent, PresenceLostEvent,
            ButtonPressEvent, ConversationStartEvent, ConversationEndEvent,
            UserSpeechEvent, AssistantSpeechEvent, SystemStateChangeEvent,
            ShutdownRequestEvent
        ]
        
        for event_type in event_types:
            bus.subscribe(event_type, self.log_event)
        
        # Could also start a web server here for remote monitoring
    
    def log_event(self, event: Event):
        """Log all events to file"""
        try:
            # Write to debug log
            with open('event_log.jsonl', 'a') as f:
                log_entry = {
                    'timestamp': event.timestamp.isoformat(),
                    'type': event.event_type,
                    'data': str(event.data)
                }
                f.write(json.dumps(log_entry) + '\n')
            
            # Could also:
            # - Update LEDs based on event type
            # - Send to web dashboard
            # - Update system metrics
            
        except Exception as e:
            self.logger.error(f"Failed to log event: {e}")

# ============= MAIN ENTRY POINT =============
#MARK:
async def main():

    """Main application entry point"""
    logger.info("Starting Voice Assistant with Event Bus Architecture")
    
    # Initialize components
    controller = SystemController(event_bus)
    debug_monitor = DebugMonitor(event_bus)
    
    # Run the system
    try:
        await controller.run()
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        logger.info("Voice Assistant stopped")

#MARK: name == main
if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
