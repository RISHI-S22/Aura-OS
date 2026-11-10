import os
from typing import Any, Dict, List, Optional

class ModelRouter:
    """Unified routing gateway for LLM calls across providers using LiteLLM."""

    def __init__(self):
        self.primary_model = os.getenv("AURA_PRIMARY_MODEL", "gemini/gemini-1.5-flash")
        self.fast_model = os.getenv("AURA_FAST_MODEL", "gemini/gemini-1.5-flash")

    def completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        response_format: Optional[Any] = None,
        **kwargs
    ) -> Any:
        try:
            import litellm
            litellm.suppress_debug_info = True
            selected_model = model or self.fast_model
            return litellm.completion(
                model=selected_model,
                messages=messages,
                temperature=temperature,
                response_format=response_format,
                **kwargs
            )
        except Exception as e:
            raise e

model_router = ModelRouter()
