from typing import List, Dict, Any

class Replanner:
    """Dynamically adapts task plans when a step encounters an error."""
    def replan_on_failure(self, failed_task_id: str, error_msg: str, remaining_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        recovery_task = {
            "id": f"recover_{failed_task_id}",
            "action": "alternative_approach",
            "context": f"Failed due to: {error_msg}"
        }
        return [recovery_task] + remaining_tasks
