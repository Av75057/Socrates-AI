from __future__ import annotations

import logging
import threading
from typing import Any

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)

_lock = threading.Lock()
_provider_override: str | None = None
_ollama_model_override: str | None = None


def get_effective_provider() -> str:
    with _lock:
        if _provider_override:
            return _provider_override.lower().strip()
    return (get_settings().llm_provider or "openrouter").lower().strip()


def get_effective_ollama_model() -> str:
    with _lock:
        if _ollama_model_override:
            return _ollama_model_override
    return (get_settings().ollama_model or "qwen2.5:7b-instruct").strip()


def set_runtime_provider(provider: str | None) -> None:
    """None — использовать LLM_PROVIDER из .env."""
    global _provider_override
    with _lock:
        if provider is None or not str(provider).strip():
            _provider_override = None
            return
        p = str(provider).lower().strip()
        if p not in ("ollama", "openrouter"):
            raise ValueError("provider must be 'ollama' or 'openrouter'")
        _provider_override = p


def set_runtime_ollama_model(model: str | None) -> None:
    """None — использовать ollama_model из .env."""
    global _ollama_model_override
    with _lock:
        if model is None or not str(model).strip():
            _ollama_model_override = None
        else:
            _ollama_model_override = str(model).strip()


def set_runtime_llm(provider: str | None, ollama_model: str | None = None) -> None:
    """Совместимость: провайдер и при необходимости модель Ollama (см. set_runtime_llm в коде)."""
    set_runtime_provider(provider)
    if ollama_model is not None:
        set_runtime_ollama_model(ollama_model)
    elif provider is None:
        set_runtime_ollama_model(None)


def ping_ollama(base_url: str | None = None) -> bool:
    url = (base_url or get_settings().ollama_base_url or "http://localhost:11434").rstrip("/")
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(f"{url}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


def runtime_snapshot() -> dict[str, Any]:
    with _lock:
        return {
            "provider_override": _provider_override,
            "ollama_model_override": _ollama_model_override,
        }
