from typing import List, Dict, Any

class ReasoningEngine:
    """Performs multi-step rational decomposition before planning."""
    def reason(self, command: str, context: Dict[str, Any]) -> List[str]:
        return [
            f"Understand goal from command: {command}",
            "Check environmental constraints and available specialist agents",
            "Synthesize subtask graph"
        ]
