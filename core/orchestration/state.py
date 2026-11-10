from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    command: str
    intent: str
    plan: List[Dict[str, Any]]
    current_step: int
    artifacts: Dict[str, Any]
    approval_needed: bool
    status: str
    error: Optional[str]
