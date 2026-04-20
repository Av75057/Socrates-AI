"""
Model Router: выбор модели, вызов OpenRouter, валидация ответа, fallback.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from app.services.response_validator import validate_response


def _openrouter_http_message(exc: httpx.HTTPStatusError) -> str:
    code = exc.response.status_code
    if code == 402:
        return (
            "[OpenRouter] Нет оплаты или баланса (402). "
            "Проверь биллинг на https://openrouter.ai и ключ OPENROUTER_API_KEY."
        )
    if code == 401:
        return "[OpenRouter] Неверный API-ключ (401). Проверь OPENROUTER_API_KEY в backend/.env."
    if code == 429:
        return "[OpenRouter] Слишком много запросов (429). Подожди и повтори."
    try:
        body = exc.response.json()
        err = body.get("error")
        if isinstance(err, dict) and err.get("message"):
            return f"[OpenRouter] {code}: {err['message']}"
        if isinstance(err, str):
            return f"[OpenRouter] {code}: {err}"
    except Exception:
        pass
    return f"[OpenRouter] Ошибка HTTP {code}. Попробуй позже."


class ModelRouter:
    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        http_referer: str | None = None,
        x_title: str | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self._api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self._api_url = (
            api_url or os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
        ).rstrip("/")
        if not self._api_url.endswith("/chat/completions"):
            self._api_url = f"{self._api_url.rstrip('/')}/chat/completions"
        self._http_referer = http_referer or os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:5173")
        self._x_title = x_title or os.getenv("OPENROUTER_X_TITLE", "Socrates AI")
        self._timeout_s = timeout_s

    def select_model(self, mode: str) -> str:
        if mode == "question":
            return os.getenv("OPENROUTER_MODEL_QUESTION", "deepseek/deepseek-chat")
        if mode == "hint":
            return os.getenv("OPENROUTER_MODEL_HINT", "openrouter/auto")
        return os.getenv("OPENROUTER_MODEL_EXPLAIN", "deepseek/deepseek-chat")

    def _fallback_model(self) -> str:
        return os.getenv("OPENROUTER_MODEL_FALLBACK", "openrouter/auto")

    def is_valid(self, response: str, mode: str) -> bool:
        return validate_response(response, mode)

    async def call_model(self, messages: list[dict[str, str]], model: str) -> str:
        if not self._api_key:
            return (
                "[OpenRouter] Задайте OPENROUTER_API_KEY в backend/.env. "
                "Пока опиши своими словами, что ты уже понимаешь по теме."
            )

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 300,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._http_referer,
            "X-Title": self._x_title,
        }
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            r = await client.post(self._api_url, json=payload, headers=headers)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                return _openrouter_http_message(e)
            data = r.json()

        choices = data.get("choices") or []
        if not choices:
            raise ValueError("empty choices")
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        return (content or "").strip() or "…"

    async def generate(self, system_prompt: str, user_message: str, mode: str) -> str:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        primary = self.select_model(mode)

        try:
            response = await self.call_model(messages, primary)
            if self.is_valid(response, mode):
                return response
        except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError):
            pass

        try:
            fallback = await self.call_model(messages, self._fallback_model())
            if self.is_valid(fallback, mode):
                return fallback
        except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError):
            pass

        return "Попробуй объяснить это своими словами по-русски."

    async def call_pedagogy_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Лёгкая модель для анализа ошибок и глубины (JSON в ответе)."""
        if not self._api_key:
            return "{}"
        model = os.getenv("OPENROUTER_MODEL_PEDAGOGY", "google/gemini-2.0-flash-001")
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.15,
            "max_tokens": 450,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._http_referer,
            "X-Title": self._x_title,
        }
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
