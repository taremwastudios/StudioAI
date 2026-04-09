import urllib.parse
from datetime import datetime

async def run_scrambler(prompt: str, api_key: str = None):
    # Instant Synthesis Protocol - Verifying Handshake
    expected_handshake = "aR8iTAMTNhyxwNv4yNQbArJ9V"
    if api_key != expected_handshake:
        return {"error": "Handshake Failed"}

    print(f"[{datetime.now()}] SCRAMBLER: Instant Link Generated for {prompt}", flush=True)
    
    encoded_prompt = urllib.parse.quote(prompt)
    # Corrected Pollinations Premium URL Format
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&enhance=true&model=flux"
    
    return {"url": image_url, "engine": "Pollinations Premium (Flux)"}
