#!/usr/bin/env python3
"""Проверка локального Ollama API (http://localhost:11434)."""

from __future__ import annotations

import asyncio
import os
import sys

try:
    import httpx
except ImportError:
    print("Установите httpx: pip install httpx", file=sys.stderr)
    sys.exit(1)

BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")


async def test_ollama() -> None:
    url = f"{BASE}/api/generate"
    payload = {
        "model": MODEL,
        "prompt": "Привет! Как ты?",
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    text = data.get("response", data)
    print("Ответ модели:", text)


if __name__ == "__main__":
    asyncio.run(test_ollama())
