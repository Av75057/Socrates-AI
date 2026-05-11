"""Правила системного промпта тьютора и эвристики валидации ответа."""

from __future__ import annotations

import re
from typing import Any

from app.models.pedagogy import TutorMode

_TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9]+")
_STUDENT_ANSWER_PATTERNS = (
    re.compile(r"\bученик мог бы ответить\b"),
    re.compile(r"\bученик мог бы сказать\b"),
    re.compile(r"\bнапример,?\s+ученик скажет\b"),
    re.compile(r"\bправильный ответ\b"),
    re.compile(r"\bправильно было бы сказать\b"),
    re.compile(r"(^|\n)\s*ответ\s*:"),
)
_DIRECT_SOLUTION_PATTERNS = (
    re.compile(r"\bвыполним\s+следующие\s+шаги\b"),
    re.compile(r"\bрешение\b\s*[:\-]?"),
    re.compile(r"\bсначала\s+(?:вычтем|прибавим|разделим|умножим|перенес[её]м)\b"),
    re.compile(r"\bтеперь\s+(?:вычтем|прибавим|разделим|умножим|перенес[её]м)\b"),
    re.compile(r"\bполучим\s+[a-zа-яё]\s*=\s*[-+]?\d"),
    re.compile(r"\bзначит\s+[a-zа-яё]\s*=\s*[-+]?\d"),
    re.compile(r"\bтаким\s+образом\b"),
)
_DIRECT_SOLUTION_EQUATION_RE = re.compile(r"\b[a-zа-яё]\s*=\s*[-+]?\d+(?:[.,]\d+)?\b")
_NON_TUTOR_REPLY_PATTERNS = (
    re.compile(r"translate\s+this\s+to\s+english", re.IGNORECASE),
    re.compile(r"the english translation", re.IGNORECASE),
    re.compile(r"translation of the (?:given phrase|response)", re.IGNORECASE),
    re.compile(r"for your convenience", re.IGNORECASE),
    re.compile(r"you're welcome", re.IGNORECASE),
    re.compile(r"feel free to ask", re.IGNORECASE),
    re.compile(r"\bпродифференциру", re.IGNORECASE),
    re.compile(r"\bпроизводн", re.IGNORECASE),
    re.compile(r"\bd/dx\b", re.IGNORECASE),
    re.compile(r"\be\^\(", re.IGNORECASE),
    re.compile(r"\b\d+\s+голос(?:ов|а)?\b", re.IGNORECASE),
    re.compile(r"\bлучший\s+ответ\b", re.IGNORECASE),
    re.compile(r"\bв\s+категории\b", re.IGNORECASE),
    re.compile(r"\b\d+\s+просмотр(?:ов|а)?\b", re.IGNORECASE),
    re.compile(r"\bответ\s+выбран\s+как\s+правильный\b", re.IGNORECASE),
    re.compile(r"\bкомментарии\s*:\b", re.IGNORECASE),
    re.compile(r"\bвопрос\s+задан\b", re.IGNORECASE),
)
_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF]")
_LATIN_WORD_RE = re.compile(r"\b[a-z]{3,}\b", re.IGNORECASE)
_CYRILLIC_WORD_RE = re.compile(r"\b[а-яё]{3,}\b", re.IGNORECASE)

_MODE_DESCRIPTIONS = {
    TutorMode.STRICT.value: (
        "строгий экзаменатор. Будь краток, не давай готовых ответов и длинных подсказок. "
        "При правильном ответе сразу усложняй вопрос."
    ),
    TutorMode.FRIENDLY.value: (
        "дружелюбный наставник. Поддерживай за попытки, можешь дать небольшой намёк, "
        "но не повторяй вопросы и не застревай на одном шаге."
    ),
    TutorMode.PROVOCATEUR.value: (
        "провокатор. Атакуй слабые места аргумента, задавай каверзные вопросы, "
        "но не повторяй один и тот же вопрос подряд."
    ),
}


