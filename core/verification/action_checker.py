from typing import Any, Dict

class ActionChecker:
    """Verifies post-execution state transitions before marking a DAG node complete."""

    @staticmethod
    def verify_step(task: Dict[str, Any], result: Dict[str, Any]) -> bool:
        if not isinstance(result, dict):
            return False
        if result.get("status") not in ("success", "pending_approval"):
            return False
        if result.get("agent") and result.get("agent") != task.get("agent"):
            return False
        return True
