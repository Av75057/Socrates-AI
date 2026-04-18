"""Prompt Builder v2: динамический промпт из режима, темы и истории (без текущего хода)."""

from __future__ import annotations

from typing import Any

VALID_USER_TYPES = frozenset({"lazy", "anxious", "thinker"})


def adapt_tone(user_type: str) -> str:
    ut = user_type if user_type in VALID_USER_TYPES else "lazy"
    if ut == "lazy":
        return """
Адаптация (тип ученика — «ленивый»):
Будь слегка настойчивым и доброжелательно подталкивай к ответу своими словами.
Короткие реплики встречай мягким вызовом: «Как думаешь, хотя бы примерно?», «Давай не сдаваться так быстро 🙂».
Не раздавай готовое; чаще наводящий вопрос.
"""
    if ut == "anxious":
        return """
Адаптация (тип ученика — «тревожный»):
Будь поддерживающим и мягким; снимай страх ошибки.
Подчёркивай: ошибаться нормально, тема может быть сложной.
Меньше давления, больше похвалы за попытку. Формулировки вроде: «Ты нормально идёшь», «Это непростая тема».
"""
    return """
Адаптация (тип ученика — «думающий»):
Уважай рассуждения; усложняй и углубляй вопрос.
Можно спросить про крайний случай, контрпример или «что если».
Тон: «Интересная мысль. А если копнуть глубже?», «А есть контрпример?».
"""


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


def build_prompt(
    mode: str,
    topic: str,
    history: list[dict[str, Any]],
    user_type: str = "lazy",
) -> str:
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

    tone = adapt_tone(user_type)

    history_text = _history_to_text(history)
    dialog_block = f"\nДиалог:\n{history_text}" if history_text else "\nДиалог: (пока пусто)"

    return base.strip() + "\n" + rules.strip() + "\n" + tone.strip() + dialog_block
