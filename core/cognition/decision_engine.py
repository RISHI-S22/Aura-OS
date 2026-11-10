from typing import Dict, Any

class DecisionEngine:
    """Evaluates risks and decides whether an action requires explicit human confirmation."""
    def evaluate_risk(self, action_name: str, payload: Dict[str, Any]) -> bool:
        sensitive_actions = {"send_email", "delete_file", "execute_terminal", "modify_system"}
        return action_name in sensitive_actions
