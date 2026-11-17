import os
import platform
from typing import Any, Dict
from memory.manager import memory_manager

class ContextEngine:
    """Aggregates live OS environment state and memory context for cognition."""

    def get_context(self, query: str = "") -> Dict[str, Any]:
        return {
            "os": f"{platform.system()} {platform.release()}",
            "cwd": os.getcwd(),
            "active_mode": "autonomous",
            "memory": memory_manager.build_context_snapshot(query),
        }

context_engine = ContextEngine()
