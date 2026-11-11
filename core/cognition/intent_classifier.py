from typing import Dict, Any
from core.cognition.confidence import ConfidenceScore

class IntentClassifier:
    """Classifies user input into domain actions with confidence calculation."""
    def classify(self, command: str) -> Dict[str, Any]:
        cmd = command.lower()
        if any(w in cmd for w in ["research", "search", "find", "lookup"]):
            return {"intent": "research", "confidence": ConfidenceScore.calculate(2, 2)}
        elif any(w in cmd for w in ["email", "mail", "send", "notify"]):
            return {"intent": "communication", "confidence": ConfidenceScore.calculate(2, 2)}
        elif any(w in cmd for w in ["code", "build", "debug", "script"]):
            return {"intent": "software_engineering", "confidence": ConfidenceScore.calculate(2, 2)}
        return {"intent": "general_inquiry", "confidence": 0.65}