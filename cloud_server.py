import os
import random
import string
import logging
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cloud_server")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
users_db = {}
mail_store = {}
wallets = {}
active_codes = {}

class RegisterRequest(BaseModel):
    username: str
    password: str
    real_names: str
    country: str
    address: str
    real_email: EmailStr

class LoginRequest(BaseModel):
    username: Optional[str] = None
    taremwa_id: Optional[str] = None
    password: Optional[str] = None

@app.get("/")
@app.get("/portal.html")
async def root():
    logger.info("Serving portal.html")
    file_path = os.path.join(os.path.dirname(__file__), "portal.html")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/html")
    logger.error(f"File not found at {file_path}")
    return HTMLResponse("<h1>Portal Not Found</h1>", status_code=404)

@app.post("/register")
async def register(req: RegisterRequest):
    if req.username in users_db:
        raise HTTPException(status_code=400, detail="Username taken")
    t_id = f"T-03{''.join(random.choices(string.digits, k=8))}"
    users_db[req.username] = {**req.dict(), "taremwa_id": t_id, "studio_inbox": f"{req.username}@taremwastudios.com"}
    wallets[req.username] = 10.0
    mail_store[req.username] = [
        {"sender": "ai@taremwastudios.com", "subject": "Welcome", "body": "Welcome to the AI Universe", "timestamp": datetime.now().isoformat()},
        {"sender": "billing@taremwastudios.com", "subject": "Credit", "body": "Free $10 added", "timestamp": datetime.now().isoformat()}
    ]
    return {"status": "success", "taremwa_id": t_id}

@app.post("/login")
async def login(req: LoginRequest):
    user = users_db.get(req.username) if req.username else next((u for u in users_db.values() if u["taremwa_id"] == req.taremwa_id), None)
    if not user or (req.password and user["password"] != req.password):
        raise HTTPException(status_code=401, detail="Invalid")
    return user

@app.get("/claim-code/{username}")
async def claim(username: str):
    code = "".join(random.choices(string.digits, k=6))
    active_codes[code] = username
    return {"code": code}

@app.post("/verify-code")
async def verify(code: str = Body(..., embed=True)):
    username = active_codes.get(code)
    if not username: raise HTTPException(status_code=401)
    del active_codes[code]
    return users_db[username]

@app.get("/inbox/{username}")
async def get_inbox(username: str): return {"messages": mail_store.get(username, [])}

@app.get("/wallet/{username}")
async def get_wallet(username: str): return {"balance": wallets.get(username, 0.0)}

@app.post("/publish-model")
async def publish_model(username: str = Body(..., embed=True), cost: float = Body(..., embed=True)):
    current_balance = wallets.get(username, 0.0)
    if current_balance < cost:
        raise HTTPException(status_code=402, detail="Insufficient funds in Taremwa Wallet.")
    
    wallets[username] -= cost
    
    mail_store[username].append({
        "sender": "billing@taremwastudios.com",
        "subject": "Studio Lab: Core Published",
        "body": f"Successfully debited ${cost} for core publishing. Your hard-copy is now ready for deployment.",
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "success", "new_balance": wallets[username]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
