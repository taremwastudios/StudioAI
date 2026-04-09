import sqlite3
import json
import time
import os
import asyncio
import secrets
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from fastapi.responses import FileResponse

# 1. Initialize App first
app = FastAPI(title="Studio AI Matrix")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("/home/Taremwastudios/TaremwaStudios/dashboard.html")

@app.get("/dashboard.html")
async def read_dashboard():
    return FileResponse("/home/Taremwastudios/TaremwaStudios/dashboard.html")

class FileSaveRequest(BaseModel):
    project_path: str
    file_path: str
    content: str

@app.post("/save-file")
async def save_file(request: FileSaveRequest):
    try:
        # Security: Prevent escaping project directory
        clean_path = os.path.normpath(request.project_path + "/" + request.file_path)
        if not clean_path.startswith("/home/Taremwastudios/TaremwaStudios/projects/"):
             raise HTTPException(status_code=403, detail="Forbidden Path")
        
        os.makedirs(os.path.dirname(clean_path), exist_ok=True)
        with open(clean_path, "w") as f:
            f.write(request.content)
        return {"status": "success", "path": clean_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ide")
async def read_ide():
    return FileResponse("/home/Taremwastudios/TaremwaStudios/ide.html")

# 2. Database & Constants
ARCHITECTS = ["Illusion 4", "Studio Code 7", "Studio 6 Mage", "Studio 5", "Studio Code 3", "Studio Create 3", "Chani 4"]
ENGINEER_COSTS = {
    "Illusion 4": 7, "Studio Code 7": 6, "Studio 6 Mage": 5, 
    "Studio 5": 4, "Studio Code 3": 3, "Bookworm Antewerp": 4, 
    "Bookworm 2": 2, "Studio Mini": 1, "Studio 3T": 2
}

def init_db():
    conn = sqlite3.connect('studio_brain.db')
    conn.execute('CREATE TABLE IF NOT EXISTS user_wallet (taremwa_id TEXT PRIMARY KEY, tokens INTEGER DEFAULT 300, daily_lite_count INTEGER DEFAULT 0, last_active DATE, last_token_claim DATE)')
    conn.execute('CREATE TABLE IF NOT EXISTS studio_projects (id TEXT PRIMARY KEY, taremwa_id TEXT, model_name TEXT, project_name TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    conn.execute('CREATE TABLE IF NOT EXISTS global_chat (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

init_db()

# ... (imports remain)

@app.get("/get-global-chat")
async def get_global_chat():
    with sqlite3.connect('studio_brain.db') as conn:
        msgs = conn.execute('SELECT username, content, timestamp FROM global_chat ORDER BY timestamp DESC LIMIT 50').fetchall()
        return [{"username": m[0], "content": m[1], "time": m[2]} for m in msgs][::-1]

@app.post("/post-global-chat")
async def post_global_chat(data: dict):
    username = data.get("username", "GUEST")
    content = data.get("content", "")
    if not content: return {"error": "Empty message"}
    with sqlite3.connect('studio_brain.db') as conn:
        conn.execute('INSERT INTO global_chat (username, content) VALUES (?, ?)', (username, content))
    return {"status": "success"}

@app.get("/get-lab-growth")
async def get_lab_growth():
    try:
        with sqlite3.connect('/home/Taremwastudios/TaremwaStudios/experimental_brain.db') as conn:
            rows = conn.execute('SELECT event, timestamp FROM neural_growth ORDER BY timestamp DESC LIMIT 10').fetchall()
            return [{"text": r[0], "time": r[1]} for r in rows]
    except: return []

# 3. Model Imports
from models.studio_code_7 import StudioCode7
from models.studio_5 import Studio5
from models.studio_3t import Studio3T
from models.nano_banana_pro import Studio6Mage
from models.illusion_4 import Illusion4
from models.studio_create_3 import StudioCreate3
from models.studio_code_lite import StudioCodeLite
from models.chani_25_beta import Chani25Beta
from models.chani_25_pro import Chani25Pro
from models.chani_4 import Chani4
from models.bookworm_antewerp import BookwormAntewerp
from models.studio_mini import StudioMini
from models.studio_code_3 import StudioCode3
from models.experimental_lab import ExperimentalLab

model_registry = {
    "Studio Code 7": StudioCode7(), "Studio 5": Studio5(), "Studio 3T": Studio3T(),
    "Studio 6 Mage": Studio6Mage(), "Illusion 4": Illusion4(), "Studio Create 3": StudioCreate3(),
    "Studio Code 3": StudioCode3(), "Studio Code Lite": StudioCodeLite(),
    "Chani 2.5 Beta": Chani25Beta(), "Chani 2.5 Pro": Chani25Pro(), "Chani 4": Chani4(),
    "Bookworm Antewerp": BookwormAntewerp(), "Bookworm 2": BookwormAntewerp(),
    "Studio Mini": StudioMini(), "Experimental Studio Lab": ExperimentalLab() 
}

# 4. Endpoints
class ChatRequest(BaseModel):
    userInput: str
    username: str
    projectId: str
    isCompanion: bool
    model: str
    history: Optional[List[Dict[str, Any]]] = []

@app.get("/get-wallet")
async def get_wallet(username: str, method: str = "other"):
    today = datetime.now().date().isoformat()
    with sqlite3.connect('studio_brain.db') as conn:
        user = conn.execute('SELECT tokens, daily_lite_count, last_token_claim FROM user_wallet WHERE taremwa_id = ?', (username,)).fetchone()
        if not user:
            tokens = 1000000 # Credited for testing
            conn.execute('INSERT INTO user_wallet (taremwa_id, tokens, daily_lite_count, last_active, last_token_claim) VALUES (?, ?, 0, ?, ?)', (username, tokens, today, today))
            return {"tokens": tokens, "daily_lite_count": 0}
        tokens, lite_count, last_claim = user
        if last_claim != today:
            tokens += 1
            conn.execute('UPDATE user_wallet SET tokens = tokens + 1, last_token_claim = ? WHERE taremwa_id = ?', (today, username))
        return {"tokens": tokens, "daily_lite_count": lite_count}

@app.post("/chat")
async def chat(request: ChatRequest):
    today = datetime.now().date().isoformat()
    with sqlite3.connect('studio_brain.db') as conn:
        user = conn.execute('SELECT tokens, daily_lite_count, last_active FROM user_wallet WHERE taremwa_id = ?', (request.username,)).fetchone()
        tokens, lite_count, last_active = user if user else (1000000, 0, today)
        if request.model in ENGINEER_COSTS:
            cost = ENGINEER_COSTS[request.model]
            if tokens < cost: raise HTTPException(status_code=402, detail="Insufficient Tokens")
            conn.execute('UPDATE user_wallet SET tokens = tokens - ? WHERE taremwa_id = ?', (cost, request.username))
        else:
            if lite_count >= 100: raise HTTPException(status_code=429, detail="Limit Reached")
            conn.execute('UPDATE user_wallet SET daily_lite_count = daily_lite_count + 1 WHERE taremwa_id = ?', (request.username,))
    model_instance = model_registry.get(request.model, model_registry["Studio 5"])
    return StreamingResponse(model_instance.sendMessageStream(request.history, request.userInput), media_type="text/plain")

@app.post("/start-project")
async def start_project(data: dict):
    username, model_name, project_name = data.get("username"), data.get("model"), data.get("projectName")
    with sqlite3.connect('studio_brain.db') as conn:
        user = conn.execute('SELECT tokens FROM user_wallet WHERE taremwa_id = ?', (username,)).fetchone()
        if not user or user[0] < 300: return {"error": "Insufficient Tokens"}
        conn.execute('UPDATE user_wallet SET tokens = tokens - 300 WHERE taremwa_id = ?', (username,))
        pid = secrets.token_hex(4)
        conn.execute('INSERT INTO studio_projects (id, taremwa_id, model_name, project_name) VALUES (?, ?, ?, ?)', (pid, username, model_name, project_name))
    return {"status": "success", "message": f"Project '{project_name}' initialized."}

@app.get("/list-projects")
async def list_projects(username: str):
    with sqlite3.connect('studio_brain.db') as conn:
        projects = conn.execute('SELECT id, model_name, project_name, timestamp FROM studio_projects WHERE taremwa_id = ? ORDER BY timestamp DESC', (username,)).fetchall()
        result = {}
        for p in projects:
            if p[1] not in result: result[p[1]] = []
            result[p[1]].append({"id": p[0], "name": p[2], "date": p[3]})
        return result

def dispatch_task(t, p):
    jid = secrets.token_hex(8)
    with sqlite3.connect("/home/Taremwastudios/TaremwaStudios/matrix_mel.db") as c:
        c.execute("INSERT INTO job_queue (id, task_type, payload) VALUES (?, ?, ?)", (jid, t, json.dumps(p)))
    return jid

async def wait_for_job(jid, timeout=120):
    s = time.time()
    while time.time() - s < timeout:
        with sqlite3.connect("/home/Taremwastudios/TaremwaStudios/matrix_mel.db") as c:
            j = c.execute("SELECT status, result FROM job_queue WHERE id = ?", (jid,)).fetchone()
            if j and j[0] in ['completed', 'failed']: return json.loads(j[1])
        await asyncio.sleep(1)
    return {"error": "Timeout"}

@app.get("/generate-image")
async def generate_image(prompt: str, username: str, request: Request):
    with sqlite3.connect('studio_brain.db') as conn:
        user = conn.execute('SELECT tokens FROM user_wallet WHERE taremwa_id = ?', (username,)).fetchone()
        if not user or user[0] < 10: return {"error": "Insufficient Tokens"}
        conn.execute('UPDATE user_wallet SET tokens = tokens - 10 WHERE taremwa_id = ?', (username,))
    jid = dispatch_task("scramble", {"prompt": prompt, "api_key": "aR8iTAMTNhyxwNv4yNQbArJ9V"})
    res = await wait_for_job(jid)
    base = f"{request.url.scheme}://{request.url.netloc}"
    if "url" in res and not res["url"].startswith("http"): res["url"] = f"{base}{res['url']}"
    return res

@app.get("/job-status/{jid}")
async def get_job_status(jid: str):
    with sqlite3.connect("/home/Taremwastudios/TaremwaStudios/matrix_mel.db") as c:
        j = c.execute("SELECT status, last_step, result FROM job_queue WHERE id = ?", (jid,)).fetchone()
        if not j: return {"status": "not_found"}
        return {"status": j[0], "step": j[1], "result": json.loads(j[2]) if j[2] else None}

@app.post("/forge-apk")
async def forge_apk(data: dict):
    username = data.get("username")
    project_name = data.get("project_name")
    model_name = data.get("model_name")
    
    with sqlite3.connect('studio_brain.db') as conn:
        user = conn.execute('SELECT tokens FROM user_wallet WHERE taremwa_id = ?', (username,)).fetchone()
        if not user or user[0] < 300: return {"error": "Insufficient Tokens"}
        conn.execute('UPDATE user_wallet SET tokens = tokens - 300 WHERE taremwa_id = ?', (username,))

    project_path = f"/home/Taremwastudios/TaremwaStudios/projects/godot/{project_name.replace(' ', '_')}"
    jid = dispatch_task("android_export", {"project_path": project_path, "game_name": project_name})
    return {"status": "queued", "jid": jid}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)