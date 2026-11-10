from typing import Dict, Any

class WorkingMemory:
    def __init__(self):
        self._store: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._store[key] = value

    def get(self, key: str) -> Any:
        return self._store.get(key)
