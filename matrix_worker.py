import sqlite3
import json
import time
import os
import subprocess
import secrets
import asyncio
from datetime import datetime
from scrambler import run_scrambler
from godot_oracle import PROJECT_GODOT_TEMPLATE, TSCN_2D_FOUNDATION, GD_PLAYER_SCRIPT, EXPORT_PRESETS_TEMPLATE

DB_PATH = "/home/Taremwastudios/TaremwaStudios/matrix_mel.db"
GODOT_BIN = "/home/Taremwastudios/TaremwaStudios/godot"

def get_db_conn():
    # Helper to handle SQLite locking with retries
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute("PRAGMA journal_mode=WAL") # Enable write-ahead logging
    return conn

def get_system_metrics():
    try:
        with open("/proc/loadavg", "r") as f:
            load = float(f.read().split()[0])
        with open("/proc/meminfo", "r") as f:
            mem = f.readlines()
            free = int([x for x in mem if "MemAvailable" in x][0].split()[1]) // 1024
    except:
        load, free = 0.0, 1024
    return load, free

def update_pulse(load, free):
    try:
        conn = get_db_conn()
        conn.execute("INSERT OR REPLACE INTO worker_status (worker_id, load, ram_free, last_pulse) VALUES (?, ?, ?, ?)",
                     ("hand_1", load, free, datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Pulse Error: {e}", flush=True)

def update_job_step(jid, step):
    try:
        conn = get_db_conn()
        conn.execute("UPDATE job_queue SET last_step = ? WHERE id = ?", (step, jid))
        conn.commit()
        conn.close()
    except: pass

async def process_tasks():
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, task_type, payload FROM job_queue WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1")
        job = cursor.fetchone()
        
        if not job:
            conn.close()
            return False

        job_id, task_type, payload = job
        payload_data = json.loads(payload)

        # Start job
        print(f"[{datetime.now()}] Picking up task: {task_type} (ID: {job_id})", flush=True)
        cursor.execute("UPDATE job_queue SET status = 'running', started_at = ? WHERE id = ?", (datetime.now(), job_id))
        conn.commit()
        
        result = {"status": "error", "output": "General Failure"}
        
        try:
            if task_type == "scramble":
                prompt = payload_data.get("prompt", "")
                api_key = payload_data.get("api_key", "")
                print(f"[{datetime.now()}] Starting Scramble for: {prompt}", flush=True)
                result = await run_scrambler(prompt, api_key)
            elif task_type == "android_export":
                base_path = os.path.abspath(payload_data.get("project_path"))
                game_name = payload_data.get("game_name", "Game").replace(" ", "_")
                game_name_safe = game_name.lower().replace("_", "")
                export_dir = "/home/Taremwastudios/TaremwaStudios/gemi-engine-app/static/builds"
                os.makedirs(export_dir, exist_ok=True)
                export_path = os.path.join(export_dir, f"{game_name}.apk")
                
                # Set Godot environment variables
                os.environ["GODOT_ANDROID_SDK_PATH"] = "/usr/lib/android-sdk"
                
                print(f"[{datetime.now()}] Forging Android APK: {game_name}", flush=True)
                update_job_step(job_id, "Searching for project root...")
                
                # Autonomous Root Discovery: Find where project.godot actually is
                project_path = base_path
                for root, dirs, files in os.walk(base_path):
                    if "project.godot" in files:
                        project_path = root
                        break
                
                # --- AUTO-INITIALIZE PROJECT IF MISSING ---
                if not os.path.exists(f"{project_path}/project.godot"):
                    update_job_step(job_id, "Initializing new Godot project...")
                    os.makedirs(project_path, exist_ok=True)
                    with open(f"{project_path}/project.godot", "w") as f:
                        f.write(PROJECT_GODOT_TEMPLATE.format(game_name=game_name))
                
                # --- ALWAYS ENSURE EXPORT PRESETS ---
                update_job_step(job_id, "Configuring Export Presets...")
                with open(f"{project_path}/export_presets.cfg", "w") as f:
                    f.write(EXPORT_PRESETS_TEMPLATE.format(
                        game_name=game_name, 
                        game_name_safe=game_name_safe,
                        export_path=export_path
                    ))
                
                update_job_step(job_id, "Godot: Initializing Export Engine...")
                # Command: godot --headless --path [project] --export-debug "Android" [output_apk]
                cmd = [
                    GODOT_BIN, "--headless", "--path", project_path,
                    "--export-debug", "Android", export_path
                ]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                
                # Stream logs to the database status
                for line in process.stdout:
                    line = line.strip()
                    if not line: continue
                    # Filter for meaningful steps to show the user
                    if any(kw in line for kw in ["Exporting", "Packing", "Signing", "Compiling", "Building"]):
                        # Truncate long paths for the UI
                        display_line = (line[:50] + '..') if len(line) > 50 else line
                        update_job_step(job_id, f"Godot: {display_line}")
                
                process.wait()
                
                if process.returncode == 0:
                    update_job_step(job_id, "Build Complete!")
                    result = {
                        "status": "success", 
                        "url": f"/static/builds/{game_name}.apk",
                        "game_name": game_name
                    }
                else:
                    update_job_step(job_id, "Build Failed.")
            elif task_type == "arcade_export":
                project_path = payload_data.get("project_path")
                game_name = payload_data.get("game_name", "Game")
                export_path = f"/home/Taremwastudios/TaremwaStudios/gemi-engine-app/static/arcade/{game_name}"
                os.makedirs(export_path, exist_ok=True)
                
                print(f"[{datetime.now()}] Exporting Arcade Build: {game_name}", flush=True)
                
                # Command: godot --headless --path [project] --export-release "Web" [output_html]
                # Note: We assume the Godot binary is available as 'godot' or in a known location
                cmd = [
                    GODOT_BIN, "--headless", "--path", project_path,
                    "--export-release", "Web", f"{export_path}/index.html"
                ]
                
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                if process.returncode == 0:
                    result = {
                        "status": "success", 
                        "url": f"/static/arcade/{game_name}/index.html",
                        "game_name": game_name
                    }
                else:
                    result = {
                        "status": "error", 
                        "message": "Godot Export Failed",
                        "stderr": process.stderr
                    }
            else:
                result = {"error": f"Unsupported task: {task_type}"}

            cursor.execute("UPDATE job_queue SET status = 'completed', result = ?, completed_at = ? WHERE id = ?",
                         (json.dumps(result), datetime.now(), job_id))
        except Exception as e:
            print(f"Task Execution Error: {e}", flush=True)
            cursor.execute("UPDATE job_queue SET status = 'failed', result = ? WHERE id = ?",
                         (json.dumps({"error": str(e)}), job_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Loop Error: {e}", flush=True)
        return False

async def main_loop():
    print(f"Matrix Worker (Hand 1) Hardened. Pulse active.", flush=True)
    while True:
        l, f = get_system_metrics()
        update_pulse(l, f)
        # Check for tasks
        found_task = await process_tasks()
        if not found_task:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main_loop())