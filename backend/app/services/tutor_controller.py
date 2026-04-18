"""
Controller v2: поведение сессии. Порядок: Controller → Prompt Builder → Model Router → Validator (внутри router).
"""

from __future__ import annotations

import re
from typing import Any, Literal

from app.models.state import TutorState
from app.models.user_memory import UserMemory
from app.services.cheat_detector import CHEAT_REPLY, is_cheating
from app.services.memory_manager import format_memory_for_prompt
from app.services.model_router import ModelRouter
from app.services.prompt_builder import build_prompt
from app.services.user_profiler import detect_user_type

ChatAction = Literal["none", "hint", "give_up"]


_TOPIC_PATTERNS = [
    re.compile(r"хочу\s+изучить\s+(?P<t>.+)", re.IGNORECASE),
    re.compile(r"тема:\s*(?P<t>.+)", re.IGNORECASE),
    re.compile(r"учим\s+(?P<t>.+)", re.IGNORECASE),
]

_FRUSTRATION_MARKERS = ("не знаю", "хз", "без понятия")

# Не считать «застреванием» явные запросы помощи (иначе «Дай пример» крутит счётчик).
_HELP_REQUEST_MARKERS = (
    "дай пример",
    "дай подсказку",
    "подсказку",
    "запрошена подсказка",
    "сдаюсь",
    "объясни",
)


def _maybe_set_topic(state: TutorState, user_text: str) -> None:
    t = user_text.strip()
    for pat in _TOPIC_PATTERNS:
        m = pat.search(t)
        if m:
            state.topic = m.group("t").strip().rstrip(".")
            return


class TutorController:
    def __init__(self, router: ModelRouter | None = None) -> None:
        self._router = router or ModelRouter()

    def update_state(self, state: TutorState, user_input: str) -> TutorState:
        raw = (user_input or "").strip()
        low = raw.lower()
        prev_attempts = state.attempts
        state.attempts += 1

        marker = any(x in low for x in _FRUSTRATION_MARKERS)
        very_short = 0 < len(raw) < 5

        if marker or very_short:
            state.frustration += 1

        # «Застрял» после пары шагов: короткие ответы без маркеров и без явной просьбы о помощи
        help_request = any(x in low for x in _HELP_REQUEST_MARKERS)
        if prev_attempts >= 2 and 5 <= len(raw) < 15 and not marker and not help_request:
            state.frustration += 1

        if len(raw) > 200:
            state.frustration += 1

        state.mode = self.decide_mode(state)
        return state

    def decide_mode(self, state: TutorState) -> str:
        ut = getattr(state, "user_type", "lazy") or "lazy"
        if ut not in ("lazy", "anxious", "thinker"):
            ut = "lazy"

        fr_th = 3 if ut == "anxious" else 2
        if state.frustration >= fr_th:
            return "hint"

        if state.attempts < 2:
            return "question"

        if ut == "thinker":
            if state.attempts < 5:
                return "question"
            if state.attempts < 8:
                return "hint"
            return "explain"

        if ut == "lazy":
            if state.attempts < 4:
                return "hint"
            return "explain"

        if state.attempts < 4:
            return "hint"
        return "explain"

    async def handle_turn(
        self,
        state: TutorState,
        user_message: str,
        action: ChatAction = "none",
        long_term_memory: UserMemory | None = None,
    ) -> tuple[str, str]:
        text = (user_message or "").strip()
        mem = long_term_memory or UserMemory()

        if text and is_cheating(text):
            state.history.append({"role": "user", "content": text})
            state.history.append({"role": "assistant", "content": CHEAT_REPLY})
            return CHEAT_REPLY, state.mode

        if action == "give_up":
            attempts_before = state.attempts
            state.mode = "explain"
            user_line = text or "(сдаюсь — нужно краткое объяснение и контрольный вопрос в конце)"
            if text:
                state.user_type = detect_user_type(text, state.user_type)
                _maybe_set_topic(state, text)
            mb = format_memory_for_prompt(mem, state, text, attempts_before == 0)
            prompt = build_prompt(
                state.mode, state.topic, state.history, state.user_type, memory_block=mb
            )
            reply = await self._router.generate(prompt, user_line, state.mode)
            state.history.append({"role": "user", "content": user_line})
            state.history.append({"role": "assistant", "content": reply})
            return reply, state.mode

        if action == "hint":
            attempts_before = state.attempts
            hint_line = text or "(запрошена подсказка)"
            if text:
                _maybe_set_topic(state, text)
            state.user_type = detect_user_type(hint_line, state.user_type)
            mb = format_memory_for_prompt(mem, state, hint_line, attempts_before == 0)
            self.update_state(state, hint_line)
            # Явный hint при кнопке (decide_mode мог оставить question при малых attempts)
            state.mode = "explain" if state.attempts >= 4 else "hint"
            prompt = build_prompt(
                state.mode, state.topic, state.history, state.user_type, memory_block=mb
            )
            reply = await self._router.generate(prompt, hint_line, state.mode)
            state.history.append({"role": "user", "content": hint_line})
            state.history.append({"role": "assistant", "content": reply})
            return reply, state.mode

        if not text:
            return "Напиши сообщение или используй кнопки подсказки / сдаться.", state.mode

        attempts_before = state.attempts
        _maybe_set_topic(state, text)
        state.user_type = detect_user_type(text, state.user_type)
        mb = format_memory_for_prompt(mem, state, text, attempts_before == 0)
        self.update_state(state, text)
        prompt = build_prompt(
            state.mode, state.topic, state.history, state.user_type, memory_block=mb
        )
        reply = await self._router.generate(prompt, text, state.mode)
        state.history.append({"role": "user", "content": text})
        state.history.append({"role": "assistant", "content": reply})
        return reply, state.mode
