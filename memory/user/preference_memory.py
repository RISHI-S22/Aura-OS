from typing import Dict, Any

class PreferenceMemory:
    def get_preferences(self) -> Dict[str, Any]:
        return {"theme": "light", "verbosity": "concise"}
