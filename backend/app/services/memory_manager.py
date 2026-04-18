"""Обновление памяти и текст для промпта."""

from __future__ import annotations

from app.models.state import TutorState
from app.models.user_memory import UserMemory


def detect_mistake(user_message: str, topic: str) -> str | None:
    low = (user_message or "").lower()
    tlow = (topic or "").lower()

    if "масса" in low and "сила" not in low:
        if "сила" in tlow or "динамик" in tlow or "ньюто" in tlow or not topic.strip():
            return "путает или смешивает массу и силу"

    if "скорост" in low and "ускорен" not in low:
        if "ускорен" in tlow or "кинематик" in tlow:
            return "возможная путаница скорости и ускорения"

    if "импульс" in tlow and "сила" in low and "импульс" not in low:
        return "в ответе про импульс упоминается сила без связи с импульсом"

    return None


def _mistake_exists(memory: UserMemory, topic: str, error: str) -> bool:
    for m in memory.mistakes:
        if m.get("error") == error and (m.get("topic") or "") == (topic or ""):
            return True
    return False


def format_memory_for_prompt(
    memory: UserMemory,
    state: TutorState,
    user_message: str,
    is_first_attempt_in_session: bool,
) -> str:
    """Текстовый блок в system prompt (кратко, без «базы данных» в ответе)."""
    topic = (state.topic or "").strip()
    low_msg = (user_message or "").lower()
    lines: list[str] = []
    nudges: list[str] = []

    if memory.topics:
        lines.append(f"Ранее пользователь уже занимался темами: {', '.join(memory.topics)}.")

    if memory.mistakes:
        recent = memory.mistakes[-5:]
        m_str = "; ".join(
            f"{m.get('topic', '?')}: {m.get('error', '')}" for m in recent if m.get("error")
        )
        if m_str:
            lines.append(f"Зафиксированные типичные затруднения: {m_str}.")

    if memory.progress:
        prog = ", ".join(f"{k}: {v}" for k, v in list(memory.progress.items())[-8:])
        lines.append(f"Прогресс по темам: {prog}.")

    revisiting = bool(topic and topic in memory.topics and is_first_attempt_in_session)
    if revisiting:
        nudges.append(
            "Пользователь снова выбрал тему, с которой уже работал раньше — "
            "мягко свяжи с прошлым («мы уже касались этого — помнишь?»), одной короткой фразой."
        )

    mistake = detect_mistake(user_message, topic)
    if mistake and topic and _mistake_exists(memory, topic, mistake):
        nudges.append(
            "Похоже, снова тот же тип путаницы — разбери под другим углом, без давления и без слова «неправильно»."
        )
    elif mistake and mistake in (m.get("error") for m in memory.mistakes):
        nudges.append("Это напоминает уже известное затруднение — дай другой пример или шаг.")

    if any(x in low_msg for x in ("туплю", "не понимаю", "опять не", "снова не")):
        nudges.append(
            "Пользователь снова застрял на похожем месте — предложи упростить шаг или разбить на микро-вопрос."
        )

    if topic and memory.progress.get(topic) == "completed":
        nudges.append(
            "По этой теме уже отмечен прогресс — можно мягко напомнить, что пользователь уже продвинулся."
        )

    if not lines and not nudges:
        return ""

    parts = ["Долговременная память о пользователе (для тебя, не цитируй дословно списком):"]
    parts.extend(lines)
    if nudges:
        parts.append("Указания по ситуации:")
        parts.extend(f"- {n}" for n in nudges)
    parts.append(
        "Используй это естественно, максимум одна короткая отсылка в ответе, без пересказа всей памяти."
    )
    return "\n".join(parts)


def update_memory_after_turn(
    memory: UserMemory,
    state: TutorState,
    user_message: str,
    reply_mode: str,
) -> UserMemory:
    topic = (state.topic or "").strip()

    if topic:
        if topic not in memory.topics:
            memory.topics.append(topic)
        if len(memory.topics) > 50:
            memory.topics = memory.topics[-50:]

        prev = memory.progress.get(topic) or "not_started"
        if reply_mode == "explain":
            memory.progress[topic] = "completed"
        elif prev != "completed":
            memory.progress[topic] = "in_progress"

    memory.user_type = state.user_type if state.user_type in ("lazy", "anxious", "thinker") else "lazy"

    mistake = detect_mistake(user_message, topic)
    if mistake and topic and not _mistake_exists(memory, topic, mistake):
        memory.mistakes.append({"topic": topic, "error": mistake})
    if len(memory.mistakes) > 40:
        memory.mistakes = memory.mistakes[-40:]

    return memory
