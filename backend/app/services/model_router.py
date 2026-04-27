"""
Model Router: выбор модели, вызов OpenRouter / Ollama / OpenAI-совместимого API, валидация, fallback.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, AsyncGenerator

import httpx

from app.config import get_settings
from app.services.llm.global_call import (
    LLM_UNAVAILABLE,
    chat_completion_global_async,
    chat_completion_global_stream_async,
)
from app.services.llm.runtime import get_effective_ollama_model, get_effective_provider
from app.services.response_validator import validate_response


def _http_error_message(exc: httpx.HTTPStatusError, *, openrouter: bool) -> str:
    prefix = "[OpenRouter]" if openrouter else "[LLM]"
    code = exc.response.status_code
    if openrouter and code == 402:
        return (
            "[OpenRouter] Нет оплаты или баланса (402). "
            "Проверь биллинг на https://openrouter.ai и ключ OPENROUTER_API_KEY."
        )
    if code == 401:
        return f"{prefix} Неверный API-ключ (401)."
    if code == 429:
        return f"{prefix} Слишком много запросов (429). Подожди и повтори."
    try:
        body = exc.response.json()
        err = body.get("error")
        if isinstance(err, dict) and err.get("message"):
            return f"{prefix} {code}: {err['message']}"
        if isinstance(err, str):
            return f"{prefix} {code}: {err}"
    except Exception:
        pass
    return f"{prefix} Ошибка HTTP {code}. Попробуй позже."


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty json response")
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError("json object not found")
    parsed = json.loads(match.group())
    if not isinstance(parsed, dict):
        raise ValueError("json payload is not an object")
    return parsed


class ModelRouter:
    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        http_referer: str | None = None,
        x_title: str | None = None,
        timeout_s: float = 60.0,
        custom_model_name: str | None = None,
        use_openrouter_headers: bool | None = None,
    ) -> None:
        settings = get_settings()
        provider = get_effective_provider()
        default_key = settings.openai_api_key if provider == "openai" else os.getenv("OPENROUTER_API_KEY", "")
        default_url = (
            settings.openai_api_url
            if provider == "openai"
            else os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
        )
        self._provider = provider
        self._api_key = (api_key if api_key is not None else default_key) or ""
        raw_url = (api_url or default_url).rstrip("/")
        if not raw_url.endswith("/chat/completions"):
            self._api_url = f"{raw_url.rstrip('/')}/chat/completions"
        else:
            self._api_url = raw_url
        self._http_referer = http_referer or os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:5173")
        self._x_title = x_title or os.getenv("OPENROUTER_X_TITLE", "Socrates AI")
        self._timeout_s = timeout_s
        self._custom_model_name = (custom_model_name or "").strip() or None
        if use_openrouter_headers is None:
            self._use_openrouter_headers = "openrouter.ai" in self._api_url.lower()
        else:
            self._use_openrouter_headers = use_openrouter_headers
        self._openrouter_brand = "openrouter.ai" in self._api_url.lower()

    def _headers(self) -> dict[str, str]:
        key = self._api_key or "sk-no-key-required"
        h: dict[str, str] = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if self._use_openrouter_headers:
            h["HTTP-Referer"] = self._http_referer
            h["X-Title"] = self._x_title
        return h

    def _uses_user_llm_endpoint(self) -> bool:
        """Свой URL+модель из настроек пользователя (OpenAI-compatible)."""
        return self._custom_model_name is not None or self._provider == "openai"

    def select_model(self, mode: str) -> str:
        settings = get_settings()
        if self._custom_model_name:
            return self._custom_model_name
        if self._provider == "ollama":
            om = get_effective_ollama_model()
            if mode == "question":
                return os.getenv("OLLAMA_MODEL_QUESTION") or om
            if mode == "hint":
                return os.getenv("OLLAMA_MODEL_HINT") or om
            return os.getenv("OLLAMA_MODEL_EXPLAIN") or om
        if self._provider == "openai":
            if mode == "question":
                return settings.openai_model_question
            if mode == "hint":
                return settings.openai_model_hint
            return settings.openai_model_explain
        if mode == "question":
            return os.getenv("OPENROUTER_MODEL_QUESTION", "deepseek/deepseek-chat")
        if mode == "hint":
            return os.getenv("OPENROUTER_MODEL_HINT", "openrouter/auto")
        return os.getenv("OPENROUTER_MODEL_EXPLAIN", "deepseek/deepseek-chat")

    def _fallback_model(self) -> str:
        settings = get_settings()
        if self._custom_model_name:
            return self._custom_model_name
        if self._provider == "openai":
            return settings.openai_model_fallback
        return os.getenv("OPENROUTER_MODEL_FALLBACK", "openrouter/auto")

    def pedagogy_model(self) -> str:
        settings = get_settings()
        if self._custom_model_name:
            return self._custom_model_name
        if self._provider == "ollama":
            return os.getenv("OLLAMA_MODEL_PEDAGOGY") or get_effective_ollama_model()
        if self._provider == "openai":
            return settings.openai_model_pedagogy
        return os.getenv("OPENROUTER_MODEL_PEDAGOGY", "google/gemini-2.0-flash-001")

    def is_valid(self, response: str, mode: str) -> bool:
        return validate_response(response, mode)

    @staticmethod
    def _generation_budget(mode: str) -> int:
        return int(get_settings().llm_max_tokens)

    async def _call_user_endpoint(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        if not self._api_key:
            if self._provider == "openai":
                return (
                    "[LLM] Задайте OPENAI_API_KEY в backend/.env. "
                    "Пока опиши своими словами, что ты уже понимаешь по теме."
                )
            if self._openrouter_brand:
                return (
                    "[OpenRouter] Задайте OPENROUTER_API_KEY в backend/.env. "
                    "Пока опиши своими словами, что ты уже понимаешь по теме."
                )
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = self._headers()
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            r = await client.post(self._api_url, json=payload, headers=headers)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                return _http_error_message(e, openrouter=self._openrouter_brand)
            data = r.json()
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("empty choices")
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        return (content or "").strip() or "…"

    async def call_model(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 250,
    ) -> str:
        if self._uses_user_llm_endpoint():
            return await self._call_user_endpoint(
                messages, model, temperature=temperature, max_tokens=max_tokens
            )
        return await chat_completion_global_async(
            messages, model=model, temperature=temperature, max_tokens=max_tokens
        )

    async def call_model_json(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 300,
    ) -> dict[str, Any]:
        raw = await self.call_model(
            messages,
            model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return _extract_json_object(raw)

    @staticmethod
    def parse_json_object(text: str) -> dict[str, Any]:
        return _extract_json_object(text)

    async def _call_user_endpoint_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        if not self._api_key:
            if self._provider == "openai":
                yield (
                    "[LLM] Задайте OPENAI_API_KEY в backend/.env. "
                    "Пока опиши своими словами, что ты уже понимаешь по теме."
                )
                return
            if self._openrouter_brand:
                yield (
                    "[OpenRouter] Задайте OPENROUTER_API_KEY в backend/.env. "
                    "Пока опиши своими словами, что ты уже понимаешь по теме."
                )
                return
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = self._headers()
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            async with client.stream("POST", self._api_url, json=payload, headers=headers) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    yield _http_error_message(e, openrouter=self._openrouter_brand)
                    return
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

    async def call_model_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 250,
    ) -> AsyncGenerator[str, None]:
        if self._uses_user_llm_endpoint():
            async for chunk in self._call_user_endpoint_stream(
                messages,
                model,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield chunk
            return
        async for chunk in chat_completion_global_stream_async(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk

    async def generate(self, system_prompt: str, user_message: str, mode: str) -> str:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        primary = self.select_model(mode)
        max_tokens = self._generation_budget(mode)

        try:
            response = await self.call_model(messages, primary, max_tokens=max_tokens)
            if response != LLM_UNAVAILABLE and self.is_valid(response, mode):
                return response
        except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError):
            pass

        try:
            fallback = await self.call_model(messages, self._fallback_model(), max_tokens=max_tokens)
            if fallback != LLM_UNAVAILABLE and self.is_valid(fallback, mode):
                return fallback
        except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError):
            pass

        return "Попробуй объяснить это своими словами по-русски."

    async def generate_stream(
        self,
        system_prompt: str,
        user_message: str,
        mode: str,
    ) -> AsyncGenerator[str, None]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        primary = self.select_model(mode)
        max_tokens = self._generation_budget(mode)
        yielded = False

        try:
            async for chunk in self.call_model_stream(messages, primary, max_tokens=max_tokens):
                if not chunk:
                    continue
                yielded = True
                yield chunk
            return
        except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError):
            if yielded:
                raise

        try:
            async for chunk in self.call_model_stream(messages, self._fallback_model(), max_tokens=max_tokens):
                if not chunk:
                    continue
                yielded = True
                yield chunk
            return
        except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError):
            if yielded:
                raise

        yield "Попробуй объяснить это своими словами по-русски."

    async def call_pedagogy_llm(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if self._uses_user_llm_endpoint():
            if not self._api_key:
                return "{}"
            model = self.pedagogy_model()
            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": 0.15,
                "max_tokens": 450,
            }
            headers = self._headers()
            async with httpx.AsyncClient(timeout=min(self._timeout_s, 45.0)) as client:
                r = await client.post(self._api_url, json=payload, headers=headers)
                try:
                    r.raise_for_status()
                except httpx.HTTPStatusError:
                    return "{}"
                data = r.json()
            choices = data.get("choices") or []
            if not choices:
                return "{}"
            msg = choices[0].get("message") or {}
            content = msg.get("content")
            return (content or "").strip() or "{}"

        model = self.pedagogy_model()
        resp = await chat_completion_global_async(
            messages,
            model=model,
            temperature=0.15,
            max_tokens=450,
        )
        if not resp or resp == LLM_UNAVAILABLE or resp.startswith("[LLM]"):
            return "{}"
        return resp.strip() or "{}"
