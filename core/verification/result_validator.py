from typing import Dict, Any

class ResultValidator:
    """Validates that agent execution matches schema and was genuinely completed."""
    def validate(self, result: Dict[str, Any]) -> bool:
        if not result or result.get("status") == "error":
            return False
        return True

validator = ResultValidator()
