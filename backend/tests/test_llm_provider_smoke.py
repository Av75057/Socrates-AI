from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.llm.runtime import set_runtime_provider
from app.services.model_router import ModelRouter


def _reset_runtime() -> None:
    set_runtime_provider(None)
    get_settings.cache_clear()


def test_health_endpoint_works():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_router_selects_openai_models(monkeypatch):
    _reset_runtime()
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL_QUESTION", "gpt-5.5")
    monkeypatch.setenv("OPENAI_MODEL_HINT", "gpt-5.4-mini")
    monkeypatch.setenv("OPENAI_MODEL_EXPLAIN", "gpt-5.5")
    monkeypatch.setenv("OPENAI_MODEL_PEDAGOGY", "gpt-5.4-mini")
    monkeypatch.setenv("OPENAI_MODEL_FALLBACK", "gpt-5.4-mini")
    get_settings.cache_clear()

    router = ModelRouter()

    assert router.select_model("question") == "gpt-5.5"
    assert router.select_model("hint") == "gpt-5.4-mini"
    assert router.select_model("explain") == "gpt-5.5"
    assert router.pedagogy_model() == "gpt-5.4-mini"
    assert "HTTP-Referer" not in router._headers()
    assert "X-Title" not in router._headers()

    _reset_runtime()


def test_model_router_openrouter_behavior_is_preserved(monkeypatch):
    _reset_runtime()
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_MODEL_QUESTION", "deepseek/deepseek-chat")
    monkeypatch.setenv("OPENROUTER_MODEL_HINT", "openrouter/auto")
    monkeypatch.setenv("OPENROUTER_MODEL_EXPLAIN", "deepseek/deepseek-chat")
    monkeypatch.setenv("OPENROUTER_MODEL_PEDAGOGY", "google/gemini-2.0-flash-001")
    monkeypatch.setenv("OPENROUTER_MODEL_FALLBACK", "openrouter/auto")
    get_settings.cache_clear()

    router = ModelRouter()

    assert router.select_model("question") == "deepseek/deepseek-chat"
    assert router.select_model("hint") == "openrouter/auto"
    assert router.select_model("explain") == "deepseek/deepseek-chat"
    assert router.pedagogy_model() == "google/gemini-2.0-flash-001"
    assert "HTTP-Referer" in router._headers()
    assert "X-Title" in router._headers()

    _reset_runtime()


def test_model_router_ollama_behavior_is_preserved(monkeypatch):
    _reset_runtime()
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    monkeypatch.setenv("OLLAMA_MODEL_QUESTION", "qwen2.5:14b")
    monkeypatch.setenv("OLLAMA_MODEL_HINT", "qwen2.5:3b")
    monkeypatch.setenv("OLLAMA_MODEL_EXPLAIN", "qwen2.5:7b-instruct")
    monkeypatch.setenv("OLLAMA_MODEL_PEDAGOGY", "qwen2.5:3b")
    get_settings.cache_clear()

    router = ModelRouter()

    assert router.select_model("question") == "qwen2.5:14b"
    assert router.select_model("hint") == "qwen2.5:3b"
    assert router.select_model("explain") == "qwen2.5:7b-instruct"
    assert router.pedagogy_model() == "qwen2.5:3b"

    _reset_runtime()
