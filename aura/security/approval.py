from typing import Any, Dict

class ApprovalGate:
    """Tracks pending human approvals for sensitive or irreversible actions."""

    _requests: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_request(cls, request_id: str, action: str, payload: Dict[str, Any]):
        cls._requests[request_id] = {
            "action": action,
            "payload": payload,
            "approved": False,
        }

    @classmethod
    def approve(cls, request_id: str) -> bool:
        if request_id in cls._requests:
            cls._requests[request_id]["approved"] = True
            return True
        return False

    @classmethod
    def is_approved(cls, request_id: str) -> bool:
        return cls._requests.get(request_id, {}).get("approved", False)