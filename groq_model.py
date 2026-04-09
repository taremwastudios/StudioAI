import json
import httpx
import os
import asyncio
from typing import List, AsyncGenerator
from gamicode_types import Message
from search_tool import web_search

class GroqModel:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    async def sendMessageStream(self, history: List[Message], userInput: str, system_prompt: str) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield "Error: GROQ_API_KEY is missing."
            return

        # --- SEARCH TRIGGER ---
        search_terms = ["search", "find", "latest", "news", "who is", "what is the price of", "current", "research"]
        web_context = ""
        if any(term in userInput.lower() for term in search_terms):
            yield "[Studio Intelligence is searching the web...]\n\n"
            # Perform search in a thread to not block async
            web_context = await asyncio.to_thread(web_search, userInput)
            yield "[Found results from DuckDuckGo. Processing...]\n\n"

        modified_system_prompt = system_prompt
        if web_context:
            modified_system_prompt += f"\n\nCURRENT WEB SEARCH RESULTS:\n{web_context}\n\nUse the above information to provide a factual, up-to-date answer."

        messages = [{"role": "system", "content": modified_system_prompt}]
        for msg in history[-10:]:
            role = "assistant" if msg.role == "assistant" else "user"
            messages.append({"role": role, "content": msg.content})
        
        messages.append({"role": "user", "content": userInput})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "stream": True,
            "temperature": 0.2
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", self.api_url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        yield f"Groq Error: {response.status_code}"
                        return
                        
                    async for line in response.aiter_lines():
                        if not line or line == "data: [DONE]": continue
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                chunk = data["choices"][0]["delta"].get("content", "")
                                if chunk:
                                    yield chunk
                            except Exception:
                                continue
        except Exception as e:
            yield f"Connection Error: {str(e)}"