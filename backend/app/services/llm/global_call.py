from __future__ import annotations

import json
import logging
import os
from typing import Any, AsyncGenerator

import httpx

from app.config import get_settings
from app.services.llm.ollama_provider import OllamaProvider, strip_thinking_tags
from app.services.llm.openrouter_provider import OpenRouterProvider
from app.services.llm.runtime import get_effective_provider

log = logging.getLogger(__name__)

LLM_UNAVAILABLE = (
    "[LLM] Сервис временно недоступен. Кратко опиши мысль своими словами или попробуй позже."
)


def _openrouter_fallback_model() -> str:
    return os.getenv("OPENROUTER_MODEL_FALLBACK", "openrouter/auto")


def _openai_fallback_model() -> str:
    return get_settings().openai_model_fallback


def _openrouter_headers() -> dict[str, str]:
    key = os.getenv("OPENROUTER_API_KEY", "") or ""
    return {
        "Authorization": f"Bearer {key or 'sk-no-key-required'}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:5173"),
        "X-Title": os.getenv("OPENROUTER_X_TITLE", "Socrates AI"),
    }


def _openai_headers() -> dict[str, str]:
    key = get_settings().openai_api_key or ""
    return {
        "Authorization": f"Bearer {key or 'sk-no-key-required'}",
        "Content-Type": "application/json",
    }


def _openrouter_url() -> str:
    raw = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions").rstrip("/")
    if not raw.endswith("/chat/completions"):
        return f"{raw.rstrip('/')}/chat/completions"
    return raw


def _openai_url() -> str:
    raw = (get_settings().openai_api_url or "https://api.openai.com/v1/chat/completions").rstrip("/")
    if not raw.endswith("/chat/completions"):
        return f"{raw.rstrip('/')}/chat/completions"
    return raw


def _extract_content(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("empty choices")
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    return (content or "").strip() or "…"


def _ollama_chat_sync(
    base_url: str,
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    max_tokens: int,
    timeout_s: float,
) -> str:
    settings = get_settings()
    url = f"{base_url.rstrip('/')}/api/chat"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": float(temperature if temperature is not None else settings.llm_temperature),
            "top_p": settings.llm_top_p,
            "repeat_penalty": settings.llm_repeat_penalty,
            "num_predict": int(max_tokens if max_tokens is not None else settings.llm_max_tokens),
        },
    }
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    msg = data.get("message") or {}
    content = msg.get("content")
    return strip_thinking_tags(content or "") or "…"


def _openrouter_chat_sync(
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    max_tokens: int,
    timeout_s: float,
) -> str:
    settings = get_settings()
    if not os.getenv("OPENROUTER_API_KEY", "").strip():
        raise ValueError("OPENROUTER_API_KEY is not set")
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": float(temperature if temperature is not None else settings.llm_temperature),
        "top_p": settings.llm_top_p,
        "max_tokens": int(max_tokens if max_tokens is not None else settings.llm_max_tokens),
        "presence_penalty": settings.llm_presence_penalty,
        "frequency_penalty": settings.llm_frequency_penalty,
    }
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(_openrouter_url(), json=payload, headers=_openrouter_headers())
        r.raise_for_status()
        data = r.json()
    return _extract_content(data)


def _openai_chat_sync(
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    max_tokens: int,
    timeout_s: float,
) -> str:
    settings = get_settings()
    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY is not set")
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": float(temperature if temperature is not None else settings.llm_temperature),
        "top_p": settings.llm_top_p,
        "max_tokens": int(max_tokens if max_tokens is not None else settings.llm_max_tokens),
        "presence_penalty": settings.llm_presence_penalty,
        "frequency_penalty": settings.llm_frequency_penalty,
    }
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(_openai_url(), json=payload, headers=_openai_headers())
        r.raise_for_status()
        data = r.json()
    return _extract_content(data)


