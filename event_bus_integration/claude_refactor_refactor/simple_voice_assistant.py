# simple_voice_assistant.py
"""
Simplified Voice Assistant - Core functionality only
No over-engineering, just what's needed to make it work
"""

import asyncio
import threading
import time
import random
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from enum import Enum

# Simple status display using rich
try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class State(Enum):
    IDLE = "Idle"
    LISTENING = "Listening"
    THINKING = "Processing"
    SPEAKING = "Speaking"

@dataclass
class SystemStatus:
    state: State = State.IDLE
    presence: bool = False
    temperature: float = 0.0
    humidity: float = 0.0
    conversation_active: bool = False
    last_speech: str = ""
    uptime: float = 0.0

class SimpleVoiceAssistant:
    def __init__(self):
        self.status = SystemStatus()
        self.running = True
        self.start_time = time.time()
        
        # Simple config
        self.simulate_hardware = True
        self.speech_timeout = 8
        self.greeting = "Hello! I noticed you're here. How can I help?"
        self.goodbye = "Goodbye! Have a great day!"
        
        # Start background threads
        self.presence_thread = threading.Thread(target=self._monitor_presence, daemon=True)
        self.sensor_thread = threading.Thread(target=self._read_sensors, daemon=True)
        self.button_thread = threading.Thread(target=self._monitor_buttons, daemon=True)
        
    def start(self):
        """Start all background monitoring"""
        self.presence_thread.start()
        self.sensor_thread.start() 
        self.button_thread.start()
        
        if HAS_RICH:
            self._run_with_display()
        else:
            self._run_simple()
    
    def _run_with_display(self):
        """Run with rich live display"""
        console = Console()
        
        with Live(self._create_display(), refresh_per_second=2, console=console) as live:
            try:
                asyncio.run(self._main_loop(live))
            except KeyboardInterrupt:
                console.print("\n[red]Shutting down...[/red]")
    
    def _run_simple(self):
        """Run with simple print output"""
        try:
            asyncio.run(self._main_loop())
        except KeyboardInterrupt:
            print("\nShutting down...")
    
    def _create_display(self):
        """Create the status display table"""
        table = Table(title="Voice Assistant Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        # Status indicators
        state_color = {
            State.IDLE: "white",
            State.LISTENING: "yellow", 
            State.THINKING: "blue",
            State.SPEAKING: "green"
        }[self.status.state]
        
        table.add_row("State", f"[{state_color}]{self.status.state.value}[/{state_color}]")
        table.add_row("Presence", "🟢 Detected" if self.status.presence else "🔴 None")
        table.add_row("Conversation", "🟢 Active" if self.status.conversation_active else "⚪ Inactive")
        table.add_row("Temperature", f"{self.status.temperature:.1f}°C")
        table.add_row("Humidity", f"{self.status.humidity:.1f}%")
        table.add_row("Last Speech", self.status.last_speech[:50] + "..." if len(self.status.last_speech) > 50 else self.status.last_speech)
        table.add_row("Uptime", f"{self.status.uptime:.1f}s")
        
        return Panel(table, title="🤖 TreeBot", border_style="blue")

    async def _main_loop(self, live=None):
        """Main application loop"""
        while self.running:
            self.status.uptime = time.time() - self.start_time
            
            # Update display if using rich
            if live:
                live.update(self._create_display())
            
            # Handle presence-based conversation
            if self.status.presence and not self.status.conversation_active:
                await self._start_conversation()
            elif not self.status.presence and self.status.conversation_active:
                await self._end_conversation()
            
            await asyncio.sleep(0.5)

    # Background monitoring threads (simple, no events)
    def _monitor_presence(self):
        """Monitor presence sensor"""
        while self.running:
            if self.simulate_hardware:
                # Simulate random presence changes
                if random.random() > 0.98:  # 2% chance to change state
                    self.status.presence = not self.status.presence
            else:
                # Real sensor code would go here
                pass
            time.sleep(1)
    
    def _read_sensors(self):
        """Read environmental sensors"""
        while self.running:
            if self.simulate_hardware:
                self.status.temperature = 20 + random.random() * 10
                self.status.humidity = 40 + random.random() * 20
            else:
                # Real sensor code would go here
                pass
            time.sleep(5)  # Read every 5 seconds
    
    def _monitor_buttons(self):
        """Monitor button presses"""
        while self.running:
            if self.simulate_hardware:
                # Simulate occasional button press
                if random.random() > 0.995:  # 0.5% chance
                    if random.random() > 0.5:
                        asyncio.run_coroutine_threadsafe(
                            self._handle_shutdown(), 
                            asyncio.get_event_loop()
                        )
            else:
                # Real GPIO code would go here
                pass
            time.sleep(0.1)

    # Core conversation logic
    async def _start_conversation(self):
        """Start a new conversation"""
        if self.status.conversation_active:
            return
            
        self.status.conversation_active = True
        await self._speak(self.greeting)
        
        # Start conversation loop
        asyncio.create_task(self._conversation_loop())
    
    async def _conversation_loop(self):
        """Main conversation loop"""
        silence_count = 0
        
        while self.status.conversation_active and self.status.presence:
            # Listen for user input
            user_input = await self._listen()
            
            if user_input:
                silence_count = 0
                # Process and respond
                response = await self._generate_response(user_input)
                if response:
                    await self._speak(response)
            else:
                silence_count += 1
                if silence_count >= 2:  # 2 timeouts = end conversation
                    await self._end_conversation()
                    break
                elif silence_count == 1:
                    await self._speak("Are you still there?")
    
    async def _end_conversation(self):
        """End the current conversation"""
        if not self.status.conversation_active:
            return
            
        await self._speak(self.goodbye)
        self.status.conversation_active = False
    
    # Audio methods (simplified)
    async def _listen(self) -> Optional[str]:
        """Listen for speech input"""
        self.status.state = State.LISTENING
        
        if self.simulate_hardware:
            await asyncio.sleep(2)  # Simulate listening delay
            if random.random() > 0.3:  # 70% chance of getting input
                responses = [
                    "Hello, how are you?",
                    "What's the weather like?", 
                    "Tell me a joke",
                    "What time is it?",
                    "Goodbye"
                ]
                return random.choice(responses)
        else:
            # Real speech recognition would go here
            pass
        
        return None
    
    async def _speak(self, text: str):
        """Speak text output"""
        self.status.state = State.SPEAKING
        self.status.last_speech = text
        
        if self.simulate_hardware:
            # Simulate TTS delay based on text length
            duration = len(text) * 0.03  # ~30ms per character
            await asyncio.sleep(duration)
        else:
            # Real TTS would go here
            pass
        
        self.status.state = State.IDLE
    
    async def _generate_response(self, user_input: str) -> Optional[str]:
        """Generate AI response"""
        self.status.state = State.THINKING
        
        if self.simulate_hardware:
            await asyncio.sleep(1)  # Simulate API delay
            
            # Simple response logic
            input_lower = user_input.lower()
            if "hello" in input_lower or "hi" in input_lower:
                return "Hello there! It's nice to meet you."
            elif "weather" in input_lower:
                return f"The temperature here is {self.status.temperature:.1f} degrees with {self.status.humidity:.1f}% humidity."
            elif "joke" in input_lower:
                jokes = [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                    "Why don't eggs tell jokes? They'd crack each other up!"
                ]
                return random.choice(jokes)
            elif "time" in input_lower:
                return f"The current time is {datetime.now().strftime('%I:%M %p')}."
            elif "goodbye" in input_lower or "bye" in input_lower:
                self.status.conversation_active = False
                return "Goodbye! Have a wonderful day!"
            else:
                return f"I heard you say: '{user_input}'. That's interesting! Tell me more."
        else:
            # Real AI API call would go here
            pass
        
        return None
    
    # System control
    async def _handle_shutdown(self):
        """Handle shutdown request"""
        await self._speak("Shutting down. Goodbye!")
        self.running = False

def main():
    assistant = SimpleVoiceAssistant()
    assistant.start()

if __name__ == "__main__":
    main()