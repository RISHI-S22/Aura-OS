from typing import Optional

class TextToSpeech:
    """Synthesizes spoken responses for duplex voice interaction."""

    def format_spoken_summary(self, status: str, intent: str, step_count: int) -> str:
        if status == "pending_approval":
            return f"I have prepared the {intent} workflow and paused at an action requiring your approval."
        if status == "completed":
            return f"Completed your {intent} request across {step_count} steps."
        return f"Task status is {status}."
