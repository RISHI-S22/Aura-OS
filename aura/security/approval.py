from typing import Any, Dict, Optional

class ApprovalGate:
    """Tracks pending human approvals and suspended graph states for seamless resume."""

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

    @classmethod
    def get_payload(cls, request_id: str) -> Optional[Dict[str, Any]]:
        req = cls._requests.get(request_id)
        return req["payload"] if req else None
