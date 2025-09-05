# Phase 1: State Management Integration
# Add this to your main.py - replaces global loop_active with events

# from thoughtprocess: Let me create a focused integration plan that addresses the real pain points without over-complicating things.

import threading
import signal
import time
import random
from sync_event_system import EasyEvents, shared_state

# Your existing imports stay the same
from elevenlabs_tts import elevenlabs_tts
from openai_api import speech_to_text, query_chatgpt, text_to_speech
from recording import VoiceRecorder
from performance_logger import logger
import RPi.GPIO as GPIO

# Initialize the event system
events = EasyEvents(debug=True)

# Replace global loop_active with event-driven state
shared_state.mode = "idle"  # "idle", "listening", "thinking", "speaking", "sleeping"

#MARK: State Management Events
@events.on('system.wake')
def wake_system():
    """System becomes active and ready for interaction"""
    shared_state.mode = "idle"
    print("🌲 Tree is now awake and ready to chat!")
    events.publish('led.on')

@events.on('system.sleep') 
def sleep_system():
    """System goes to sleep mode"""
    shared_state.mode = "sleeping"
    print("😴 Tree is going to sleep...")
    events.publish('led.off')
    events.publish('audio.play', {'type': 'goodbye'})

@events.on('conversation.start')
def start_conversation():
    """Begin a new conversation"""
    shared_state.mode = "listening"
    shared_state.conversation_history = getattr(shared_state, 'conversation_history', [])
    events.publish('led.on')
    events.publish('sensor.update_request')

@events.on('conversation.end')
def end_conversation():
    """End current conversation"""
    shared_state.mode = "idle" 
    shared_state.conversation_history = []
    events.publish('led.off')

#MARK: Button/Signal Handlers (Clean Replacement)
def button_handler_events():
    """Monitor button press - now publishes events instead of changing globals"""
    last_button_state = GPIO.HIGH
    
    while True:
        try:
            current_button_state = GPIO.input(BUTTON_PIN)
            
            if last_button_state == GPIO.HIGH and current_button_state == GPIO.LOW:
                # Publish event instead of changing global
                if shared_state.mode == "sleeping":
                    events.publish('system.wake')
                else:
                    events.publish('system.sleep')
                
                # Flash LED to confirm
                events.publish('led.flash', {'times': 3})
                time.sleep(0.3)  # Debounce
            
            last_button_state = current_button_state
            time.sleep(0.05)
            
        except Exception as e:
            logger.error(f"Button handler error: {e}")
            time.sleep(1)

def signal_handler_events(signum, frame):
    """Signal handler - now publishes events"""
    if shared_state.mode == "sleeping":
        events.publish('system.wake')
    else:
        events.publish('system.sleep')
    print(f"Received signal - mode is now {shared_state.mode}")

#MARK: LED Control (Event-Driven)
@events.on('led.on')
def led_on():
    GPIO.output(LED_PIN, GPIO.HIGH)

@events.on('led.off') 
def led_off():
    GPIO.output(LED_PIN, GPIO.LOW)

@events.on('led.flash')
def led_flash(times=1):
    for _ in range(times):
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(LED_PIN, GPIO.LOW) 
        time.sleep(0.1)

#MARK: Modified Main Loop (Event-Driven)
def main_with_events():
    """Simplified main loop that responds to events"""
    setup_logging()
    
    # Start button monitoring 
    button_thread = threading.Thread(target=button_handler_events, daemon=True)
    button_thread.start()
    
    # Set up signal handler
    signal.signal(signal.SIGUSR1, signal_handler_events)
    
    # Start the event system in background
    stop_events = events.run_in_background()
    
    # Wake up the system initially
    events.publish('system.wake')
    
    try:
        # Main conversation loop - much simpler now
        while True:
            if shared_state.mode in ["idle", "listening"]:
                # Only process conversations when awake
                events.publish('conversation.start')
                
                # Record audio (still blocking for now - we'll fix this in Phase 2)
                voice_recorder = VoiceRecorder()
                audio_stream = voice_recorder.record_audio()
                
                if audio_stream:
                    events.publish('speech.recorded', audio_stream)
                
            elif shared_state.mode == "sleeping":
                time.sleep(0.1)  # Sleep mode - just wait
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        stop_events()
        GPIO.cleanup()

#MARK: Conversation Flow Events
@events.on('speech.recorded')
def process_speech(audio_stream):
    """Process recorded speech"""
    shared_state.mode = "thinking"
    events.publish('led.flash', {'times': 2})  # Show we heard them
    
    # Speech to text
    question, language = speech_to_text(audio_stream)
    shared_state.last_question = question
    shared_state.question_language = language
    
    events.publish('speech.transcribed', {'question': question, 'language': language})

@events.on('speech.transcribed')
def handle_transcription(question, language):
    """Handle transcribed speech"""
    # Check for end words
    end_words = config["tech_config"]["end_words"]
    if any(word in question.lower() for word in end_words):
        events.publish('conversation.goodbye_requested')
        return
    
    # Add to history and get response
    shared_state.conversation_history.append({"role": "user", "content": question})
    events.publish('ai.query_requested', {'question': question})

@events.on('ai.query_requested')
def query_ai(question):
    """Query AI for response"""
    # Get current sensor readings
    events.publish('sensor.reading_request')
    # This is still somewhat blocking - we'll improve in Phase 2
    
    with sensor_manager.sensor_lock:
        readings = get_sensor_readings()
    
    prompt = generate_dynamic_prompt(readings)
    response, full_response = query_chatgpt(question, prompt, shared_state.conversation_history)
    
    shared_state.conversation_history.append({"role": "assistant", "content": response})
    events.publish('ai.response_ready', {'response': response})

@events.on('ai.response_ready')
def handle_ai_response(response):
    """Convert AI response to speech and play it"""
    shared_state.mode = "speaking"
    
    # Generate audio
    if config["tech_config"]["use_elevenlabs"]:
        response_audio = elevenlabs_tts(response)
    else:
        response_audio = text_to_speech(response)
    
    events.publish('audio.play', {'audio': response_audio})

@events.on('conversation.goodbye_requested')
def handle_goodbye():
    """Handle goodbye request"""
    random_goodbye = random.choice(config["goodbyes"])
    goodbye_audio = elevenlabs_tts(random_goodbye["text"])
    events.publish('audio.play', {'audio': goodbye_audio})
    events.publish('conversation.end')

@events.on('audio.play')
def play_audio_handler(audio=None, type=None):
    """Play audio - either provided audio or a type"""
    if type == 'goodbye':
        random_goodbye = random.choice(config["goodbyes"])
        audio = elevenlabs_tts(random_goodbye["text"])
    
    if audio:
        play_audio(audio)  # Your existing function
        events.publish('audio.finished')

@events.on('audio.finished')
def audio_finished():
    """Called when audio playback finishes"""
    if shared_state.mode == "speaking":
        shared_state.mode = "idle"  # Ready for next interaction
