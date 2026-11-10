from typing import List, Dict, Any

class EpisodicMemory:
    def __init__(self):
        self._episodes: List[Dict[str, Any]] = []

    def record(self, event: Dict[str, Any]):
        self._episodes.append(event)
