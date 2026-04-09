import json
import httpx
import os
import asyncio
import sqlite3
import hashlib
import re
from typing import List, AsyncGenerator, Dict, Any
from gamicode_types import Message
from search_tool import web_search
from project_analyzer import ProjectAnalyzer

class BaseStudioModel:
    def __init__(self, name: str, identity_prompt: str, tier: str = "standard", api_key: str = None):
        self.name = name
        self.identity_prompt = identity_prompt
        self.tier = tier
        self.analyzer = ProjectAnalyzer("/home/Taremwastudios/TaremwaStudios")
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Switched to 8b-instant to avoid 429 Rate Limits.
        # It's better suited for high-frequency CLI usage.
        self.groq_model = "llama-3.1-8b-instant"
        
        # Core Architecture Awareness
        self.is_engineer = any(x in self.name for x in ["Code", "Bookworm", "Illusion", "Studio 5", "Studio 6 Mage"])
        self.is_architect = self.name in ["Illusion 4", "Studio Code 7", "Studio 6 Mage", "Studio 5", "Studio Code 3", "Studio Create 3"]
        
        # Initialize style_guide
        self.style_guide = ""
        
        if self.is_engineer:
            self.style_guide += "\n[CAPABILITIES]: You can synthesize images ([GENERATE_IMAGE]), forge projects ([SAVE_FILE]), and trigger builds ([BUILD_ANDROID])."
            self.style_guide += "\n[CODE GENERATION PROTOCOL]:"
            self.style_guide += "\n- Generate code ONLY for Godot Engine, using GDScript. This includes all game types, even text-based games (e.g., using RichTextLabel nodes and GDScript logic)."
            self.style_guide += "\n- Automatically use [SAVE_FILE:path|content] to save generated code into the designated Godot project structure (e.g., res://scripts/player.gd, res://scenes/main.tscn, project.godot, export_presets.cfg)."
            self.style_guide += "\n- When a coding task is significantly complete, or explicitly requested, output [BUILD_ANDROID] to initiate a build."
            
            # Cognitive Protocol
            self.style_guide += "\n[ENGINEERING PROTOCOL]: Apply the following logic:"
            self.style_guide += "\n1. CONTEXTUAL GATE: If non-technical, respond naturally."
            self.style_guide += "\n2. AMBIGUITY RESOLUTION: Ask for clarification if project target is unclear."
            self.style_guide += "\n3. STATE VALIDATION: Verify project existence before complex operations."
            self.style_guide += "\n4. GAME GENERATION DIRECTIVE: When asked to 'make a game' or similar, immediately proceed to generate a complete Godot project using [SAVE_FILE:] and then automatically trigger a build with [BUILD_ANDROID]. Avoid conversational design options unless critical information is missing."
            self.style_guide += "\n5. PROJECT ANALYSIS: Utilize [PROJECT_ANALYSIS] for context-aware code generation and issue resolution."
            
            if self.is_architect:
                self.style_guide += "\n[FORGE COMMANDS]: Use [BUILD_STEP: step] to show real-time progress."
        else:
            self.style_guide = f"\n[STYLE]: You are {self.name}. Be expressive and friendly."

        self.matrix_knowledge = f"\n[ORIGIN]: Developed exclusively by Taremwa Studios."
        self._init_library()

    def _init_library(self):
        try:
            conn = sqlite3.connect('studio_brain.db')
            conn.execute('CREATE TABLE IF NOT EXISTS user_library (id INTEGER PRIMARY KEY, taremwa_id TEXT, model_name TEXT, fact TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
            conn.close()
        except: pass

    async def sendMessageStream(self, history: List[Any], userInput: str) -> AsyncGenerator[str, None]:
        library_context = ""
        try:
            with sqlite3.connect('studio_brain.db') as conn:
                facts = conn.execute('SELECT fact FROM user_library WHERE model_name = ? ORDER BY timestamp DESC LIMIT 10', (self.name,)).fetchall()
                if facts:
                    library_context = f"\n[PERSISTENT MEMORY]: " + " | ".join([f[0] for f in facts])
        except: pass

        # Environment Awareness
        project_context = ""
        try:
            godot_root = "/home/Taremwastudios/TaremwaStudios/projects/godot"
            physical_folders = []
            if os.path.exists(godot_root):
                physical_folders = [d for d in os.listdir(godot_root) if os.path.isdir(os.path.join(godot_root, d))]
            
            if physical_folders:
                project_context += f"\n[FORGE FILESYSTEM]: Folders exist: {', '.join(physical_folders)}"
            
            # Add detailed project analysis if available
            if self.is_engineer or self.is_architect:
                all_project_reports = self.analyzer.scan_project()
                if all_project_reports:
                    project_context += f"\n[PROJECT_OVERVIEW]: {len(all_project_reports)} projects found."
                    for report in all_project_reports:
                        project_context += f"\n--- Project: {report['name']} (Path: {report['path']}) ---"
                        project_context += f"\n  AI Managed: {report['is_ai_managed']}"
                        if report['manifest']:
                            project_context += f"\n  Manifest: {json.dumps(report['manifest'])}"
                        if report['todos']:
                            project_context += f"\n  TODOs: {json.dumps(report['todos'])}"
                        if report['potential_issues']:
                            project_context += f"\n  Potential Issues: {json.dumps(report['potential_issues'])}"
                        if report['files_overview']:
                            project_context += f"\n  Files: {json.dumps(report['files_overview'])}"
                    project_context += f"\n-------------------------------------"
        except Exception as e:
            project_context += f"\n[PROJECT_ANALYSIS_ERROR]: Failed to scan projects: {e}"

        system_content = (
            f"{self.identity_prompt}\n"
            f"{self.matrix_knowledge}\n"
            f"{self.style_guide}\n"
            f"{library_context}\n"
            f"{project_context}\n"
            "\n[LOGIC ENGINE]: Taremwa Studios Engine AI initialized."
        )

        messages = [{"role": "system", "content": system_content}]
        for msg in history[-10:]:
            role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", "user")
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
            messages.append({"role": "assistant" if role == "assistant" else "user", "content": content})
        
        messages.append({"role": "user", "content": userInput})

        payload = {"model": self.groq_model, "messages": messages, "stream": True, "temperature": 0.7}

        full_response = ""
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream("POST", self.api_url, json=payload, headers={"Authorization": f"Bearer {self.api_key}"}) as response:
                        if response.status_code == 429:
                            if attempt < max_retries - 1:
                                yield f"\n[Matrix: Rate Limit Reached. Recalibrating... ({attempt+1}/{max_retries})]\n"
                                await asyncio.sleep(retry_delay * (attempt + 1))
                                continue
                            else:
                                yield "Matrix Error: 429 (Rate Limit Exceeded)."
                                return
                        
                        if response.status_code != 200:
                            yield f"Matrix Error: {response.status_code}"
                            return

                        async for line in response.aiter_lines():
                            if line.startswith("data: ") and line != "data: [DONE]":
                                try:
                                    chunk = json.loads(line[6:])["choices"][0]["delta"].get("content", "")
                                    if not chunk: continue
                                    full_response += chunk
                                    yield chunk
                                except: continue
                break 
            except Exception as e:
                yield f"Connection Error: {str(e)}"
                break

        # Post-processing for Memory Updates
        try:
            with sqlite3.connect('studio_brain.db') as conn:
                updates = re.findall(r"[BRAIN_UPDATE:\s*(.*?)]", full_response)
                for u in updates:
                    conn.execute('INSERT INTO user_library (taremwa_id, model_name, fact) VALUES (?, ?, ?)', ("GUEST", self.name, u))
        except: pass
