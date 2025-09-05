# Treebot Event Integration - Phase 1: State Management
# This replaces the complex global state handling in your main.py

import threading
import signal
import time
import random
import json
from sync_event_system import EasyEvents, shared_state

# Your existing imports
from elevenlabs_tts import elevenlabs_tts
from openai_api import speech_to_text, query_chatgpt, text_to_speech
from recording import VoiceRecorder
from performance_logger import logger, setup_logging
import RPi.GPIO as GPIO

# Load your config
with open("config.json", "r") as file:
    config = json.load(file)

# Initialize event system
events = EasyEvents(debug=True)

# GPIO setup (your existing code)
LED_PIN = 24
BUTTON_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize shared state
shared_state.mode = "sleeping"  # "sleeping", "idle", "listening", "thinking", "speaking"
shared_state.conversation_history = []

#MARK: State Management Events
@events.on('system.wake')
def wake_system():
    """System becomes active and ready for interaction"""
    shared_state.mode = "idle"
    logger.info("Tree woke up - ready for interaction")
    events.publish('led.pulse', {'pattern': 'wake'})

@events.on('system.sleep')
def sleep_system():
    """System goes to sleep mode"""
    shared_state.mode = "sleeping" 
    logger.info("Tree going to sleep")
    events.publish('audio.goodbye')
    events.publish('led.off')

@events.on('conversation.start')
def start_conversation():
    """Begin new conversation"""
    if shared_state.mode == "sleeping":
        return  # Ignore if sleeping
    
    shared_state.mode = "listening"
    shared_state.conversation_history = []
    logger.info("Starting new conversation")
    events.publish('led.on')

@events.on('conversation.end')
def end_conversation():
    """End current conversation and return to idle"""
    shared_state.mode = "idle"
    logger.info("Conversation ended")

#MARK: LED Control (Event-Driven)
@events.on('led.on')
def led_on():
    GPIO.output(LED_PIN, GPIO.HIGH)

@events.on('led.off')
def led_off():
    GPIO.output(LED_PIN, GPIO.LOW)

@events.on('led.pulse')
def led_pulse(pattern='default'):
    """Different LED patterns for different events"""
    if pattern == 'wake':
        # Gentle fade-in pattern
        for i in range(5):
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.1)
    elif pattern == 'thinking':
        # Slower pulse while processing
        for i in range(3):
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.3)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.2)

@events.on('audio.goodbye')
def play_goodbye():
    """Play goodbye message"""
    random_goodbye = random.choice(config["goodbyes"])
    logger.info(f"Playing goodbye: {random_goodbye['text']}")
    goodbye_audio = elevenlabs_tts(random_goodbye["text"])
    play_audio(goodbye_audio)  # Your existing function

#MARK: Button Handler (Clean Event Version)
def button_handler_events():
    """
    Simplified button handler that just publishes events.
    No more direct global variable manipulation!
    """
    last_state = GPIO.HIGH
    
    while True:
        try:
            current_state = GPIO.input(BUTTON_PIN)
            
            # Detect button press (HIGH to LOW)
            if last_state == GPIO.HIGH and current_state == GPIO.LOW:
                if shared_state.mode == "sleeping":
                    events.publish('system.wake')
                else:
                    events.publish('system.sleep')
                
                time.sleep(0.3)  # Debounce
            
            last_state = current_state
            time.sleep(0.05)
            
        except Exception as e:
            logger.error(f"Button error: {e}")
            time.sleep(1)

def signal_handler_events(signum, frame):
    """Signal handler that publishes events instead of changing globals"""
    logger.info("Received SIGUSR1 signal")
    if shared_state.mode == "sleeping":
        events.publish('system.wake')
    else:
        events.publish('system.sleep')

#MARK: Sensor Integration (Event-Driven)
class EventSensorManager:
    """
    Simplified sensor manager that uses events instead of complex threading.
    Much easier to understand and extend!
    """
    def __init__(self):
        self.current_readings = []
        
    @events.on('sensor.reading_request')
    def update_readings(self):
        """Update sensor readings when requested"""
        try:
            from bme280_sensor import get_sensor_readings
            self.current_readings = get_sensor_readings()
            events.publish('sensor.readings_updated', self.current_readings)
            logger.info(f"Sensor readings updated: {self.current_readings}")
        except Exception as e:
            logger.error(f"Sensor reading error: {e}")
            events.publish('sensor.error', str(e))
    
    @events.every(30.0)  # Update sensors every 30 seconds when idle
    def periodic_update(self):
        """Periodic background sensor updates"""
        if shared_state.mode in ["idle", "sleeping"]:
            events.publish('sensor.reading_request')

