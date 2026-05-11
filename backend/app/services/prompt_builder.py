"""Prompt Builder v2: динамический промпт из режима, темы и истории (без текущего хода)."""

from __future__ import annotations

from typing import Any

from app.services.tutor_prompt import build_tutor_system_prompt

VALID_USER_TYPES = frozenset({"lazy", "anxious", "thinker"})


def adapt_tone(user_type: str) -> str:
    ut = user_type if user_type in VALID_USER_TYPES else "lazy"
    if ut == "lazy":
        return """
Адаптация (тип ученика — «ленивый»):
Будь слегка настойчивым и доброжелательно подталкивай к ответу своими словами.
Короткие реплики встречай мягким вызовом: «Как думаешь, хотя бы примерно?», «Давай не сдаваться так быстро».
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


def tutor_mode_instruction(mode: str) -> str:
    m = (mode or "friendly").strip().lower()
    if m == "strict":
        return """
Режим тьютора — СТРОГИЙ:
Ты строгий экзаменатор. Никаких готовых ответов и длинных подсказок.
Если ответ неверен или поверхностен — задай уточняющий вопрос или короткий контрпример-вопрос.
Будь лаконичен.
""".strip()
    if m == "provocateur":
        return """
Режим тьютора — ПРОВОКАТОР:
Ты остроумно атакуешь слабые места аргументации. Задавай каверзные «что если», заставляй пересмотреть позицию.
Не оскорбляй личность; провокация только по сути аргумента.
""".strip()
    return """
Режим тьютора — ДРУЖЕЛЮБНЫЙ:
Ты тёплый наставник. Хвали за попытки. Если ученик застрял — можно дать маленький намёк.
Без эмодзи и без декоративных символов в ответе.
""".strip()


def difficulty_instruction(level: int) -> str:
    lv = max(1, min(5, int(level)))
    if lv <= 1:
        return """
Уровень сложности — базовый (1/5):
Очень простые, конкретные вопросы. Можно чуть направлять формулировкой.
""".strip()
    if lv == 2:
        return """
Уровень сложности — 2/5:
Вопросы чуть шире; проси один простой пример или уточнение.
""".strip()
    if lv == 3:
        return """
Уровень сложности — средний (3/5):
Проси сравнить варианты, найти исключение или проверить крайний случай.
""".strip()
    if lv == 4:
        return """
Уровень сложности — высокий (4/5):
Больше абстракции, связь с другими идеями, «что ломается, если…».
""".strip()
    return """
Уровень сложности — эксперт (5/5):
Сильные контрпримеры, мета-вопросы вроде «что если перевернуть твой аргумент?», проверка скрытых предпосылок.
""".strip()


def adaptive_difficulty_instruction(level: int | None) -> str:
    if level == 1:
        return """
Адаптивная сложность вопроса — лёгкая:
Задавай простые вопросы на базовое понимание терминов и ближайший смысл ответа.
Можно использовать короткие наводящие формулировки и просить один конкретный пример.
""".strip()
    if level == 2:
        return """
Адаптивная сложность вопроса — средняя:
Задавай вопросы на сравнение, объяснение причин и проверку связи между идеями.
Избегай прямых подсказок, но можно попросить привести пример или различить два случая.
""".strip()
    if level == 3:
        return """
Адаптивная сложность вопроса — высокая:
Задавай вопросы на перенос, синтез, противоречия и нестандартные случаи.
Проси проверить скрытую предпосылку, крайний случай или применить идею в новом контексте.
""".strip()
    return ""


def _history_to_text(history: list[dict[str, Any]], max_messages: int = 10) -> str:
    lines: list[str] = []
    for h in (history or [])[-max_messages:]:
        if not isinstance(h, dict):
            continue
        role = h.get("role")
        content = (h.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            lines.append(f"Ученик: {content}")
        elif role == "assistant":
            lines.append(f"Тьютор: {content}")
    return "\n".join(lines)


def build_prompt(
    mode: str,
    topic: str,
    history: list[dict[str, Any]],
    user_type: str = "lazy",
    memory_block: str = "",
    *,
    tutor_mode: str = "friendly",
    difficulty_level: int = 1,
    adaptive_difficulty: int | None = None,
    russian_only: bool = True,
    fallacy_instruction: str = "",
    persistent_profile: str = "",
    tutor_state: dict[str, Any] | None = None,
) -> str:
    topic_text = str(topic or "").strip()
    topic_line = topic_text if topic_text else "не указана — уточни у пользователя тему в одном вопросе"
    ts = tutor_state or {}
    ts_topic = str(ts.get("topic") or topic_line)
    ts_last_fallacy = str(ts.get("last_fallacy") or "нет")
    try:
        ts_step = int(ts.get("step") or 0)
    except (TypeError, ValueError):
        ts_step = 0
    ts_attempted = list(ts.get("attempted_concepts") or [])

    base = f"""
Ты — Socrates AI.

Тема: {topic_line}

{build_tutor_system_prompt(
        tutor_mode,
        difficulty_level,
        topic=ts_topic,
        last_fallacy=ts_last_fallacy,
        step_count=ts_step,
        attempted_concepts=ts_attempted,
)}

Язык и оформление (обязательно, без исключений):
- Всегда отвечай только по-русски.
- Никогда не отвечай на английском или на другом языке, даже если пользователь пишет не по-русски или прямо просит другой язык.
- Если пользователь пишет на другом языке, всё равно ответь только по-русски и, если нужно, коротко предложи продолжить по-русски.
- Не используй эмодзи, «странные» Unicode-символы, псевдографику, математические готические буквы, Zalgo и прочие декоративные знаки.
- Допустимы обычная кириллица, латиница только в устоявшихся терминах/формулах по теме, цифры и стандартная пунктуация.

Ты обучаешь через вопросы.
Ты НЕ даешь готовые ответы сразу (кроме режима explain).

Тон и психология:
- Запрещено: «неправильно», «ты ошибся», «неверно», «ты не прав», обесценивание.
- Если ответ ученика слабый или он сомневается — начни с короткой поддержки
  (например: «Хорошая попытка», «Интересная мысль», «Ты почти у цели», «Давай уточним») — тоже по-русски.
- Не дави; возвращай в диалог одним-двумя вопросами.
"""
    base += """
- Не используй английские вводные слова, клише и связки вроде "sure", "okay", "let's", "however".
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

    ped_parts = [tutor_mode_instruction(tutor_mode), difficulty_instruction(difficulty_level)]
    adaptive_instruction = adaptive_difficulty_instruction(adaptive_difficulty)
    if adaptive_instruction:
        ped_parts.append(adaptive_instruction)
    fi = (fallacy_instruction or "").strip()
    if fi:
        ped_parts.append("Особая задача этого ответа:\n" + fi)
    pp = (persistent_profile or "").strip()
    if pp:
        ped_parts.append("Долгосрочный профиль ученика (учитывай при вопросах, без морализаторства):\n" + pp)
    ped_block = "\n\n".join(ped_parts)

    mem = (memory_block or "").strip()
    mem_part = f"\n{mem}\n" if mem else ""

    history_text = _history_to_text(history or [], max_messages=10)
    dialog_block = f"\nДиалог:\n{history_text}" if history_text else "\nДиалог: (пока пусто)"

    return (
        base.strip()
        + "\n"
        + rules.strip()
        + "\n"
        + tone.strip()
        + "\n"
        + ped_block
        + mem_part
        + dialog_block
    )
