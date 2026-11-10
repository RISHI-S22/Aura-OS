from typing import List, Dict, Any

class TaskDecomposer:
    """Breaks complex tasks down into atomic units."""
    def decompose(self, command: str) -> List[Dict[str, Any]]:
        return [
            {"id": "task_1", "action": "gather_information", "target": command},
            {"id": "task_2", "action": "verify_and_synthesize", "target": "task_1"}
        ]
