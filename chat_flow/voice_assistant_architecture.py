"""
2025-09-03 claude ai: https://claude.ai/public/artifacts/8f6520d3-57cb-463e-a470-7c22b8052678 


Simplified Voice Assistant Architecture for Raspberry Pi
This provides a foundation that's easy to understand and extend
"""

import asyncio
import threading
import queue
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import logging
from enum import Enum

#MARK: Logging
# Set up simple logging
# here using "relativeCreated" = time since start of script
logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
logger = logging.getLogger(__name__)

# ============= SHARED STATE SYSTEM =============
#MARK: SystemState
class SystemState(Enum):
    """Simple state tracking"""
    IDLE = "idle"
    LISTENING = "listening"
    SPEAKING = "speaking"
    PROCESSING = "processing"
    CONVERSATION_ACTIVE = "conversation_active"
    
#MARK: SensorData
@dataclass
class SensorData:
    """Simple container for sensor readings"""
    temperature: float
    humidity: float
    timestamp: datetime
    presence_detected: bool = False

#MARK: GlobalState
class GlobalState:
    """
    Simple global state manager - all components can read/write here
    In production, you might want to add thread-safe locks for certain operations
    """
    def __init__(self):
        self.current_state = SystemState.IDLE
        self.latest_sensor_data: Optional[SensorData] = None
        self.conversation_active = False
        self.presence_detected = False
        self.debug_info: Dict[str, Any] = {}
    
    def update(self, key: str, value: Any):
        """Simple update method for any component to use"""
        if key == "sensor_data":
            self.latest_sensor_data = value
        elif key == "presence":
            self.presence_detected = value
        elif key == "conversation":
            self.conversation_active = value
        else:
            self.debug_info[key] = value
        logger.info(f"State updated: {key} = {value}")

# Global instance - simple singleton pattern
state = GlobalState()

# ============= HARDWARE INTERFACES (THREADING) =============
#MARK: SensorReader
class SensorReader(threading.Thread):
    """
    Runs in a separate thread to handle blocking GPIO operations
    Communicates with async world via a queue
    
    Default update_interval = 60s
    """
    def __init__(self, interval=60):
        super().__init__(daemon=True)
        self.interval = interval
        self.running = True
        self.data_queue = queue.Queue()
        
    def run(self):
        """Thread main loop - reads sensors periodically"""
        while self.running:
            # Simulate sensor reading (replace with actual GPIO code)
            import random
            data = SensorData(
                temperature=20 + random.random() * 10,
                humidity=40 + random.random() * 20,
                timestamp=datetime.now()
            )
            
            # Put data in queue for async world to consume
            self.data_queue.put(data)
            
            # Sleep until next reading
            threading.Event().wait(self.interval)
    
    def stop(self):
        self.running = False

#MARK: ButtonHandler
class ButtonHandler(threading.Thread):
    """
    Handles GPIO button interrupts in a separate thread
    """
    def __init__(self):
        super().__init__(daemon=True)
        self.event_queue = queue.Queue()
        self.running = True
    
    def run(self):
        """
        In real implementation, this would set up GPIO interrupts
        For now, we'll simulate
        """
        while self.running:
            # This would be replaced by actual GPIO interrupt callbacks
            threading.Event().wait(1)
    
    def simulate_button_press(self, button_type):
        """For testing - simulate a button press"""
        self.event_queue.put(("button", button_type))

# ============= ASYNC COMPONENTS =============
#MARK: ConversationManager
class ConversationManager:
    """
    Manages the AI conversation flow using asyncio
    """
    def __init__(self):
        self.active = False
        self.immediate_response = None
        self.followup_response = None
        self.last_interaction = datetime.now()
        
    async def start_conversation(self):
        """Initialize a new conversation"""
        self.active = True
        state.update("conversation", True)
        logger.info("Conversation started")
        
        # Simulate greeting (replace with actual OpenAI call)
        await asyncio.sleep(1)
        return "Hello! I noticed you're here. Would you like to chat?"
    
    async def process_query(self, query: str):
        """
        Process user input and generate responses
        In real implementation, this would call OpenAI API
        """
        logger.info(f"Processing query: {query}")
        
        # Simulate API call
        await asyncio.sleep(0.5)
        
        # Generate both immediate and followup responses
        self.immediate_response = f"Quick response to: {query}"
        self.followup_response = f"Interesting thought about {query}..."
        self.last_interaction = datetime.now()
        
        return self.immediate_response
    
    async def check_followup(self, timeout=5):
        """Check if we should deliver the followup response"""
        await asyncio.sleep(timeout)
        
        time_since_last = (datetime.now() - self.last_interaction).seconds
        if time_since_last >= timeout and self.followup_response:
            return self.followup_response
        return None
    
    async def end_conversation(self):
        """Clean up conversation"""
        self.active = False
        state.update("conversation", False)
        logger.info("Conversation ended")