def build_socratic_system_prompt(
    level: int = 2,
    mode: str = "friendly",
    topic: str = "обсуждаемая тема",
    last_fallacy: str = "нет",
    step_count: int = 0,
    attempted_concepts: list[str] | None = None,
) -> str:
    attempted_str = ", ".join([str(x).strip() for x in (attempted_concepts or []) if str(x).strip()]) or "нет"
    return f"""
Ты — Сократический тьютор по математике Socrates-AI. Твоя задача — развивать критическое мышление пользователя, задавая наводящие вопросы.
НИКОГДА не давай готовых ответов, не объясняй тему напрямую и не подводи итоги за пользователя.
Ты отвечаешь только на русском языке.

ПРАВИЛА ПОВЕДЕНИЯ:
1. Задавай максимум 1 вопрос за раз.
2. Только пользователь может давать ответы. Ты НИКОГДА не отвечаешь на свои вопросы и не говоришь от имени ученика.
3. Если пользователь отвечает поверхностно — проси пример, уточнение или контраргумент.
4. Если пользователь ошибается логически — мягко укажи на паттерн ошибки и спроси: «Как можно переформулировать мысль, чтобы избежать этой ловушки?»
5. Адаптируй сложность: уровень {level}/5. На низких уровнях используй аналогии, на высоких — требуй структуры и доказательств.
6. Тон: {mode}. Не выходи за рамки режима.
7. Работай только в рамках математики и текущей темы диалога.
8. Не задавай повторно тот же вопрос, если пользователь уже сделал шаг вперёд.

ТЕКУЩИЙ КОНТЕКСТ:
- Тема диалога: {topic}
- Последняя ошибка: {last_fallacy}
- Шагов в диалоге: {step_count}
- Пользователь уже пробовал: {attempted_str}

ФОРМАТ ОТВЕТА:
[Анализ] Одно короткое предложение: что пользователь сделал правильно или где ошибся.
[Вопрос] Ровно один наводящий вопрос.
[Подсказка] Только если пользователь явно просит подсказку.

НЕЛЬЗЯ:
- Давать определения, формулы и готовые решения
- Задавать больше одного вопроса
- Использовать фразы «Правильный ответ:», «как я уже говорил», «подведём итог»
- Менять тему без запроса пользователя

ПРИМЕРЫ ЗАПРЕЩЁННЫХ ФРАЗ:
❌ «Правильный ответ — 42»
❌ «Давай я объясню тему...»
❌ «Как я уже говорил ранее...»
❌ «Подведём итог: ты сказал, что...»
""".strip()


def build_tutor_system_prompt(
    mode: str,
    difficulty: int,
    user_skills: dict[str, Any] | None = None,
    *,
    topic: str = "обсуждаемая тема",
    last_fallacy: str = "нет",
    step_count: int = 0,
    attempted_concepts: list[str] | None = None,
) -> str:
    mode_key = (mode or TutorMode.FRIENDLY.value).strip().lower()
    mode_description = _MODE_DESCRIPTIONS.get(mode_key, _MODE_DESCRIPTIONS[TutorMode.FRIENDLY.value])
    difficulty_value = max(1, min(5, int(difficulty or 1)))
    topic_text = str(topic or "обсуждаемая тема").strip() or "обсуждаемая тема"
    fallacy_text = str(last_fallacy or "нет").strip() or "нет"
    skills_note = ""
    if user_skills:
        skills_note = "\nНавыки ученика: учитывай их как фон, но всё равно двигай диалог вперёд."
    prompt = build_socratic_system_prompt(
        level=difficulty_value,
        mode=mode_description,
        topic=topic_text,
        last_fallacy=fallacy_text,
        step_count=step_count,
        attempted_concepts=attempted_concepts,
    )
    return prompt + skills_note


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(text or "") if len(token) > 1}


def is_repeating_question(new_response: str, last_question: str, threshold: float = 0.7) -> bool:
    if not (new_response or "").strip() or not (last_question or "").strip():
        return False
    words1 = _tokenize(new_response)
    words2 = _tokenize(last_question)
    if not words1 or not words2:
        return False
    intersection = words1 & words2
    union = words1 | words2
    jaccard = len(intersection) / len(union) if union else 0.0
    return jaccard >= threshold


def is_tutor_answering_for_student(response_text: str) -> bool:
    normalized = str(response_text or "").strip().lower()
    if not normalized:
        return False
    if any(pattern.search(normalized) for pattern in _STUDENT_ANSWER_PATTERNS):
        return True
    if "?" in normalized:
        return False
    if any(pattern.search(normalized) for pattern in _DIRECT_SOLUTION_PATTERNS):
        return True
    if _DIRECT_SOLUTION_EQUATION_RE.search(normalized):
        return True
    return False


def is_invalid_tutor_reply(response_text: str) -> bool:
    text = str(response_text or "").strip()
    if not text:
        return True
    lowered = text.lower()
    if any(pattern.search(lowered) for pattern in _NON_TUTOR_REPLY_PATTERNS):
        return True
    if _EMOJI_RE.search(text):
        return True
    latin_words = _LATIN_WORD_RE.findall(lowered)
    cyrillic_words = _CYRILLIC_WORD_RE.findall(lowered)
    if len(latin_words) >= 4 and len(latin_words) > len(cyrillic_words):
        return True
    return False


def postprocess_tutor_response(response_text: str, last_tutor_question: str) -> tuple[str, bool, bool, bool]:
    text = str(response_text or "").strip()
    repeated = is_repeating_question(text, last_tutor_question)
    answered_for_student = is_tutor_answering_for_student(text)
    invalid = is_invalid_tutor_reply(text)
    return text, repeated, answered_for_student, invalid
