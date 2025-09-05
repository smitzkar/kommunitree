# simple_voice_assistant.py
"""
Simplified Voice Assistant - Normal console output with side status panel
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
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich import box
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
    temperature: float = 20.0
    humidity: float = 50.0
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
        
        # Console output
        self.console = Console() if HAS_RICH else None
        self.log_messages = []
        
        # Start background threads
        self.presence_thread = threading.Thread(target=self._monitor_presence, daemon=True)
        self.sensor_thread = threading.Thread(target=self._read_sensors, daemon=True)
        
    def log(self, message: str, level: str = "INFO"):
        """Add a log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.log_messages.append(log_entry)
        
        # Keep only last 20 messages
        if len(self.log_messages) > 20:
            self.log_messages.pop(0)
    
    def start(self):
        """Start the assistant"""
        self.presence_thread.start()
        self.sensor_thread.start()
        
        if HAS_RICH:
            self._run_with_panel()
        else:
            self._run_simple()
    
    def _run_simple(self):
        """Run with simple print output"""
        try:
            asyncio.run(self._main_loop())
        except KeyboardInterrupt:
            print("\nShutting down...")
    
    def _run_with_panel(self):
        """Run with side status panel"""
        layout = Layout()
        layout.split_row(
            Layout(name="logs", ratio=2),
            Layout(name="status", ratio=1)
        )
        
        with Live(layout, refresh_per_second=2, console=self.console) as live:
            try:
                asyncio.run(self._main_loop(live, layout))
            except KeyboardInterrupt:
                self.console.print("\n[red]Shutting down...[/red]")
    
    def _create_status_panel(self):
        """Create the status panel"""
        table = Table(box=box.SIMPLE)
        table.add_column("Property", style="cyan", width=12)
        table.add_column("Value", style="white", width=15)
        
        # Status with colors
        state_colors = {
            State.IDLE: "white",
            State.LISTENING: "yellow",
            State.THINKING: "blue", 
            State.SPEAKING: "green"
        }
        state_color = state_colors[self.status.state]
        
        table.add_row("State", f"[{state_color}]{self.status.state.value}[/{state_color}]")
        table.add_row("Presence", "[green]YES[/green]" if self.status.presence else "[red]NO[/red]")
        table.add_row("Conversation", "[green]ACTIVE[/green]" if self.status.conversation_active else "[dim]inactive[/dim]")
        table.add_row("Temperature", f"{self.status.temperature:.1f}°C")
        table.add_row("Humidity", f"{self.status.humidity:.0f}%")
        table.add_row("Uptime", f"{self.status.uptime:.0f}s")
        
        return Panel(table, title="System Status", border_style="blue")
    
    def _create_log_panel(self):
        """Create the log panel"""
        log_text = Text()
        for msg in self.log_messages:
            if "ERROR" in msg:
                log_text.append(msg + "\n", style="red")
            elif "WARN" in msg:
                log_text.append(msg + "\n", style="yellow")
            elif "SPEAK" in msg:
                log_text.append(msg + "\n", style="green")
            elif "LISTEN" in msg:
                log_text.append(msg + "\n", style="cyan")
            else:
                log_text.append(msg + "\n", style="white")
        
        return Panel(log_text, title="Activity Log", border_style="green")

    async def _main_loop(self, live=None, layout=None):
        """Main application loop"""
        self.log("System started")
        
        while self.running:
            self.status.uptime = time.time() - self.start_time
            
            # Update display if using rich
            if live and layout:
                layout["status"].update(self._create_status_panel())
                layout["logs"].update(self._create_log_panel())
            
            # Handle presence-based conversation
            if self.status.presence and not self.status.conversation_active:
                await self._start_conversation()
            elif not self.status.presence and self.status.conversation_active:
                await self._end_conversation()
            
            await asyncio.sleep(0.5)

    # Background monitoring
    def _monitor_presence(self):
        """Monitor presence sensor"""
        while self.running:
            old_presence = self.status.presence
            
            if self.simulate_hardware:
                # Simulate presence changes every 10-30 seconds
                if random.random() > 0.99:  # 1% chance to change
                    self.status.presence = not self.status.presence
                    if self.status.presence != old_presence:
                        self.log(f"Presence {'detected' if self.status.presence else 'lost'}")
            
            time.sleep(1)
    
    def _read_sensors(self):
        """Read environmental sensors"""
        while self.running:
            if self.simulate_hardware:
                # Gradually changing values
                self.status.temperature += random.uniform(-0.5, 0.5)
                self.status.temperature = max(15, min(35, self.status.temperature))
                
                self.status.humidity += random.uniform(-2, 2)
                self.status.humidity = max(20, min(80, self.status.humidity))
            
            time.sleep(3)

    # Conversation logic
    async def _start_conversation(self):
        """Start a new conversation"""
        if self.status.conversation_active:
            return
            
        self.status.conversation_active = True
        self.log("Starting conversation")
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
                self.log(f"User said: '{user_input}'", "LISTEN")
                
                # Process and respond
                response = await self._generate_response(user_input)
                if response:
                    await self._speak(response)
            else:
                silence_count += 1
                self.log(f"No response (timeout {silence_count}/2)")
                
                if silence_count >= 2:
                    await self._end_conversation()
                    break
                elif silence_count == 1:
                    await self._speak("Are you still there?")
    
    async def _end_conversation(self):
        """End the current conversation"""
        if not self.status.conversation_active:
            return
            
        self.log("Ending conversation")
        await self._speak(self.goodbye)
        self.status.conversation_active = False
    
    # Audio simulation
    async def _listen(self) -> Optional[str]:
        """Listen for speech input"""
        self.status.state = State.LISTENING
        self.log("Listening for speech...")
        
        if self.simulate_hardware:
            # Simulate listening time
            for i in range(30):  # 3 seconds
                await asyncio.sleep(0.1)
                if not self.status.presence:  # Stop if presence lost
                    break
            
            # Random chance of getting speech
            if random.random() > 0.4:  # 60% chance
                responses = [
                    "Hello, how are you today?",
                    "What's the weather like outside?",
                    "Can you tell me a joke?",
                    "What time is it?",
                    "I'm doing well, thanks for asking",
                    "That's interesting, tell me more",
                    "Goodbye, see you later"
                ]
                self.status.state = State.IDLE
                return random.choice(responses)
        
        self.status.state = State.IDLE
        return None
    
    async def _speak(self, text: str):
        """Speak text output"""
        self.status.state = State.SPEAKING
        self.status.last_speech = text
        self.log(f"Speaking: '{text}'", "SPEAK")
        
        if self.simulate_hardware:
            # Simulate speaking time based on text length
            duration = len(text) * 0.05  # 50ms per character
            await asyncio.sleep(duration)
        
        self.status.state = State.IDLE
    
    async def _generate_response(self, user_input: str) -> Optional[str]:
        """Generate AI response"""
        self.status.state = State.THINKING
        self.log("Generating response...")
        
        if self.simulate_hardware:
            await asyncio.sleep(1)  # Simulate thinking time
            
            # Simple response logic
            input_lower = user_input.lower()
            if "hello" in input_lower or "hi" in input_lower:
                responses = [
                    "Hello there! It's great to see you.",
                    "Hi! How are you doing today?",
                    "Hello! What can I help you with?"
                ]
                return random.choice(responses)
            elif "weather" in input_lower:
                return f"Based on my sensors, it's {self.status.temperature:.1f} degrees with {self.status.humidity:.0f}% humidity here."
            elif "joke" in input_lower:
                jokes = [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                    "What do you call a bear with no teeth? A gummy bear!"
                ]
                return random.choice(jokes)
            elif "time" in input_lower:
                return f"The current time is {datetime.now().strftime('%I:%M %p')}."
            elif "goodbye" in input_lower or "bye" in input_lower:
                self.status.conversation_active = False
                return "It was nice talking with you. Goodbye!"
            else:
                responses = [
                    f"You said: '{user_input}'. That's quite interesting!",
                    "I see. Can you tell me more about that?",
                    "That's fascinating. What made you think of that?",
                    "Hmm, I'm not sure I understand completely. Could you explain more?"
                ]
                return random.choice(responses)
        
        self.status.state = State.IDLE
        return None

def main():
    assistant = SimpleVoiceAssistant()
    assistant.start()

if __name__ == "__main__":
    main()