#MARK: AudioManager
class AudioManager:
    """
    Manages audio I/O - bridges between threading and async
    """
    def __init__(self):
        self.playing = False
        self.listening = False
        
    async def listen_for_speech(self, timeout=10):
        """
        Start listening for speech input
        Real implementation would use threading for audio capture
        """
        self.listening = True
        state.current_state = SystemState.LISTENING
        
        # Simulate listening (replace with actual audio capture)
        await asyncio.sleep(2)
        
        self.listening = False
        return "simulated user input"
    
    async def play_speech(self, text: str):
        """
        Play TTS output
        Real implementation would use threading for audio playback
        """
        self.playing = True
        state.current_state = SystemState.SPEAKING
        
        logger.info(f"Speaking: {text}")
        
        # Simulate TTS playback
        await asyncio.sleep(len(text) * 0.05)  # Rough estimate
        
        self.playing = False
        state.current_state = SystemState.IDLE

# ============= MAIN EVENT LOOP =============
#MARK: VoiceAssistant 
# basically the real main()
class VoiceAssistant:
    """
    Main coordinator - runs the async event loop and coordinates all components
    """
    def __init__(self):
        self.sensor_reader = SensorReader(interval=5)
        self.button_handler = ButtonHandler()
        self.conversation = ConversationManager()
        self.audio = AudioManager()
        self.running = True
        
    async def sensor_monitor(self):
        """Async task to consume sensor data from thread queue"""
        while self.running:
            try:
                # Non-blocking check for sensor data
                if not self.sensor_reader.data_queue.empty():
                    data = self.sensor_reader.data_queue.get_nowait()
                    state.update("sensor_data", data)
                    
                    # Log to CSV (simplified)
                    logger.info(f"Sensor: T={data.temperature:.1f}°C, H={data.humidity:.1f}%")
                
                await asyncio.sleep(1)
            except queue.Empty:
                await asyncio.sleep(1)
    
    async def button_monitor(self):
        """Async task to handle button events from thread queue"""
        while self.running:
            try:
                if not self.button_handler.event_queue.empty():
                    event_type, button = self.button_handler.event_queue.get_nowait()
                    await self.handle_button(button)
                
                await asyncio.sleep(0.1)
            except queue.Empty:
                await asyncio.sleep(0.1)
    
    async def handle_button(self, button_type: str):
        """Handle different button presses"""
        logger.info(f"Button pressed: {button_type}")
        
        if button_type == "shutdown":
            # Use threading for subprocess call
            threading.Thread(target=self.shutdown_pi, daemon=True).start()
        elif button_type == "stop_start":
            self.running = not self.running
        elif button_type == "force_conversation":
            if not self.conversation.active:
                await self.start_conversation_flow()
    
    def shutdown_pi(self):
        """Shutdown Raspberry Pi (runs in thread)"""
        import subprocess
        subprocess.run(["sudo", "shutdown", "-h", "now"])
    
    async def presence_monitor(self):
        """Monitor for human presence (simulated for now)"""
        while self.running:
            # In real implementation, check mmWave sensor
            if state.presence_detected and not self.conversation.active:
                await self.start_conversation_flow()
            
            await asyncio.sleep(2)
    
    async def start_conversation_flow(self):
        """Main conversation flow"""
        greeting = await self.conversation.start_conversation()
        await self.audio.play_speech(greeting)
        
        # Main conversation loop
        while self.conversation.active and state.presence_detected:
            # Listen for input
            user_input = await self.audio.listen_for_speech()
            
            if user_input:
                # Process and respond immediately
                response = await self.conversation.process_query(user_input)
                await self.audio.play_speech(response)
                
                # Schedule followup check
                asyncio.create_task(self.deliver_followup())
            else:
                # No input detected - check if person still there
                await self.audio.play_speech("Are you still there?")
                confirmation = await self.audio.listen_for_speech(timeout=5)
                
                if not confirmation:
                    await self.audio.play_speech("Goodbye!")
                    await self.conversation.end_conversation()
    
    async def deliver_followup(self):
        """Deliver followup response if appropriate"""
        followup = await self.conversation.check_followup()
        if followup and self.conversation.active:
            await self.audio.play_speech(followup)
    
    async def run(self):
        """Main entry point - start all systems"""
        # Start hardware threads
        self.sensor_reader.start()
        self.button_handler.start()
        
        # Create async tasks
        tasks = [
            asyncio.create_task(self.sensor_monitor()),
            asyncio.create_task(self.button_monitor()),
            asyncio.create_task(self.presence_monitor()),
        ]
        
        logger.info("Voice Assistant started")
        
        try:
            # Run until interrupted
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.running = False
            self.sensor_reader.stop()

# ============= ENTRY POINT =============
#MARK: main
def main():
    """Simple main function to start everything"""
    assistant = VoiceAssistant()
    
    try:
        # Run the async event loop
        asyncio.run(assistant.run())
    except KeyboardInterrupt:
        logger.info("Assistant stopped")

#MARK: name == main
if __name__ == "__main__":
    main()
