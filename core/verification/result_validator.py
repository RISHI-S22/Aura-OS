import os
from typing import Any, Dict

class ResultValidator:
    """Verifies that agent execution outputs are valid and physically exist."""

    def validate(self, result: Dict[str, Any]) -> bool:
        if not isinstance(result, dict) or result.get("status") == "error":
            return False

        artifact_path = result.get("artifact_path")
        if artifact_path and not os.path.exists(artifact_path):
            return False

        return True

validator = ResultValidator()
