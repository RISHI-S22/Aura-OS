from typing import Dict, Any, Optional

class ApprovalGate:
    """Manages pending human authorizations for sensitive operations."""
    _pending: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_request(cls, request_id: str, action: str, details: Dict[str, Any]):
        cls._pending[request_id] = {
            "action": action,
            "details": details,
            "approved": False
        }

    @classmethod
    def approve(cls, request_id: str) -> bool:
        if request_id in cls._pending:
            cls._pending[request_id]["approved"] = True
            return True
        return False

    @classmethod
    def is_approved(cls, request_id: str) -> bool:
        return cls._pending.get(request_id, {}).get("approved", False)