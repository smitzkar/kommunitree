#!/usr/bin/env python3
"""
Non-streaming voice agent that works without OpenAI organization verification.
This version processes requests without streaming, which should bypass the verification requirement.
"""

import asyncio
import random
import json
import io
import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI
import os
from dotenv import load_dotenv
from util import record_audio, AudioPlayer

# Load environment variables
load_dotenv()

class NonStreamingVoiceAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_history = []
        
    def get_weather(self, city: str) -> str:
        """Get the weather for a given city (mock function)."""
        print(f"[debug] get_weather called with city: {city}")
        choices = ["sunny", "cloudy", "rainy", "snowy"]
        return f"The weather in {city} is {random.choice(choices)}."
    
    def process_function_call(self, function_name: str, arguments: dict) -> str:
        """Process function calls from the AI."""
        if function_name == "get_weather":
            return self.get_weather(arguments.get("city", ""))
        return "Function not found."
    
    def audio_to_text(self, audio_data: np.ndarray) -> str:
        """Convert audio to text using OpenAI Whisper."""
        # Convert numpy array to WAV bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, 24000, format='WAV')
        buffer.seek(0)
        
        # Create a temporary file-like object for OpenAI API
        audio_file = buffer
        audio_file.name = "audio.wav"
        
        try:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcript.text
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""
    
    def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using OpenAI TTS."""
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            return response.content
        except Exception as e:
            print(f"Error generating speech: {e}")
            return b""
    
    def play_audio_bytes(self, audio_bytes: bytes):
        """Play audio from bytes using sounddevice."""
        try:
            # Convert bytes to audio data
            audio_io = io.BytesIO(audio_bytes)
            data, samplerate = sf.read(audio_io)
            
            # Play the audio
            sd.play(data, samplerate)
            sd.wait()  # Wait until playback is finished
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    async def get_ai_response(self, user_input: str, language_hint: str = None) -> str:
        """Get response from OpenAI with function calling support (non-streaming)."""
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Define available functions
        functions = [
            {
                "name": "get_weather",
                "description": "Get the weather for a given city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The name of the city"
                        }
                    },
                    "required": ["city"]
                }
            }
        ]
        
        # Determine system message based on language hint
        system_message = "You're a helpful voice assistant. Be polite and concise since you're speaking to a human. If the user asks about weather, use the get_weather function."
        if language_hint == "spanish" or "spanish" in user_input.lower() or any(word in user_input.lower() for word in ["hola", "buenos", "gracias", "español"]):
            system_message = "You're a helpful voice assistant that speaks Spanish. Be polite and concise since you're speaking to a human. Respond in Spanish. If the user asks about weather, use the get_weather function."
        
        try:
            # Get response from OpenAI (NON-STREAMING)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message}
                ] + self.conversation_history,
                functions=functions,
                function_call="auto",
                stream=False  # Explicitly disable streaming
            )
            
            message = response.choices[0].message
            
            # Check if AI wants to call a function
            if message.function_call:
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)
                
                # Call the function
                function_result = self.process_function_call(function_name, function_args)
                
                # Add function call and result to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": function_name,
                        "arguments": message.function_call.arguments
                    }
                })
                self.conversation_history.append({
                    "role": "function",
                    "name": function_name,
                    "content": function_result
                })
                
                # Get final response with function result (NON-STREAMING)
                final_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_message}
                    ] + self.conversation_history,
                    stream=False  # Explicitly disable streaming
                )
                
                assistant_message = final_response.choices[0].message.content
            else:
                assistant_message = message.content
            
            # Add assistant response to conversation history
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return "Sorry, I encountered an error processing your request."
    
    async def run_conversation(self):
        """Run the main voice conversation loop."""
        print("Non-streaming Voice Agent started!")
        print("Press Enter to start recording, or type 'quit' to exit")
        
        while True:
            user_input = input("\nPress Enter to record or type 'quit' to exit: ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            if user_input == "":  # User pressed Enter, so record audio
                try:
                    print("Recording audio...")
                    # Record audio using the same method as the original
                    audio_data = record_audio()
                    
                    if len(audio_data) == 0:
                        print("No audio recorded. Please try again.")
                        continue
                    
                    print("Processing audio...")
                    
                    # Convert to text
                    user_text = self.audio_to_text(audio_data)
                    if not user_text:
                        print("Could not understand audio. Please try again.")
                        continue
                    
                    print(f"[debug] Transcription: {user_text}")
                    
                except Exception as e:
                    print(f"Error with audio recording: {e}")
                    continue
            else:
                continue
            
            # Get AI response
            print("Getting AI response...")
            ai_response = await self.get_ai_response(user_text)
            print(f"Assistant: {ai_response}")
            
            # Convert response to speech and play it
            try:
                print("Converting to speech...")
                audio_bytes = self.text_to_speech(ai_response)
                if audio_bytes:
                    print("Playing response...")
                    self.play_audio_bytes(audio_bytes)
                else:
                    print("Could not generate speech.")
            except Exception as e:
                print(f"Error with text-to-speech: {e}")


async def main():
    agent = NonStreamingVoiceAgent()
    await agent.run_conversation()


if __name__ == "__main__":
    asyncio.run(main())
