import json
import os
from typing import Any, Dict, List

class ProceduralMemory:
    """Stores and recalls generalized action traces that succeeded across arbitrary tasks."""

    def __init__(self, storage_path: str = "workspace/procedural_memory.json"):
        self.storage_path = storage_path
        self._procedures: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self._procedures[-100:], f, indent=2)

    def record_procedure(self, goal: str, agent: str, action_sequence: List[Dict[str, Any]]):
        if not action_sequence:
            return
        self._procedures.append({
            "goal": goal,
            "agent": agent,
            "steps": action_sequence,
        })
        self._save()

    def recall(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        tokens = {w.lower() for w in query.split() if len(w) > 3}
        if not tokens:
            return self._procedures[-limit:]
        scored = []
        for proc in self._procedures:
            goal_tokens = {w.lower() for w in proc.get("goal", "").split()}
            overlap = len(tokens & goal_tokens)
            if overlap > 0:
                scored.append((overlap, proc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]
