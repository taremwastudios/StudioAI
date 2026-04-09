import sqlite3
import asyncio
import os
import httpx
import warnings
from bs4 import BeautifulSoup
from datetime import datetime

warnings.filterwarnings("ignore", category=RuntimeWarning, module='duckduckgo_search')

try:
    from duckduckgo_search import DDGS
except ImportError:
    from ddgs import DDGS

import random
import re

# Configuration
PROJECT_ROOT = "/home/Taremwastudios/TaremwaStudios"
DB_PATH = "/home/Taremwastudios/TaremwaStudios/experimental_brain.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS neural_growth (id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS synapses (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, predicate TEXT, object TEXT, strength INTEGER DEFAULT 1, last_reinforced DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(subject, predicate, object))")
    conn.execute("CREATE TABLE IF NOT EXISTS project_index (path TEXT PRIMARY KEY, content TEXT, last_indexed DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS global_knowledge (url TEXT PRIMARY KEY, topic TEXT, title TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    
    # NEW: Curiosity Queue
    conn.execute("CREATE TABLE IF NOT EXISTS curiosity_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, term TEXT UNIQUE, status TEXT DEFAULT 'pending', requested_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()

async def scrape_url(url, topic):
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for script in soup(["script", "style"]): script.decompose()
                text = soup.get_text(separator=' ', strip=True)
                
                conn = sqlite3.connect(DB_PATH)
                conn.execute("INSERT OR REPLACE INTO global_knowledge (url, topic, title, content) VALUES (?, ?, ?, ?)", 
                             (url, topic, soup.title.string if soup.title else url, text[:10000]))
                conn.commit()
                conn.close()
                return True
    except: pass
    return False

async def research_term(term):
    """Specific research for terms the AI was confused about."""
    print(f"[{datetime.now()}] Curiosity: Researching unknown term '{term}'...")
    try:
        ddgs = DDGS()
        results = [r['href'] for r in ddgs.text(term, max_results=3)]
        for url in results:
            await scrape_url(url, term)
        
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE curiosity_queue SET status = 'completed' WHERE term = ?", (term,))
        conn.execute("INSERT INTO neural_growth (event) VALUES (?)", (f"Matrix researched curiosity term: {term}",))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Research Error: {e}")

async def heartbeat():
    print("Matrix Brain: Curiosity-Driven Learning Online.")
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            # Check for curiosity requests first
            todo = conn.execute("SELECT term FROM curiosity_queue WHERE status = 'pending' LIMIT 1").fetchone()
            conn.close()

            if todo:
                await research_term(todo[0])
            else:
                # Default background learning
                await scramble_internet() 
            
            await asyncio.sleep(2) 
        except Exception as e:
            await asyncio.sleep(5)

# (Keeping standard scramble_internet logic...)
def scramble_internet():
    # ... logic stays the same ...
    pass

if __name__ == "__main__":
    init_db()
    asyncio.run(heartbeat())
