from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.config import get_settings
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openrouter_provider import OpenRouterProvider
from app.services.llm.runtime import get_effective_provider

log = logging.getLogger(__name__)

LLM_UNAVAILABLE = (
    "[LLM] Сервис временно недоступен. Кратко опиши мысль своими словами или попробуй позже."
)


def _openrouter_fallback_model() -> str:
    return os.getenv("OPENROUTER_MODEL_FALLBACK", "openrouter/auto")


def _openrouter_headers() -> dict[str, str]:
    key = os.getenv("OPENROUTER_API_KEY", "") or ""
    h: dict[str, str] = {
        "Authorization": f"Bearer {key or 'sk-no-key-required'}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:5173"),
        "X-Title": os.getenv("OPENROUTER_X_TITLE", "Socrates AI"),
    }
    return h


def _openrouter_url() -> str:
    raw = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions").rstrip("/")
    if not raw.endswith("/chat/completions"):
        return f"{raw.rstrip('/')}/chat/completions"
    return raw


def _ollama_chat_sync(
    base_url: str,
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    max_tokens: int,
    timeout_s: float,
) -> str:
    url = f"{base_url.rstrip('/')}/api/chat"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    msg = data.get("message") or {}
    content = msg.get("content")
    return (content or "").strip() or "…"


def _openrouter_chat_sync(
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    max_tokens: int,
    timeout_s: float,
) -> str:
    if not os.getenv("OPENROUTER_API_KEY", "").strip():
        raise ValueError("OPENROUTER_API_KEY is not set")
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(_openrouter_url(), json=payload, headers=_openrouter_headers())
        r.raise_for_status()
        data = r.json()
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("empty choices")
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    return (content or "").strip() or "…"


async def chat_completion_global_async(
    messages: list[dict[str, Any]],
    *,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 300,
) -> str:
    """Глобальный LLM: по настройке Ollama или OpenRouter; при сбое Ollama — OpenRouter."""
    provider = get_effective_provider()
    s = get_settings()
    ollama_base = (s.ollama_base_url or "http://localhost:11434").rstrip("/")
    fb = _openrouter_fallback_model()

    if provider == "ollama":
        try:
            op = OllamaProvider(ollama_base)
            return await op.chat_completion(
                messages, model=model, temperature=temperature, max_tokens=max_tokens
            )
        except Exception as e:
            log.warning("Ollama недоступен или ошибка, fallback OpenRouter: %s", e)
            try:
                orp = OpenRouterProvider()
                return await orp.chat_completion(
                    messages, model=fb, temperature=temperature, max_tokens=max_tokens
                )
            except Exception as e2:
                log.exception("OpenRouter fallback failed: %s", e2)
                return LLM_UNAVAILABLE

    try:
        orp = OpenRouterProvider()
        return await orp.chat_completion(
            messages, model=model, temperature=temperature, max_tokens=max_tokens
        )
    except Exception as e:
        log.exception("OpenRouter failed: %s", e)
        return LLM_UNAVAILABLE


def chat_completion_global_sync(
    messages: list[dict[str, Any]],
    *,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 300,
    timeout_s: float = 25.0,
) -> str:
    """Синхронный вызов (редкие проверки в learning_service)."""
    provider = get_effective_provider()
    s = get_settings()
    ollama_base = (s.ollama_base_url or "http://localhost:11434").rstrip("/")
    fb = _openrouter_fallback_model()

    if provider == "ollama":
        try:
            return _ollama_chat_sync(
                ollama_base,
                model,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
            )
        except Exception as e:
            log.warning("Ollama sync недоступен, fallback OpenRouter: %s", e)
            try:
                return _openrouter_chat_sync(
                    fb, messages, temperature=temperature, max_tokens=max_tokens, timeout_s=timeout_s
                )
            except Exception:
                log.debug("OpenRouter sync fallback failed", exc_info=True)
                return ""

    try:
        return _openrouter_chat_sync(
            model, messages, temperature=temperature, max_tokens=max_tokens, timeout_s=timeout_s
        )
    except Exception:
        log.debug("OpenRouter sync failed", exc_info=True)
        return ""
