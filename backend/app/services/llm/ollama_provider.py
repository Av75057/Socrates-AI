from __future__ import annotations

import json
import re
from typing import Any, AsyncGenerator

import httpx

from app.config import get_settings
from app.services.llm.base import BaseLLMProvider

_THINK_TAG_RE = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)


def strip_thinking_tags(text: str, *, trim: bool = True) -> str:
    cleaned = _THINK_TAG_RE.sub("", text or "")
    return cleaned.strip() if trim else cleaned


class OllamaProvider(BaseLLMProvider):
    def __init__(
        self,
        base_url: str,
        timeout_s: float = 120.0,
        default_model: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s
        self._default_model = (default_model or "").strip() or None

    def _resolve_model(self, model: str | None) -> str:
        resolved = (model or self._default_model or "").strip()
        if not resolved:
            raise ValueError("model is required")
        return resolved

    @staticmethod
    def _sanitize_content(content: str | None) -> str:
        return strip_thinking_tags(content or "") or "…"

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> str:
        settings = get_settings()
        url = f"{self._base_url}/api/chat"
        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": float(temperature if temperature is not None else settings.llm_temperature),
                "top_p": settings.llm_top_p,
                "repeat_penalty": settings.llm_repeat_penalty,
                "num_predict": int(max_tokens if max_tokens is not None else settings.llm_max_tokens),
            },
        }
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        msg = data.get("message") or {}
        content = msg.get("content")
        return self._sanitize_content(content)

    async def generate_stream(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> AsyncGenerator[str, None]:
        settings = get_settings()
        url = f"{self._base_url}/api/chat"
        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": float(temperature if temperature is not None else settings.llm_temperature),
                "top_p": settings.llm_top_p,
                "repeat_penalty": settings.llm_repeat_penalty,
                "num_predict": int(max_tokens if max_tokens is not None else settings.llm_max_tokens),
            },
        }
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    message = data.get("message") or {}
                    content = message.get("content")
                    if isinstance(content, str) and content:
                        sanitized = strip_thinking_tags(content, trim=False)
                        if sanitized:
                            yield sanitized
                    if data.get("done"):
                        break