#MARK: Simplified Main Loop
def main_event_driven():
    """
    Much simpler main loop - most logic moved to event handlers.
    This makes it easy to test and extend individual components.
    """
    setup_logging()
    logger.info("Starting event-driven treebot")
    
    # Initialize sensor manager (registers its own event handlers)
    sensor_manager = EventSensorManager()
    
    # Start button monitoring thread
    button_thread = threading.Thread(target=button_handler_events, daemon=True)
    button_thread.start()
    logger.info("Button monitoring started")
    
    # Set up signal handler  
    signal.signal(signal.SIGUSR1, signal_handler_events)
    
    # Start event system in background
    stop_events = events.run_in_background()
    
    # System starts sleeping - button press will wake it
    events.publish('system.sleep')
    logger.info("System initialized - press button to wake")
    
    try:
        # Simplified main loop - just handles conversation flow
        while True:
            if shared_state.mode == "idle":
                # Ready for conversation - start listening
                events.publish('conversation.start')
                
                # This is the only blocking operation left
                # (We'll improve this in Phase 2)
                voice_recorder = VoiceRecorder()
                audio_stream = voice_recorder.record_audio()
                
                if audio_stream:
                    events.publish('speech.recorded', audio_stream)
                
                # Wait a bit before next cycle
                time.sleep(0.1)
                
            elif shared_state.mode == "sleeping":
                time.sleep(1)  # Just wait when sleeping
                
            else:
                # Other states (thinking, speaking) handled by events
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        logger.info("Shutting down...")
        stop_events()
        GPIO.cleanup()

