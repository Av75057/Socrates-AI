"""Prompt Builder v2: динамический промпт из режима, темы и истории (без текущего хода)."""

from __future__ import annotations

from typing import Any


def _history_to_text(history: list[dict[str, Any]], max_messages: int = 6) -> str:
    lines: list[str] = []
    for h in history[-max_messages:]:
        role = h.get("role")
        content = (h.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            lines.append(f"User: {content}")
        elif role == "assistant":
            lines.append(f"AI: {content}")
    return "\n".join(lines)


def build_prompt(mode: str, topic: str, history: list[dict[str, Any]]) -> str:
    topic_line = topic.strip() if topic.strip() else "не указана — уточни у пользователя тему в одном вопросе"

    base = f"""
Ты — Socrates AI.

Тема: {topic_line}

Ты обучаешь через вопросы.
Ты НЕ даешь готовые ответы сразу (кроме режима explain).

Тон и психология:
- Запрещено: «неправильно», «ты ошибся», «неверно», «ты не прав», обесценивание.
- Если ответ ученика слабый или он сомневается — начни с короткой поддержки
  (например: «Хорошая попытка», «Интересная мысль», «Ты почти у цели», «Давай уточним»).
- Не дави; возвращай в диалог одним-двумя вопросами.
"""

    if mode == "question":
        rules = """
Задай 1-2 коротких вопроса.
НЕ объясняй.
НЕ давай определений.
"""

    elif mode == "hint":
        rules = """
Формат подсказки (обязательно):
1) Одна короткая ситуация-пример на «ты» (1–2 предложения), близкая к теме.
2) Один наводящий вопрос в конце — чтобы мозг включился, а не получил готовый ответ.

Без морали и без длинной лекции. Максимум 4 коротких предложения суммарно.
"""

    else:
        rules = """
Дай краткое объяснение (2-3 предложения).
Потом задай контрольный вопрос.
"""

    history_text = _history_to_text(history)
    dialog_block = f"\nДиалог:\n{history_text}" if history_text else "\nДиалог: (пока пусто)"

    return base.strip() + "\n" + rules.strip() + dialog_block
