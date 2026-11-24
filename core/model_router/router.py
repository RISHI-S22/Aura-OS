from typing import Any, Dict, List, Optional
from core.model_router.fallback_handler import FallbackHandler

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class ModelRouter:
    """Universal multi-provider LiteLLM gateway with automatic fallback across cloud and local models."""

    def __init__(self):
        self.fallback = FallbackHandler()

    def get_routing_status(self) -> Dict[str, Any]:
        return {
            "model_chain": self.fallback.get_model_chain(),
            "providers": self.fallback.configured_providers(),
        }

    def completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        import litellm

        candidates = [model] if model else self.fallback.get_model_chain()
        last_error: Optional[Exception] = None

        for candidate in candidates:
            try:
                call_kwargs: Dict[str, Any] = {
                    "model": candidate,
                    "messages": messages,
                    **kwargs,
                }
                if response_format is not None:
                    call_kwargs["response_format"] = response_format
                return litellm.completion(**call_kwargs)
            except Exception as exc:
                last_error = exc
                continue

        raise RuntimeError(f"All configured models failed ({candidates}): {last_error}")

model_router = ModelRouter()
