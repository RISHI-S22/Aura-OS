from unittest.mock import patch
from fastapi.testclient import TestClient
from aura.api.main import app
from core.model_router.fallback_handler import FallbackHandler
from core.model_router.router import ModelRouter

client = TestClient(app)

def test_fallback_handler_builds_deduplicated_chain(monkeypatch):
    monkeypatch.setenv("DEFAULT_MODEL", "gemini/gemini-2.5-flash")
    monkeypatch.setenv("FALLBACK_MODELS", "groq/llama-3.3-70b-versatile, gemini/gemini-2.5-flash, ollama/qwen2.5:7b")
    chain = FallbackHandler.get_model_chain()
    assert chain == [
        "gemini/gemini-2.5-flash",
        "groq/llama-3.3-70b-versatile",
        "ollama/qwen2.5:7b",
    ]

def test_model_router_cascades_on_provider_error(monkeypatch):
    monkeypatch.setenv("DEFAULT_MODEL", "gemini/gemini-2.5-flash")
    monkeypatch.setenv("FALLBACK_MODELS", "groq/llama-3.3-70b-versatile")
    router = ModelRouter()

    calls = []
    def fake_completion(**kwargs):
        calls.append(kwargs["model"])
        if kwargs["model"] == "gemini/gemini-2.5-flash":
            raise RuntimeError("429 Rate Limit")
        return {"choices": [{"message": {"content": "ok"}}]}

    with patch("litellm.completion", side_effect=fake_completion):
        res = router.completion(messages=[{"role": "user", "content": "hi"}])
        assert res["choices"][0]["message"]["content"] == "ok"
        assert calls == ["gemini/gemini-2.5-flash", "groq/llama-3.3-70b-versatile"]

def test_models_endpoint_masks_secrets(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret_value_123")
    resp = client.get("/api/v1/models")
    assert resp.status_code == 200
    body = resp.json()
    assert body["providers"]["groq"] is True
    assert "gsk_secret_value_123" not in str(body)
