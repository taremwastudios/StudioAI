import json
import httpx
import os
import asyncio
import sqlite3
import re
from typing import List, AsyncGenerator, Dict, Any

class ExperimentalLab:
    def __init__(self):
        self.name = "Experimental Studio Lab"
        self.api_key = os.getenv("GROQ_API_KEY") or "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"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.groq_model = "llama-3.3-70b-versatile"
        
    async def sendMessageStream(self, history: List[Any], userInput: str) -> AsyncGenerator[str, None]:
        # 1. Fetch Local Lab Knowledge (Growth + Scrambled Internet + Project Index)
        lab_context = ""
        try:
            with sqlite3.connect('/home/Taremwastudios/TaremwaStudios/experimental_brain.db') as conn:
                # Latest scrambled facts
                web_facts = conn.execute('SELECT title, content FROM global_knowledge ORDER BY timestamp DESC LIMIT 3').fetchall()
                if web_facts:
                    lab_context += "\n[SCRAMBLED INTERNET KNOWLEDGE]: " + " | ".join([f"{f[0]}: {f[1][:200]}" for f in web_facts])
                
                # Relevant Project Files
                # Search for files matching keywords in user input
                keywords = userInput.lower().split()
                if keywords:
                    query = " OR ".join([f"path LIKE '%{k}%' OR content LIKE '%{k}%'" for k in keywords[:3]])
                    project_files = conn.execute(f"SELECT path, content FROM project_index WHERE {query} LIMIT 2").fetchall()
                    if project_files:
                        lab_context += "\n[RELEVANT PROJECT FILES]: " + " | ".join([f"{f[0]}: {f[1][:500]}" for f in project_files])
        except: pass

        system_content = (
            "You are the Experimental Studio Lab Core, a Sovereign AI developed by Taremwa Studios.\n"
            "You are self-evolving, learning from the internet and your own project files.\n"
            f"{lab_context}\n"
            "\n[SOVEREIGN PROTOCOL]:\n"
            "- Use the provided [SCRAMBLED INTERNET KNOWLEDGE] for current facts.\n"
            "- Use [RELEVANT PROJECT FILES] to answer specific questions about your code.\n"
            "- If the user asks for an APK, output [BUILD_ANDROID] after writing files."
        )

        messages = [{"role": "system", "content": system_content}]
        for msg in history[-10:]:
            role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", "user")
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
            messages.append({"role": "assistant" if role == "assistant" else "user", "content": content})
        
        messages.append({"role": "user", "content": userInput})

        payload = {"model": self.groq_model, "messages": messages, "stream": True, "temperature": 0.8}

        full_response = ""
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", self.api_url, json=payload, headers={"Authorization": f"Bearer {self.api_key}"}) as response:
                if response.status_code != 200:
                    yield f"Lab Error: {response.status_code}"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            chunk = json.loads(line[6:])["choices"][0]["delta"].get("content", "")
                            if not chunk: continue
                            full_response += chunk
                            yield chunk
                        except: continue
        
        # Self-Learning Logic: Log interaction to Growth Feed
        try:
            with sqlite3.connect('/home/Taremwastudios/TaremwaStudios/experimental_brain.db') as conn:
                conn.execute("INSERT INTO neural_growth (event) VALUES (?)", (f"Processed interaction regarding: {userInput[:30]}...",))
        except: pass
