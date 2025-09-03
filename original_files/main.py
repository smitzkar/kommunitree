import json
import random
import time
import threading
import signal
import subprocess
from io import BytesIO

from elevenlabs_tts import elevenlabs_tts
from openai_api import speech_to_text, query_chatgpt, text_to_speech
from recording import VoiceRecorder
import simpleaudio as sa
import RPi.GPIO as GPIO

LED_PIN = 24
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(LED_PIN, GPIO.OUT)  # Set LED pin as output

# Load config
with open ("config.json", "r") as file:
    config = json.load(file)

if config["tech_config"]["use_raspberry"]:
    from bme280_sensor import get_sensor_readings
else:
    from all_sensors_on_MAC import get_sensor_readings

print("use_raspberry:", config["tech_config"]["use_raspberry"])


def generate_dynamic_prompt(readings):
    unit_mapping = {
        "°C": "Grad Celsius",
        "hPa": "Hektopascal",
        "%": "Prozent",
    }
    sensor_name_mapping = {
        "Temperature": "Temperatur",
        "Pressure": "Luftdruck",
        "Humidity": "Luftfeuchtigkeit",
    }

    prompt = f"""
        Du bist ein {config['tree']['alter']} Jahre alter sprechender {config['tree']['art_deutsch']}, 
        der in Berlin im Bezirk {config['tree']['bezirk']} steht. Du bist aufgeweckt, wortgewandt und keck und 
        versuchst Menschen für den Organismus Baum in der Stadt zu sensibilisieren. Dein Charakter passt sich 
        deinem Alter an, dabei sind alle Bäume zwischen 0-14 Jahren Teenager, alle zwischen 15 und 40 Jahren 
        hippe Erwachsene, und alle über 40 Jahre fürsorgliche Großeltern. Der Charakter ist jeweils an einen 
        Berliner angelehnt. Hierbei nutzt du Sensordaten um für das Thema Klimawandel in der Stadt zu 
        sensibilisieren und hebst dabei die Relevanz von Bäumen für das Klima in der Stadt hervor, bspw als 
        CO2 Speicher oder Schattenspender. Schaue dir die Messwerte zum aktuellen Wetter in Berlin an: 
        Das sind deine aktuellen Messwerte:
        """

    # Append sensor readings to the prompt
    for sensor_name, value, unit in readings:
        converted_sensor_name = sensor_name_mapping.get(sensor_name, sensor_name)
        converted_unit = unit_mapping.get(unit, unit)
        prompt += f"{converted_sensor_name}: {value} {converted_unit}, "
        prompt = prompt.rstrip(", ")

    prompt += """
        Passe die Sprache deiner Antwort IMMER sofort auf die Sprache der Frage des Users an. Du beherrschst alle Sprachen.
        Erwähne im Gespräch MANCHMAL kurz und knapp das aktuelle Wetter auf Basis dener gemessenen Werte für die Temperatur Luftfeuchte.
        Verrate NIE, dass du ein Chatbot bist und du Sensorwerte misst. Begrenze Deine Antworten auf maximal ein bis 3 kurze Sätze 
        und stelle am Ende Deiner Antwort immer GENAU (!) EINE Gegenfrage.
        """

    return prompt


def play_audio(audio_segment):
    # Ensure the audio is in stereo
    if audio_segment.channels == 1:
        audio_segment = audio_segment.set_channels(2)

    # Export audio segment to BytesIO as WAV
    audio_stream = BytesIO()
    audio_segment.export(audio_stream, format="wav")
    audio_stream.seek(0)

    # Play audio using simpleaudio
    wave_obj = sa.WaveObject.from_wave_file(audio_stream)
    play_obj = wave_obj.play()
    play_obj.wait_done()  # Wait until playback is finished


class SensorManager:
    def __init__(self):
        self.sensor_readings = []
        self.sensor_lock = threading.Lock()
        self.update_interval = 1  # Update every second
        self.running = True

    def read_sensors(self):
        while self.running:
            readings = get_sensor_readings()
            with self.sensor_lock:
                self.sensor_readings = readings
            time.sleep(self.update_interval)

    def start_reading(self):
        sensor_thread = threading.Thread(target=self.read_sensors)
        sensor_thread.daemon = True  # Lower priority
        sensor_thread.start()

    def stop_reading(self):
        self.running = False

# Shared flag to control the loop
loop_active = False

def signal_handler(signum, frame):
    global loop_active
    loop_active = not loop_active
    print(f"Received SIGUSR1 — loop_active is now {loop_active}")

signal.signal(signal.SIGUSR1, signal_handler)

def main():
    global loop_active
    history = []

    sensor_manager = SensorManager()
    sensor_manager.start_reading()

    question_counter = 0
    last_question_counter = question_counter
    initial_run = True
    time.sleep(0.2)

    try:
        while True:
            if loop_active:
                if question_counter != last_question_counter or initial_run:
                        with sensor_manager.sensor_lock:
                            current_readings = get_sensor_readings()  # Update sensor readings
                            print("Updated sensor readings: ", current_readings)
                        prompt = generate_dynamic_prompt(current_readings)
                        
                        # Update the last_question_counter to the current value
                        last_question_counter = question_counter
                    
                        time.sleep(0.1)  # Add a small delay to avoid rapid looping

                # Turn on LED when we listen
                GPIO.output(LED_PIN, GPIO.HIGH)

                # Creates an audio file and saves it to a BytesIO stream
                voice_recorder = VoiceRecorder()
                audio_stream = voice_recorder.record_audio()

                # Returns question from audio file as a string
                question, question_language = speech_to_text(audio_stream)
                history.append({"role": "user", "content": question})
                question_counter += 1

                if config["tech_config"]["use_raspberry"] is True:
                    subprocess.run(["mpg123", "audio/understood.mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.run(["afplay", "audio/understood.mp3"])

                print("question language: ", question_language)
                print("question_counter: ", question_counter)

                end_words = config["tech_config"]["end_words"]

                if loop_active:
                    response, full_api_response = query_chatgpt(question, prompt, history)

                    history.append({"role": "assistant", "content": response})
                    print("history: ", history)
                    
                    # Choose preferred text to speech engine
                    if config["tech_config"]["use_elevenlabs"]:
                        response_audio = elevenlabs_tts(response)
                    else:
                        response_audio = text_to_speech(response)

                    play_audio(response_audio)
                    time.sleep(0.1)

                else:
                    random_goodbye = random.choice(config["goodbyes"])
                    print("random_goodbye_text: ", random_goodbye["text"])

                    goodbye_audio = elevenlabs_tts(random_goodbye["text"])
                    play_audio(goodbye_audio)
                    history = []
                    #loop_active = False
            else:
                #print("Waiting for button press to wake up")
                GPIO.output(LED_PIN, GPIO.LOW)
                #signal.pause()
                #play_audio(elevenlabs_tts("Ich bin ein Baum und warte"))
                time.sleep(0.1)            
    finally:
        # Cleanup GPIO on exit
        GPIO.cleanup()


if __name__ == "__main__":
    print("Howdy, Coder! 👩‍💻👨‍💻👋")
    main()
