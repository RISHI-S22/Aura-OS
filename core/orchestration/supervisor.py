from typing import Dict, Any
from core.orchestration.state import AgentState

class Supervisor:
    """Oversees multi-agent coordination, verifying checkpoints and state."""
    def supervise(self, state: AgentState) -> str:
        if state.get("approval_needed"):
            return "WAIT_FOR_APPROVAL"
        if state.get("current_step", 0) >= len(state.get("plan", [])):
            return "COMPLETED"
        return "CONTINUE"
