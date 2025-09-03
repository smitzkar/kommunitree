#!/usr/bin/env python3
"""
Text-based version of the voice agent for testing functionality without audio dependencies.
This allows you to test the AI agent logic without dealing with WSL audio issues.
"""

import asyncio
import random
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TextBasedAgent:
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
    
    async def get_ai_response(self, user_input: str, language_hint: str = None) -> str:
        """Get response from OpenAI with function calling support."""
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
        system_message = "You're a helpful assistant. Be polite and concise. If the user asks about weather, use the get_weather function."
        if language_hint == "spanish" or "spanish" in user_input.lower() or any(word in user_input.lower() for word in ["hola", "buenos", "gracias", "español"]):
            system_message = "You're a helpful assistant that speaks Spanish. Be polite and concise. Respond in Spanish. If the user asks about weather, use the get_weather function."
        
        try:
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message}
                ] + self.conversation_history,
                functions=functions,
                function_call="auto"
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
                
                # Get final response with function result
                final_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_message}
                    ] + self.conversation_history,
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
        """Run the main conversation loop."""
        print("Text-based Agent started!")
        print("Type your messages and get AI responses (including weather function calls)")
        print("Try asking about weather in different cities!")
        print("Try speaking in Spanish to see language detection!")
        print("Type 'quit' to exit\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            if not user_input:
                continue
            
            # Get AI response
            ai_response = await self.get_ai_response(user_input)
            print(f"Assistant: {ai_response}\n")


async def main():
    agent = TextBasedAgent()
    await agent.run_conversation()


if __name__ == "__main__":
    asyncio.run(main())
