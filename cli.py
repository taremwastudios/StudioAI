#!/usr/bin/env python3
import asyncio
import os
import sys
import datetime
import uuid
import re
import sqlite3
import json
import secrets
from typing import List, Optional

# Attempt to load .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except ImportError:
    pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Model Registry ---
MODEL_REGISTRY = {}

# Import project modules
try:
    from gamicode_types import Message
    from models.speedy import Speedy 
    from models.sovereign_core import SovereignEngine
    from models.studio_code_7 import StudioCode7
    from models.illusion_4 import Illusion4
    from models.studio_5 import Studio5
    from models.chani_25_pro import Chani25Pro
    
    MODEL_REGISTRY = {
        "Speedy": Speedy,
        "Studio Code 7": StudioCode7,
        "Illusion 4": Illusion4,
        "Studio 5": Studio5,
        "Chani 2.5 Pro": Chani25Pro,
    }
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to load models. {e}")
    sys.exit(1)

# --- ANSI Colors ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GREY = '\033[90m'

def print_banner():
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("   _____ __            ___          ________    ____")
    print("  / ___// /___  ______/ (_)___     / ____/ /   /  _/")
    print("  \__ \/ __/ / / / __  / / __ \   / /   / /    / /  ")
    print(" ___/ / /_/ /_/ / /_/ / / /_/ /  / /___/ /____/ /   ")
    print(f"/____/\__/\__,_/\__,_/_/\____/   \____/_____/___/   ")
    print(f"{Colors.ENDC}")
    print(f"{Colors.BLUE}   » Taremwa Studios Intelligence Interface «{Colors.ENDC}")
    print(f"{Colors.GREY}   Type '/help' for commands.{Colors.ENDC}\n")

def load_model_safe(model_name):
    try:
        if model_name not in MODEL_REGISTRY:
            return None, f"Model '{model_name}' not found."
        model_class = MODEL_REGISTRY[model_name]
        model = model_class()
        
        # Apply CLI specific overrides to Groq-based models
        if hasattr(model, 'style_guide'):
            model.style_guide += (
                "\n\n[INTERFACE CONSTRAINTS]:\n"
                "- This is a TERMINAL interface.\n"
                "- Image generation is DISABLED.\n"
                "- File creation ([SAVE_FILE]) and Builds ([BUILD_ANDROID]) are ENABLED."
            )
        return model, None
    except Exception as e:
        return None, str(e)

async def spinner_task(stop_event, label="Thinking..."):
    chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{Colors.WARNING}{chars[i]} {label}{Colors.ENDC}")
        sys.stdout.flush()
        await asyncio.sleep(0.1)
        i = (i + 1) % len(chars)
    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.flush()

def save_file_locally(path, content):
    try:
        base_dir = "/home/Taremwastudios/TaremwaStudios/projects/godot/Forge"
        full_path = os.path.join(base_dir, path.strip().lstrip('/'))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)
        print(f"\n{Colors.GREEN}>> File Saved: {full_path}{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}>> Error Saving File: {e}{Colors.ENDC}")

async def monitor_build_job(jid):
    db_path = "/home/Taremwastudios/TaremwaStudios/matrix_mel.db"
    print(f"{Colors.WARNING}>> Monitoring Forge Job: {jid}{Colors.ENDC}")
    last_step = ""
    while True:
        try:
            with sqlite3.connect(db_path) as conn:
                job = conn.execute("SELECT status, last_step, result FROM job_queue WHERE id = ?", (jid,)).fetchone()
            if not job: break
            status, step, result = job
            if step and step != last_step:
                print(f"{Colors.BLUE}   [FORGE]: {step}{Colors.ENDC}")
                last_step = step
            if status == 'completed':
                res_data = json.loads(result) if result else {}
                apk_name = res_data.get("game_name", "Forge")
                apk_path = f"/home/Taremwastudios/TaremwaStudios/gemi-engine-app/static/builds/{apk_name}.apk"
                print(f"\n{Colors.GREEN}{Colors.BOLD}✅ FORGE COMPLETE!{Colors.ENDC}")
                print(f"{Colors.GREEN}📦 APK LOCATION: {Colors.UNDERLINE}{apk_path}{Colors.ENDC}")
                break
            elif status == 'failed':
                print(f"\n{Colors.FAIL}❌ FORGE FAILED: {result}{Colors.ENDC}")
                break
            await asyncio.sleep(2)
        except Exception as e:
            print(f"{Colors.FAIL}Monitor Error: {e}{Colors.ENDC}")
            break

