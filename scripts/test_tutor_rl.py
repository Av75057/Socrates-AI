#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.llm.ollama_provider import OllamaProvider

BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get("OLLAMA_TUTOR_MODEL", "socrates-tutor-rl")


async def test() -> None:
    provider = OllamaProvider(base_url=BASE_URL, default_model=MODEL)
    messages = [
        {
            "role": "system",
            "content": (
                "Ты сократический тьютор по математике. "
                "Никогда не решай задачу полностью и не давай финальный ответ. "
                "Отвечай только короткой реакцией и одним наводящим вопросом."
            ),
        },
        {"role": "user", "content": "Помоги решить уравнение 3x + 5 = 20"},
    ]
    async for chunk in provider.generate_stream(messages):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(test())
