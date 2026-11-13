import time
from typing import Any, Dict, List

class EpisodicMemory:
    """Chronological log of executed user commands and task outcomes."""

    def __init__(self):
        self._episodes: List[Dict[str, Any]] = []

    def record(self, session_id: str, command: str, status: str, artifacts: Dict[str, Any]):
        self._episodes.append({
            "session_id": session_id,
            "timestamp": time.time(),
            "command": command,
            "status": status,
            "artifacts": artifacts,
        })

    def recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._episodes[-limit:]