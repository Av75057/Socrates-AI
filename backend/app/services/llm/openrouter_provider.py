from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator

import httpx

from app.services.llm.base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        http_referer: str | None = None,
        x_title: str | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self._api_key = (api_key if api_key is not None else os.getenv("OPENROUTER_API_KEY", "")) or ""
        raw_url = (
            api_url or os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
        ).rstrip("/")
        if not raw_url.endswith("/chat/completions"):
            self._api_url = f"{raw_url.rstrip('/')}/chat/completions"
        else:
            self._api_url = raw_url
        self._http_referer = http_referer or os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:5173")
        self._x_title = x_title or os.getenv("OPENROUTER_X_TITLE", "Socrates AI")
        self._timeout_s = timeout_s

    def _headers(self) -> dict[str, str]:
        key = self._api_key or "sk-no-key-required"
        h: dict[str, str] = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if "openrouter.ai" in self._api_url.lower():
            h["HTTP-Referer"] = self._http_referer
            h["X-Title"] = self._x_title
        return h

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> str:
        if not self._api_key and "openrouter.ai" in self._api_url.lower():
            raise ValueError("OPENROUTER_API_KEY is not set")
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            r = await client.post(self._api_url, json=payload, headers=self._headers())
            r.raise_for_status()
            data = r.json()
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("empty choices")
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        return (content or "").strip() or "…"

    async def generate_stream(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> AsyncGenerator[str, None]:
        if not self._api_key and "openrouter.ai" in self._api_url.lower():
            raise ValueError("OPENROUTER_API_KEY is not set")
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            async with client.stream("POST", self._api_url, json=payload, headers=self._headers()) as response:
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
