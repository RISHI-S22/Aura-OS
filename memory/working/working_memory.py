from typing import Dict, Any, Optional

class WorkingMemory:
    """Scratchpad memory for active subtasks, intermediate outputs, and context."""
    def __init__(self):
        self._store: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._store[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._store.get(key, default)

    def clear(self):
        self._store.clear()