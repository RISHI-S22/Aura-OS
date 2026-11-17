from core.orchestration.state import AgentState

class Supervisor:
    """Evaluates graph execution state and determines next routing transition."""

    def supervise(self, state: AgentState) -> str:
        if state.get("error"):
            return "REPLAN"
        if state.get("approval_needed"):
            return "WAIT_FOR_APPROVAL"
        if state.get("current_step", 0) >= len(state.get("plan", [])):
            return "COMPLETED"
        return "CONTINUE"

supervisor = Supervisor()
