
import sqlite3
import os
from typing import List, Dict, Any

class KnowledgeManager:
    def __init__(self, db_path: str = "knowledge_base.db"):
        self.db_path = os.path.join(os.path.dirname(__file__), db_path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    source TEXT
                )
            """)
            # Create a full-text search table for efficient retrieval
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts 
                USING fts5(topic, content, tags, source, content='knowledge', content_rowid='id')
            """)
            
            # Triggers to keep FTS in sync
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge BEGIN
                    INSERT INTO knowledge_fts(rowid, topic, content, tags, source) VALUES (new.id, new.topic, new.content, new.tags, new.source);
                END;
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge BEGIN
                    INSERT INTO knowledge_fts(knowledge_fts, rowid, topic, content, tags, source) VALUES('delete', old.id, old.topic, old.content, old.tags, old.source);
                END;
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge BEGIN
                    INSERT INTO knowledge_fts(knowledge_fts, rowid, topic, content, tags, source) VALUES('delete', old.id, old.topic, old.content, old.tags, old.source);
                    INSERT INTO knowledge_fts(rowid, topic, content, tags, source) VALUES (new.id, new.topic, new.content, new.tags, new.source);
                END;
            """)
            conn.commit()

    def add_entry(self, topic: str, content: str, tags: str = "", source: str = ""):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO knowledge (topic, content, tags, source) VALUES (?, ?, ?, ?)",
                (topic, content, tags, source)
            )
            conn.commit()

    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        # Simple sanitization: keep only alphanumeric and spaces
        sanitized_query = "".join(c for c in query if c.isalnum() or c.isspace())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Simple FTS5 search
            cursor.execute("""
                SELECT topic, content, source FROM knowledge_fts 
                WHERE knowledge_fts MATCH ? 
                ORDER BY rank 
                LIMIT ?
            """, (sanitized_query, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_topics(self) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT topic FROM knowledge")
            return [row[0] for row in cursor.fetchall()]
