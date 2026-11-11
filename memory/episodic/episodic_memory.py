from typing import List, Dict, Any
import time

class EpisodicMemory:
    """Stores sequential execution episodes and run history."""
    def __init__(self):
        self._episodes: List[Dict[str, Any]] = []

    def record(self, command: str, status: str, artifacts: Dict[str, Any]):
        self._episodes.append({
            "timestamp": time.time(),
            "command": command,
            "status": status,
            "artifacts": artifacts
        })

    def get_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self._episodes[-limit:]