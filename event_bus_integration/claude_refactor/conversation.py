
# ==========================
# conversation.py
# ==========================
"""
conversation.py - ai conversation management
handles conversation flow and openai integration
"""

import asyncio
from typing import Optional
from datetime import datetime
import logging

from config import config
from events import *
from event_bus import EventBus
from audio_manager import AudioManager

#MARK: ConversationManager
class ConversationManager:
    """
    manages ai conversation flow
    handles greeting, responses, and goodbye
    """
    def __init__(self, bus: EventBus, audio_manager: AudioManager):
        self.bus = bus
        self.audio = audio_manager
        self.active = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # response management
        self.immediate_response: Optional[str] = None
        self.followup_response: Optional[str] = None
        self.last_interaction = datetime.now()
        
        # subscribe to events
        self.bus.subscribe(ConversationStartEvent, self._handle_start_request)
        self.bus.subscribe(ConversationEndEvent, self._handle_end)
    
    # Removed _handle_presence; presence is now handled by SystemController
    
    def _handle_start_request(self, event: ConversationStartEvent):
        """explicit request to start conversation"""
        if not self.active:
            asyncio.create_task(self.start_conversation())
    
    def _handle_end(self, event: ConversationEndEvent):
        """conversation ending"""
        self.active = False
        self.logger.info("conversation ended")
    
    async def start_conversation(self):
        """
        begin a new conversation
        greet user and start listening
        """
        if self.active:
            return  # already in conversation
        
        self.active = True
        self.bus.publish(ConversationStartEvent())
        
        # greet user
        await self.audio.speak(config.greeting_message)
        
        # start conversation loop
        await self._conversation_loop()
    
    async def _conversation_loop(self):
        """
        main conversation loop
        listens for input and responds
        """
        no_response_count = 0
        
        while self.active:
            # listen for user
            user_input = await self.audio.listen_for_speech()
            
            if user_input:
                # got input - process it
                no_response_count = 0
                await self._process_user_input(user_input)
            else:
                # no input - check if user still there
                no_response_count += 1
                
                if no_response_count == 1:
                    # first timeout
                    await self.audio.speak(config.check_presence_message)
                elif no_response_count >= config.max_silence_count:
                    # too many timeouts - end conversation
                    await self.audio.speak(config.goodbye_message)
                    self.bus.publish(ConversationEndEvent())
                    break
            
            await asyncio.sleep(1)
    
    async def _process_user_input(self, text: str):
        """
        process what user said
        generate and speak response
        """
        self.logger.info(f"processing: {text}")
        
        # generate responses (would use openai here)
        responses = await self._generate_responses(text)
        
        if responses:
            self.immediate_response = responses.get('immediate')
            self.followup_response = responses.get('followup')
            
            # speak immediate response
            if self.immediate_response:
                await self.audio.speak(self.immediate_response)
            
            # schedule followup
            if self.followup_response:
                asyncio.create_task(self._deliver_followup())
        
        self.last_interaction = datetime.now()
    
    async def _generate_responses(self, user_input: str) -> Optional[dict]:
        """
        generate ai responses
        returns dict with 'immediate' and 'followup' responses
        """
        if config.simulate_hardware:
            # simulation - return dummy responses
            await asyncio.sleep(0.5)  # simulate api delay
            return {
                'immediate': f"I heard: {user_input[:30]}...",
                'followup': "That reminds me of something interesting..."
            }
        else:
            # real openai implementation would go here
            # response = await openai.chat.completions.create(...)
            return None
    
    async def _deliver_followup(self):
        """deliver followup response after delay"""
        await asyncio.sleep(config.followup_delay)
        
        # check if still relevant
        time_since = (datetime.now() - self.last_interaction).seconds
        if time_since >= config.followup_delay and self.followup_response and self.active:
            await self.audio.speak(self.followup_response)
            self.followup_response = None  # clear after using
