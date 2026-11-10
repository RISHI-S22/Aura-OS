from typing import Dict, Any

class IntentClassifier:
    """Classifies user input into actionable intents."""
    def classify(self, command: str) -> Dict[str, Any]:
        cmd = command.lower()
        if "research" in cmd or "search" in cmd:
            return {"intent": "research", "confidence": 0.95}
        elif "email" in cmd or "send" in cmd:
            return {"intent": "communication", "confidence": 0.92}
        elif "code" in cmd or "debug" in cmd:
            return {"intent": "software_engineering", "confidence": 0.90}
        return {"intent": "general_inquiry", "confidence": 0.85}
