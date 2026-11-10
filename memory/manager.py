from memory.working.working_memory import WorkingMemory
from memory.episodic.episodic_memory import EpisodicMemory
from memory.semantic.semantic_memory import SemanticMemory
from memory.user.preference_memory import PreferenceMemory

class MemoryManager:
    def __init__(self):
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.user = PreferenceMemory()

memory_manager = MemoryManager()