def teach_lesson(subject, predicate, object_val):
    try:
        db_path = "/home/Taremwastudios/TaremwaStudios/experimental_brain.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                INSERT INTO synapses (subject, predicate, object) VALUES (?, ?, ?)
                ON CONFLICT(subject, predicate, object) DO UPDATE SET strength = strength + 1
            """, (subject.lower(), predicate.lower(), object_val.lower()))
        print(f"{Colors.GREEN}>> Lesson Recorded: {subject} {predicate} {object_val}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}>> Learning Error: {e}{Colors.ENDC}")

async def main():
    print_banner()
    
    current_model_name = "Speedy"
    current_model, err = load_model_safe(current_model_name)
    if err:
        print(f"{Colors.FAIL}Init Error: {err}{Colors.ENDC}")
        return

    history: List[dict] = []
    api_key = os.getenv("GROQ_API_KEY")
    
    print(f"{Colors.GREEN}System Online. Active Core: {Colors.BOLD}{current_model_name}{Colors.ENDC}")

    while True:
        try:
            print(f"{Colors.BLUE}┌──[{Colors.BOLD}{current_model_name}{Colors.ENDC}{Colors.BLUE}]──────────────────────────────────────────{Colors.ENDC}")
            user_input = input(f"{Colors.BLUE}└─> {Colors.ENDC}").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input: continue
        if user_input.lower() in ['/exit', '/quit']: break
        if user_input.lower() == '/clear':
            history = []; print(f"{Colors.WARNING}Context cleared.{Colors.ENDC}"); continue
        
        # Help Command
        if user_input.lower() == '/help':
            print(f"{Colors.CYAN}Commands:{Colors.ENDC}")
            print(" /model <name>       - Switch AI cores")
            print(" /lesson s | p | o   - Directly teach Speedy (e.g. /lesson Godot | is | Engine)")
            print(" /clear              - Reset conversation")
            print(" /exit               - Close interface")
            continue

        # Lesson Command
        if user_input.lower().startswith('/lesson'):
            parts = user_input.split('|')
            if len(parts) == 3:
                s = parts[0].replace('/lesson', '').strip()
                p = parts[1].strip()
                o = parts[2].strip()
                teach_lesson(s, p, o)
            else:
                print(f"{Colors.WARNING}Usage: /lesson Subject | Predicate | Object{Colors.ENDC}")
            continue

        # Model Switch
        if user_input.lower().startswith('/model'):
            parts = user_input.split(' ', 1)
            if len(parts) < 2:
                print(f"{Colors.CYAN}Cores: {', '.join(MODEL_REGISTRY.keys())}{Colors.ENDC}")
            else:
                match = next((m for m in MODEL_REGISTRY.keys() if m.lower() == parts[1].lower()), None)
                if match:
                    current_model_name = match
                    current_model, _ = load_model_safe(match)
                    print(f"{Colors.GREEN}>> Switched to {current_model_name}{Colors.ENDC}")
            continue

        full_response_text = ""
        stop_spinner = asyncio.Event()
        spinner = asyncio.create_task(spinner_task(stop_spinner))
        
        try:
            first_chunk = True
            async for chunk in current_model.sendMessageStream(history=history, userInput=user_input):
                if first_chunk:
                    stop_spinner.set(); await spinner
                    first_chunk = False
                    print(f"{Colors.CYAN}", end="", flush=True)
                print(chunk, end="", flush=True)
                full_response_text += chunk
            print(f"{Colors.ENDC}")
            
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": full_response_text})

            # Detect Files
            file_matches = re.findall(r"[SAVE_FILE:\s*(.*?)\|(.*?)]", full_response_text, re.DOTALL)
            for f_match in file_matches:
                if isinstance(f_match, tuple) and len(f_match) == 2:
                    save_file_locally(f_match[0], f_match[1])
            
            # Detect Build
            if "[BUILD_ANDROID]" in full_response_text:
                db_path = "/home/Taremwastudios/TaremwaStudios/matrix_mel.db"
                jid = secrets.token_hex(8)
                payload = {"project_path": "/home/Taremwastudios/TaremwaStudios/projects/godot/Forge", "game_name": "Forge"}
                with sqlite3.connect(db_path) as conn:
                    conn.execute("INSERT INTO job_queue (id, task_type, payload, status) VALUES (?, ?, ?, ?)", 
                                 (jid, "android_export", json.dumps(payload), "pending"))
                asyncio.create_task(monitor_build_job(jid))

        except Exception as e:
            stop_spinner.set()
            print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}")
        finally:
            if not stop_spinner.is_set(): stop_spinner.set()

if __name__ == "__main__":
    asyncio.run(main())
