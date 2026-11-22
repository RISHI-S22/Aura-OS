from typing import Any, Dict
from memory.episodic.episodic_memory import EpisodicMemory
from memory.procedural.procedural_memory import ProceduralMemory
from memory.semantic.semantic_memory import SemanticMemory
from memory.user.preference_memory import PreferenceMemory
from memory.working.working_memory import WorkingMemory

class MemoryManager:
    """Unified cognitive memory controller across working, episodic, semantic, and procedural stores."""

    def __init__(self):
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.user = PreferenceMemory()

    def build_context_snapshot(self, query: str) -> Dict[str, Any]:
        return {
            "preferences": self.user.get_preferences(),
            "recent_episodes": self.episodic.recent(limit=3),
            "semantic_hits": self.semantic.search(query, limit=3),
            "learned_procedures": self.procedural.recall(query, limit=2),
        }

memory_manager = MemoryManager()
