from __future__ import annotations

import json
import re
from typing import Any

from app.services.llm.global_call import chat_completion_global_async
from app.services.model_router import ModelRouter


_GENERATOR_SYSTEM_PROMPT = """Ты редактор библиотеки тем для Socrates AI.
Ответь СТРОГО одним JSON-объектом без markdown.

Поля:
- "title": короткий привлекательный заголовок темы на русском.
- "description": 1-2 предложения для карточки.
- "initial_prompt": первый вопрос тьютора, который запускает диалог.
- "difficulty": целое число от 1 до 5.
- "tags": массив из 2-5 коротких тегов на русском.

Правила:
- initial_prompt должен быть в роли сократического тьютора: только вопрос или очень короткая реакция + вопрос.
- Не пиши ответы за ученика.
- Не используй markdown и пояснения вокруг JSON.
"""


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group())
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _normalize_tags(raw: Any) -> list[str]:
    items = raw if isinstance(raw, list) else []
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        tag = str(item or "").strip().lower()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        out.append(tag[:48])
    return out[:5]


async def generate_topic_draft(seed: str) -> dict[str, Any]:
    mr = ModelRouter()
    model = mr.select_model("question")
    user_prompt = f"Сгенерируй тему для библиотеки: {seed.strip()}"
    raw = await chat_completion_global_async(
        [{"role": "system", "content": _GENERATOR_SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
        model=model,
        temperature=0.7,
        max_tokens=500,
    )
    data = _extract_json_object(raw)
    difficulty = data.get("difficulty")
    try:
        difficulty_value = int(difficulty)
    except (TypeError, ValueError):
        difficulty_value = 2
    difficulty_value = max(1, min(5, difficulty_value))
    title = str(data.get("title") or seed or "Новая тема").strip()[:255]
    description = str(data.get("description") or "").strip()[:512]
    initial_prompt = str(data.get("initial_prompt") or "").strip()
    if not initial_prompt:
        initial_prompt = f"Что тебе уже приходит в голову, когда ты слышишь тему «{title}»?"
    return {
        "title": title,
        "description": description,
        "initial_prompt": initial_prompt,
        "difficulty": difficulty_value,
        "tags": _normalize_tags(data.get("tags")),
        "model": model,
    }
