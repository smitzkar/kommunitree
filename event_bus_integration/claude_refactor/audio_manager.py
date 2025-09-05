
# ==========================
# audio_manager.py
# ==========================
"""
audio_manager.py - handles all audio i/o
provides simple interface for speech input/output
"""

import asyncio
import threading
from typing import Optional
import logging

from config import config
from events import AssistantSpeechEvent, UserSpeechEvent, InterruptAudioEvent
from event_bus import EventBus

#MARK: AudioManager
class AudioManager:
    """
    manages audio input and output
    bridges blocking audio operations with async code
    """
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.is_playing = False
        self.is_listening = False
        self.logger = logging.getLogger(self.__class__.__name__)
        # Store main event loop for thread communication
        try:
            self.main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self.logger.warning("AudioManager: No running event loop found during init; using get_event_loop().")
            self.main_loop = asyncio.get_event_loop()
            
            
        #MARK: added by copilot
        # why does it use self.bus.subscribe, instead of bus.subscribe, here? 
        # -> it doesn't really matter here, as we're still inside __init__, 
        # so bus is directly accessible, but it's just best practice to make sure it uses the correct one     
        # subscribe to speech events
        self.bus.subscribe(AssistantSpeechEvent, self._handle_assistant_speech)
        self.bus.subscribe(InterruptAudioEvent, self._handle_interrupt_audio)
        
    #MARK: NEW   
    def _handle_interrupt_audio(self, event):
        """Handle interrupt event to stop audio operations"""
        self.logger.info("InterruptAudioEvent received: stopping audio operations.")
        self.is_listening = False
        self.is_playing = False
    
    def _handle_assistant_speech(self, event: AssistantSpeechEvent):
        """handle request to speak"""
        if not self.is_playing:
            # start playback in thread
            thread = threading.Thread(
                target=self._play_audio_blocking,
                args=(event.data,)
            )
            thread.start()
    
    def _play_audio_blocking(self, text: str):
        """
        play text as speech (runs in thread)
        this would use tts api and audio hardware
        """
        self.is_playing = True
        self.logger.info(f"playing: {text}")
        
        try:
            if config.simulate_hardware:
                # simulate tts delay
                import time
                duration = len(text) * 0.05
                time.sleep(duration)
            else:
                # real tts implementation would go here
                # response = openai.audio.speech.create(...)
                # play_audio(response.content)
                pass
                
        except Exception as e:
            self.logger.error(f"error playing audio: {e}")
        finally:
            self.is_playing = False
    
    async def listen_for_speech(self, timeout: Optional[int] = None) -> Optional[str]:
        """
        listen for user speech (async)
        returns transcribed text or None if timeout/no speech
        """
        if self.is_listening:
            return None
        
        timeout = timeout or config.speech_timeout
        
        # use future to bridge thread/async
        future = asyncio.Future()
        
        def _listen_thread():
            """blocking listen operation"""
            self.is_listening = True
            self.logger.info("listening for speech...")
            try:
                if config.simulate_hardware:
                    # simulate speech recognition
                    import time
                    import random
                    time.sleep(2)
                    if random.random() > 0.3:
                        text = "Hello, how are you today?"
                    else:
                        text = None
                else:
                    # real speech recognition would go here
                    # audio = record_audio(timeout)
                    # text = openai.audio.transcribe(audio)
                    text = None
                # set result in async context using main event loop
                asyncio.run_coroutine_threadsafe(
                    self._set_future(future, text),
                    self.main_loop
                )
            except Exception as e:
                self.logger.error(f"error listening: {e}")
                asyncio.run_coroutine_threadsafe(
                    self._set_future(future, None),
                    self.main_loop
                )
            finally:
                self.is_listening = False
        
        # start listening in thread
        thread = threading.Thread(target=_listen_thread)
        thread.start()
        
        # wait for result
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            if result:
                self.bus.publish(UserSpeechEvent(result))
            return result
        except asyncio.TimeoutError:
            self.logger.info("listen timeout")
            return None
    
    async def _set_future(self, future: asyncio.Future, result):
        """helper to set future result from thread"""
        if not future.done():
            future.set_result(result)
    
    # simple public interface
    async def speak(self, text: str):
        """
        speak text (async wrapper)
        waits for speech to complete
        """
        self.bus.publish(AssistantSpeechEvent(text))
        
        # wait for playback to finish
        while self.is_playing:
            await asyncio.sleep(0.1)
    
    def is_speaking(self) -> bool:
        """check if currently speaking"""
        return self.is_playing
