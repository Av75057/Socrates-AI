from __future__ import annotations

from typing import Any

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
    try:
        data = await mr.call_model_json(
            [{"role": "system", "content": _GENERATOR_SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
            model,
            temperature=0.7,
            max_tokens=500,
        )
    except Exception:
        data = {}
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