async def _openai_chat_async(
    messages: list[dict[str, Any]],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    settings = get_settings()
    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY is not set")
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": float(temperature if temperature is not None else settings.llm_temperature),
        "top_p": settings.llm_top_p,
        "max_tokens": int(max_tokens if max_tokens is not None else settings.llm_max_tokens),
        "presence_penalty": settings.llm_presence_penalty,
        "frequency_penalty": settings.llm_frequency_penalty,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(_openai_url(), json=payload, headers=_openai_headers())
        r.raise_for_status()
        data = r.json()
    return _extract_content(data)


async def _openai_stream(
    messages: list[dict[str, Any]],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
) -> AsyncGenerator[str, None]:
    settings = get_settings()
    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY is not set")
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": float(temperature if temperature is not None else settings.llm_temperature),
        "top_p": settings.llm_top_p,
        "max_tokens": int(max_tokens if max_tokens is not None else settings.llm_max_tokens),
        "presence_penalty": settings.llm_presence_penalty,
        "frequency_penalty": settings.llm_frequency_penalty,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", _openai_url(), json=payload, headers=_openai_headers()) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if not data or data == "[DONE]":
                    if data == "[DONE]":
                        break
                    continue
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                if isinstance(content, str) and content:
                    yield content


async def chat_completion_global_async(
    messages: list[dict[str, Any]],
    *,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 250,
) -> str:
    """Глобальный LLM: по настройке Ollama, OpenAI или OpenRouter."""
    provider = get_effective_provider()
    s = get_settings()
    ollama_base = (s.ollama_base_url or "http://localhost:11434").rstrip("/")
    openrouter_fb = _openrouter_fallback_model()
    openai_fb = _openai_fallback_model()

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
                    messages, model=openrouter_fb, temperature=temperature, max_tokens=max_tokens
                )
            except Exception as e2:
                log.exception("OpenRouter fallback failed: %s", e2)
                return LLM_UNAVAILABLE

    if provider == "openai":
        try:
            return await _openai_chat_async(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            log.warning("OpenAI failed, fallback OpenRouter: %s", e)
            try:
                orp = OpenRouterProvider()
                return await orp.chat_completion(
                    messages, model=openrouter_fb, temperature=temperature, max_tokens=max_tokens
                )
            except Exception as e2:
                log.warning("OpenRouter fallback failed, retry OpenAI fallback model: %s", e2)
                try:
                    return await _openai_chat_async(
                        messages,
                        model=openai_fb,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                except Exception as e3:
                    log.exception("OpenAI fallback failed: %s", e3)
                    return LLM_UNAVAILABLE

    try:
        orp = OpenRouterProvider()
        return await orp.chat_completion(
            messages, model=model, temperature=temperature, max_tokens=max_tokens
        )
    except Exception as e:
        log.exception("OpenRouter failed: %s", e)
        return LLM_UNAVAILABLE


async def _stream_with_fallback(
    primary,
    fallback_factory,
) -> AsyncGenerator[str, None]:
    yielded = False
    try:
        async for chunk in primary:
            yielded = True
            yield chunk
        return
    except Exception as e:
        if yielded:
            raise e
        log.warning("Primary stream failed before first chunk: %s", e)

    if fallback_factory is None:
        yield LLM_UNAVAILABLE
        return

    try:
        async for chunk in fallback_factory():
            yielded = True
            yield chunk
    except Exception as e:
        log.exception("Fallback stream failed: %s", e)
        if not yielded:
            yield LLM_UNAVAILABLE


async def chat_completion_global_stream_async(
    messages: list[dict[str, Any]],
    *,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 250,
) -> AsyncGenerator[str, None]:
    provider = get_effective_provider()
    s = get_settings()
    ollama_base = (s.ollama_base_url or "http://localhost:11434").rstrip("/")
    openrouter_fb = _openrouter_fallback_model()

    if provider == "ollama":
        op = OllamaProvider(ollama_base)

        def _fallback() -> AsyncGenerator[str, None]:
            return OpenRouterProvider().generate_stream(
                messages,
                model=openrouter_fb,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        async for chunk in _stream_with_fallback(
            op.generate_stream(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            ),
            _fallback,
        ):
            yield chunk
        return

    if provider == "openai":
        def _fallback() -> AsyncGenerator[str, None]:
            return OpenRouterProvider().generate_stream(
                messages,
                model=openrouter_fb,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        async for chunk in _stream_with_fallback(
            _openai_stream(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            ),
            _fallback,
        ):
            yield chunk
        return

    orp = OpenRouterProvider()
    async for chunk in _stream_with_fallback(
        orp.generate_stream(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
        None,
    ):
        yield chunk


def chat_completion_global_sync(
    messages: list[dict[str, Any]],
    *,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 250,
    timeout_s: float = 25.0,
) -> str:
    """Синхронный вызов (редкие проверки в learning_service)."""
    provider = get_effective_provider()
    s = get_settings()
    ollama_base = (s.ollama_base_url or "http://localhost:11434").rstrip("/")
    openrouter_fb = _openrouter_fallback_model()
    openai_fb = _openai_fallback_model()

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
                    openrouter_fb,
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout_s=timeout_s,
                )
            except Exception:
                log.debug("OpenRouter sync fallback failed", exc_info=True)
                return ""

    if provider == "openai":
        try:
            return _openai_chat_sync(
                model,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
            )
        except Exception as e:
            log.warning("OpenAI sync failed, fallback OpenRouter: %s", e)
            try:
                return _openrouter_chat_sync(
                    openrouter_fb,
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout_s=timeout_s,
                )
            except Exception:
                log.debug("OpenRouter sync fallback failed, retry OpenAI fallback", exc_info=True)
                try:
                    return _openai_chat_sync(
                        openai_fb,
                        messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout_s=timeout_s,
                    )
                except Exception:
                    log.debug("OpenAI sync fallback failed", exc_info=True)
                    return ""

    try:
        return _openrouter_chat_sync(
            model, messages, temperature=temperature, max_tokens=max_tokens, timeout_s=timeout_s
        )
    except Exception:
        log.debug("OpenRouter sync failed", exc_info=True)
        return ""
