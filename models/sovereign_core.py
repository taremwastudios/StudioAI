import sqlite3
import re
import os
import nltk
import random
from nltk.corpus import wordnet
from typing import List, AsyncGenerator, Any

class SovereignEngine:
    """
    The Taremwa Studios Back-Weighting Engine.
    Implements local 'Fine-Tuning' via synaptic reinforcement and pruning.
    """
    def __init__(self):
        self.db_path = "/home/Taremwastudios/TaremwaStudios/experimental_brain.db"
        self.name = "Speedy Sovereign"
        self.last_synapses = [] # The 'weights' we used in the last turn
        self._init_db_tuning()

    def _init_db_tuning(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Track what we just thought about so we can tune it
                conn.execute("CREATE TABLE IF NOT EXISTS active_thought_path (synapse_id INTEGER)")
                conn.commit()
        except: pass

    def _apply_tuning(self, reward: float):
        """
        The 'Fine-Tuning' Algorithm. 
        Adjusts weights of the last used synapses based on user feedback.
        Reward 2.0 = Strong Positive, 0.5 = Negative.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                for sid in self.last_synapses:
                    if reward > 1.0:
                        conn.execute("UPDATE synapses SET strength = strength + 2 WHERE id = ?", (sid,))
                    else:
                        conn.execute("UPDATE synapses SET strength = strength - 1 WHERE id = ?", (sid,))
                # Prune dead synapses
                conn.execute("DELETE FROM synapses WHERE strength <= 0")
                conn.commit()
            self.last_synapses = []
        except: pass

    def _find_logic(self, query: str) -> List[str]:
        """Weighted search - prioritizes 'Strong' synapses."""
        words = re.findall(r'\w+', query.lower())
        results = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                for word in words:
                    if len(word) < 3: continue
                    # Get high-strength synapses (The 'Fine-Tuned' Knowledge)
                    syns = conn.execute(
                        "SELECT id, predicate, object FROM synapses WHERE subject = ? ORDER BY strength DESC LIMIT 5", 
                        (word,)
                    ).fetchall()
                    for sid, p, o in syns:
                        self.last_synapses.append(sid) # Record for tuning
                        results.append(f"{word.capitalize()} {p} {o}.")
        except: pass
        return results

    async def generate(self, userInput: str) -> AsyncGenerator[str, None]:
        query = userInput.lower().strip()

        # 1. DETECT FEEDBACK (The 'Fine-Tuning' Trigger)
        if any(x in query for x in ["correct", "good", "yes", "right"]):
            self._apply_tuning(2.0)
            yield "Understood. I have reinforced that logical path in my synaptic map.\n"
            return
        elif any(x in query for x in ["wrong", "no", "bad", "incorrect"]):
            self._apply_tuning(0.5)
            yield "Acknowledged. I have pruned that logic as it was incorrect. I will try a different path.\n"
            return

        # 2. NORMAL INFERENCE
        self.last_synapses = [] # Clear last thought
        results = self._find_logic(query)
        
        if results:
            for r in results: yield r + "\n"
        else:
            # Semantic Fallback (Dictionary)
            tokens = nltk.word_tokenize(query)
            meanings = []
            for w in tokens:
                if len(w) > 3:
                    syns = wordnet.synsets(w)
                    if syns: meanings.append(f"'{w}': {syns[0].definition().split(';')[0]}")
            
            if meanings:
                yield "[Semantic Map]: " + " + ".join(meanings) + "\n"
            else:
                yield "I have no synapses for this yet. Tell me what it means to build a connection.\n"
