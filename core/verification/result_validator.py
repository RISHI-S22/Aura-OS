from pathlib import Path
from typing import Dict, Any

class ResultValidator:
    \"\"\"Verifies that agent execution outputs are valid and physically exist.\"\"\"

    def validate(self, result: Dict[str, Any]) -> bool:
        if not result or result.get("status") == "error":
            return False

        if result.get("artifact_created"):
            artifact_path = result.get("artifact_path")
            if not artifact_path or not Path(artifact_path).exists():
                return False

        return True

validator = ResultValidator()
