import hashlib
import json
from typing import Any, Dict, List

class ScreenDeltaVerifier:
    """Detects whether a UI or DOM action produced an observable state transition."""

    @staticmethod
    def compute_state_signature(elements: List[Dict[str, Any]]) -> str:
        normalized = json.dumps(elements, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def has_state_changed(
        cls,
        before_elements: List[Dict[str, Any]],
        after_elements: List[Dict[str, Any]],
    ) -> bool:
        return cls.compute_state_signature(before_elements) != cls.compute_state_signature(after_elements)
