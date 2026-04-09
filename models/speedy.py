from models.sovereign_core import SovereignEngine
from typing import List, AsyncGenerator, Any

class Speedy(SovereignEngine):
    def __init__(self):
        super().__init__()
        self.name = "Speedy (Sovereign Core 0.2)"

    def _get_personality(self) -> str:
        """Retrieves learned traits to shape interaction."""
        try:
            with sqlite3.connect('/home/Taremwastudios/TaremwaStudios/experimental_brain.db') as conn:
                traits = conn.execute('SELECT trait, value FROM personality ORDER BY importance DESC LIMIT 5').fetchall()
                if traits:
                    return "\n[LEARNED PERSONALITY]: " + " | ".join([f"{t[0]}: {t[1]}" for t in traits])
        except: pass
        return ""

    def _learn_trait(self, userInput: str):
        """Attempts to extract a personal trait or preference from user input."""
        # Simple pattern: "I like X", "I prefer X", "Remember that X"
        patterns = [
            (r"(?:i|I)\s+(?:like|prefer|want)\s+(.*)", "User Preference"),
            (r"(?:r|R)emember\s+(?:that|to)\s+(.*)", "Core Directive"),
            (r"(?:m|M)y\s+style\s+is\s+(.*)", "Coding Style")
        ]
        
        try:
            for pattern, trait_type in patterns:
                match = re.search(pattern, userInput)
                if match:
                    val = match.group(1).strip()
                    with sqlite3.connect('/home/Taremwastudios/TaremwaStudios/experimental_brain.db') as conn:
                        conn.execute("""
                            INSERT INTO personality (trait, value, importance) VALUES (?, ?, 1)
                            ON CONFLICT(trait) DO UPDATE SET value = ?, importance = importance + 1
                        """, (trait_type, val, val))
                        conn.commit()
        except: pass

    async def sendMessageStream(self, history: List[Any], userInput: str) -> AsyncGenerator[str, None]:
        """Local generation with synaptic and personality awareness."""
        # 1. Active Learning
        self._learn_trait(userInput)
        
        # 2. Context Retrieval (Internal only for now)
        personality_context = self._get_personality()
        
        # 3. Generate pure response from local engine
        async for chunk in self.generate(userInput):
            yield chunk