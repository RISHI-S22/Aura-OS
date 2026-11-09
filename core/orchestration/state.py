from typing import TypedDict, Any

class AuraState(TypedDict, total=False):
    command: str
    intent: dict[str, Any]
    plan: list[dict[str, Any]]
    execution_log: list[dict[str, Any]]
    verification: dict[str, Any]
    response: str
    error: str
