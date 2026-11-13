import os
from typing import Any, Dict, List, Optional
from core.model_router.fallback import FallbackHandler

class ModelRouter:
    """Unified routing gateway across LLM providers with automatic fallback."""

    def __init__(self):
        self.primary_model = os.getenv("AURA_PRIMARY_MODEL", "gemini/gemini-1.5-flash")
        self.fast_model = os.getenv("AURA_FAST_MODEL", "gemini/gemini-1.5-flash")

    def completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        response_format: Optional[Any] = None,
        **kwargs,
    ) -> Any:
        import litellm
        litellm.suppress_debug_info = True

        selected = model or self.fast_model
        attempts = len(FallbackHandler.MODEL_CHAIN)

        last_err = None
        for _ in range(attempts):
            try:
                return litellm.completion(
                    model=selected,
                    messages=messages,
                    temperature=temperature,
                    response_format=response_format,
                    **kwargs,
                )
            except Exception as err:
                last_err = err
                selected = FallbackHandler.get_next(selected)
        raise last_err

model_router = ModelRouter()