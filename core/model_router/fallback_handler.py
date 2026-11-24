import os
from typing import List

class FallbackHandler:
    """Resolves ordered multi-provider LLM fallback chains from environment configuration."""

    PROVIDER_KEY_MAP = {
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "mistral": "MISTRAL_API_KEY",
    }

    @classmethod
    def get_model_chain(cls) -> List[str]:
        primary = os.getenv("DEFAULT_MODEL", "gemini/gemini-2.5-flash").strip()
        raw_fallbacks = os.getenv(
            "FALLBACK_MODELS",
            "groq/llama-3.3-70b-versatile,openrouter/meta-llama/llama-3.3-70b-instruct:free,ollama/qwen2.5:7b",
        )
        chain = [primary] if primary else []
        for item in raw_fallbacks.split(","):
            model = item.strip()
            if model and model not in chain:
                chain.append(model)
        return chain

    @classmethod
    def configured_providers(cls) -> dict[str, bool]:
        status = {
            provider: bool(os.getenv(env_var, "").strip())
            for provider, env_var in cls.PROVIDER_KEY_MAP.items()
        }
        status["ollama"] = bool(os.getenv("OLLAMA_API_BASE", "http://localhost:11434").strip())
        return status
