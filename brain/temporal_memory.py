"""
Aura-OS Temporal & Episodic Recall Engine
Maintains deep chronological provenance of tasks, actions, and outputs.
Recalls similar requests over variable time windows (e.g. 180 days)
and provides filtered historical suggestions.
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime
import numpy as np
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import PATHS, MODELS

OLLAMA_EMBED_URL = "http://127.0.0.1:11434/api/embeddings"

class TemporalMemoryEngine:
    def __init__(self):
        os.makedirs(PATHS.MEMORY, exist_ok=True)
        self.db_path = os.path.join(PATHS.MEMORY, "temporal_episodes.db")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_signature TEXT,
                    user_prompt TEXT,
                    parameters_json TEXT,
                    outcome_summary TEXT,
                    embedding_json TEXT,
                    timestamp REAL,
                    date_str TEXT
                )
            """)

    def get_embedding(self, text: str) -> list:
        try:
            res = requests.post(OLLAMA_EMBED_URL, json={
                "model": "all-minilm:latest" if "minilm" in MODELS.LLM_MODEL else MODELS.LLM_MODEL,
                "prompt": text
            }, timeout=10).json()
            return res.get("embedding", [])
        except Exception:
            return []

    def record_episode(self, user_prompt: str, task_signature: str, parameters: dict, outcome: str):
        """Logs an executed task with exact timestamp and semantic vector."""
        emb = self.get_embedding(user_prompt)
        now = time.time()
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO episodes (task_signature, user_prompt, parameters_json, outcome_summary, embedding_json, timestamp, date_str)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task_signature,
                user_prompt,
                json.dumps(parameters),
                outcome,
                json.dumps(emb),
                now,
                date_str
            ))
        print(f"[💾 Episodic Ledger] Recorded task: '{task_signature}' on {date_str}")

    def query_similar_historical_task(self, current_prompt: str, min_similarity: float = 0.72) -> dict:
        """
        Scans temporal memory, filters relevance within itself, and calculates
        the exact time difference in days.
        """
        curr_emb = self.get_embedding(current_prompt)
        if not curr_emb:
            return None

        curr_vec = np.array(curr_emb)
        norm_curr = np.linalg.norm(curr_vec)
        if norm_curr == 0:
            return None

        best_match = None
        highest_sim = -1.0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, task_signature, user_prompt, parameters_json, outcome_summary, embedding_json, timestamp, date_str FROM episodes")
            rows = cursor.fetchall()

        now = time.time()

        for row in rows:
            ep_id, sig, prompt, params, outcome, emb_json, ts, date_str = row
            if not emb_json:
                continue

            saved_vec = np.array(json.loads(emb_json))
            norm_saved = np.linalg.norm(saved_vec)
            if norm_saved == 0:
                continue

            similarity = float(np.dot(curr_vec, saved_vec) / (norm_curr * norm_saved))

            if similarity > highest_sim and similarity >= min_similarity:
                highest_sim = similarity
                days_ago = int((now - ts) / 86400)
                best_match = {
                    "task_signature": sig,
                    "original_prompt": prompt,
                    "parameters": json.loads(params),
                    "outcome": outcome,
                    "days_ago": days_ago,
                    "date_str": date_str,
                    "similarity": round(similarity, 3)
                }

        return best_match