#MARK: Enhanced Conversation Flow
@events.on('speech.recorded')  
def process_recorded_speech(audio_stream):
    """Process the recorded audio"""
    shared_state.mode = "thinking"
    events.publish('led.pulse', {'pattern': 'thinking'})
    
    # Play "understood" sound
    if config["tech_config"]["use_raspberry"]:
        import subprocess
        subprocess.run(["mpg123", "audio/understood.mp3"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Speech to text
    question, language = speech_to_text(audio_stream)
    logger.info(f"Transcribed ({language}): {question}")
    
    events.publish('speech.transcribed', {
        'question': question, 
        'language': language
    })

@events.on('speech.transcribed')
def handle_transcribed_speech(question, language):
    """Decide what to do with the transcribed speech"""
    # Check for goodbye phrases
    end_words = config["tech_config"]["end_words"]
    if any(word.lower() in question.lower() for word in end_words):
        events.publish('conversation.goodbye')
        return
    
    # Normal conversation - add to history and query AI
    shared_state.conversation_history.append({"role": "user", "content": question})
    events.publish('ai.query', {'question': question, 'language': language})

@events.on('ai.query')
def query_chatgpt_handler(question, language):
    """Handle AI query with current sensor data"""
    # Request fresh sensor data
    events.publish('sensor.reading_request')
    time.sleep(0.1)  # Give sensor time to respond
    
    # Generate prompt with sensor data (your existing function)
    from main import generate_dynamic_prompt  # Import your function
    prompt = generate_dynamic_prompt(getattr(shared_state, 'current_sensor_readings', []))
    
    # Query AI (your existing function)
    response, full_response = query_chatgpt(question, prompt, shared_state.conversation_history)
    shared_state.conversation_history.append({"role": "assistant", "content": response})
    
    logger.info(f"AI response generated: {response[:50]}...")
    events.publish('ai.response', {'text': response, 'language': language})

@events.on('ai.response')
def generate_and_play_response(text, language):
    """Convert AI response to speech and play it"""
    shared_state.mode = "speaking"
    
    # Generate audio (your existing logic)
    if config["tech_config"]["use_elevenlabs"]:
        audio = elevenlabs_tts(text)
    else:
        audio = text_to_speech(text)
    
    # Play audio
    play_audio(audio)  # Your existing function
    
    events.publish('audio.finished')

@events.on('conversation.goodbye')
def handle_goodbye():
    """Play goodbye and end conversation"""
    random_goodbye = random.choice(config["goodbyes"])
    logger.info("Playing goodbye message")
    
    goodbye_audio = elevenlabs_tts(random_goodbye["text"])
    play_audio(goodbye_audio)
    
    events.publish('conversation.end')

@events.on('audio.finished')
def audio_playback_finished():
    """Called when any audio finishes playing"""
    if shared_state.mode == "speaking":
        shared_state.mode = "idle"  # Ready for next interaction
        logger.info("Ready for next conversation")

#MARK: Event-Driven Sensor Manager 
@events.on('sensor.reading_request')
def update_sensor_readings():
    """Update sensor readings when requested (no more complex threading!)"""
    try:
        if config["tech_config"]["use_raspberry"]:
            from bme280_sensor import get_sensor_readings
        else:
            from all_sensors_on_MAC import get_sensor_readings
            
        readings = get_sensor_readings()
        shared_state.current_sensor_readings = readings
        events.publish('sensor.readings_updated', readings)
        
    except Exception as e:
        logger.error(f"Sensor error: {e}")
        # Fallback readings
        shared_state.current_sensor_readings = [
            ("Temperatur (Celsius)", "N/A", "°C"),
            ("Luftfeuchtigkeit", "N/A", "%"), 
            ("Luftdruck", "N/A", "hPa"),
        ]

@events.every(60.0)  # Update every minute when idle
def periodic_sensor_update():
    """Periodic sensor updates when system is idle"""
    if shared_state.mode in ["idle", "sleeping"]:
        events.publish('sensor.reading_request')

#MARK: Button Handler (Simplified)
def button_monitor():
    """
    Dead simple button handler - just publishes events.
    No more global variable manipulation!
    """
    last_state = GPIO.HIGH
    
    while True:
        try:
            current = GPIO.input(BUTTON_PIN)
            
            if last_state == GPIO.HIGH and current == GPIO.LOW:
                # Button pressed - toggle system state
                if shared_state.mode == "sleeping":
                    events.publish('system.wake')
                else:
                    events.publish('system.sleep') 
                    
                time.sleep(0.3)  # Debounce
                
            last_state = current
            time.sleep(0.05)
            
        except Exception as e:
            logger.error(f"Button error: {e}")
            time.sleep(1)

def signal_handler(signum, frame):
    """Signal handler - publishes events instead of changing globals"""
    logger.info("Received SIGUSR1 toggle signal")
    if shared_state.mode == "sleeping":
        events.publish('system.wake')
    else:
        events.publish('system.sleep')

#MARK: New Main Function
def main():
    """
    Dramatically simplified main function.
    Most logic moved to event handlers - easier to test and extend!
    """
    setup_logging()
    logger.info("Starting event-driven treebot")
    
    # Start button monitoring
    button_thread = threading.Thread(target=button_monitor, daemon=True)
    button_thread.start()
    
    # Set up signal handler
    signal.signal(signal.SIGUSR1, signal_handler)
    
    # Start event system
    stop_events = events.run_in_background()
    
    # Start in sleep mode
    events.publish('system.sleep')
    logger.info("System ready - press button to start")
    
    try:
        # Main loop is now much simpler
        while True:
            if shared_state.mode == "idle":
                # Ready for conversation
                events.publish('conversation.start')
                
                # Record audio (still blocking - we'll fix this in Phase 2)
                voice_recorder = VoiceRecorder() 
                audio_stream = voice_recorder.record_audio()
                
                if audio_stream:
                    events.publish('speech.recorded', audio_stream)
                else:
                    # No speech detected - stay idle
                    shared_state.mode = "idle"
                    
            else:
                # Let events handle other states
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        logger.info("Shutting down gracefully")
        stop_events()
        GPIO.cleanup()

if __name__ == "__main__":
    main()


# ===== MIGRATION NOTES =====
#
# What this replaces in your original main.py:
# 
# 1. Global `loop_active` variable -> shared_state.mode
# 2. Complex button_handler() -> simple button_monitor() + events  
# 3. signal_handler() global changes -> event publishing
# 4. Complex SensorManager threading -> simple event-driven requests
# 5. Monolithic main loop -> clean separation via events
#
# Benefits you get immediately:
# - No more race conditions with global variables
# - Easy to add new features (just subscribe to events)
# - Much easier testing (can inject events)
# - Better logging and debugging
# - Cleaner separation of concerns
#
# To integrate this:
# 1. Copy your existing imports and config loading
# 2. Replace your main() function with this one
# 3. Remove the global loop_active variable
# 4. Remove the old button_handler and SensorManager classes
# 5. Import the sync_event_system module