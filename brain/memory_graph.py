"""
Aura-OS Relational Knowledge & Identity Graph
Stores structured deterministic user facts, contacts, and system entities
using SQLite to anchor conversational context and eliminate hallucinations.
"""

import os
import sqlite3
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import PATHS

DB_PATH = os.path.join(PATHS.MEMORY, "identity_graph.db")

class MemoryGraph:
    def __init__(self):
        os.makedirs(PATHS.MEMORY, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT,
                    predicate TEXT,
                    object TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(subject, predicate, object)
                )
            """)

    def insert_fact(self, subject: str, predicate: str, obj: str, category: str = "general"):
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO entities (subject, predicate, object, category)
                VALUES (?, ?, ?, ?)
            """, (subject.lower(), predicate.lower(), obj, category.lower()))

    def query_facts(self, subject: str) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT predicate, object FROM entities WHERE subject = ?", (subject.lower(),))
        return cursor.fetchall()

    def get_contact_info(self, name: str) -> dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT predicate, object FROM entities WHERE subject = ? AND category = 'contact'", (name.lower(),))
        results = cursor.fetchall()
        return {pred: obj for pred, obj in results}

    def dump_context_string(self, keyword: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT subject, predicate, object FROM entities 
            WHERE subject LIKE ? OR object LIKE ? LIMIT 10
        """, (f"%{keyword}%", f"%{keyword}%"))
        rows = cursor.fetchall()
        if not rows:
            return ""
        return "\n".join([f"- {s} {p} {o}" for s, p, o in rows])