from typing import List

class FallbackHandler:
    """Manages provider fallback chains for resilient LLM routing."""

    MODEL_CHAIN: List[str] = [
        "gemini/gemini-1.5-flash",
        "gpt-4o-mini",
        "claude-3-5-sonnet-20241022",
        "ollama/qwen2.5:7b",
    ]

    @classmethod
    def get_next(cls, current_model: str) -> str:
        try:
            idx = cls.MODEL_CHAIN.index(current_model)
            if idx + 1 < len(cls.MODEL_CHAIN):
                return cls.MODEL_CHAIN[idx + 1]
        except ValueError:
            pass
        return cls.MODEL_CHAIN[0]