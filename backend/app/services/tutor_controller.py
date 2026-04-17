"""
Controller v2: поведение сессии. Порядок: Controller → Prompt Builder → Model Router → Validator (внутри router).
"""

from __future__ import annotations

import re
from typing import Any, Literal

from app.models.state import TutorState
from app.services.cheat_detector import CHEAT_REPLY, is_cheating
from app.services.model_router import ModelRouter
from app.services.prompt_builder import build_prompt

ChatAction = Literal["none", "hint", "give_up"]


_TOPIC_PATTERNS = [
    re.compile(r"хочу\s+изучить\s+(?P<t>.+)", re.IGNORECASE),
    re.compile(r"тема:\s*(?P<t>.+)", re.IGNORECASE),
    re.compile(r"учим\s+(?P<t>.+)", re.IGNORECASE),
]

_FRUSTRATION_MARKERS = ("не знаю", "хз", "без понятия")


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
        state.attempts += 1

        low = user_input.lower()
        if any(x in low for x in _FRUSTRATION_MARKERS):
            state.frustration += 1

        if len(user_input) > 200:
            state.frustration += 1

        state.mode = self.decide_mode(state)
        return state

    def decide_mode(self, state: TutorState) -> str:
        if state.frustration >= 2:
            return "hint"

        if state.attempts < 2:
            return "question"

        if state.attempts < 4:
            return "hint"

        return "explain"

    async def handle_turn(
        self,
        state: TutorState,
        user_message: str,
        action: ChatAction = "none",
    ) -> tuple[str, str]:
        text = (user_message or "").strip()

        if text and is_cheating(text):
            state.history.append({"role": "user", "content": text})
            state.history.append({"role": "assistant", "content": CHEAT_REPLY})
            return CHEAT_REPLY, state.mode

        if action == "give_up":
            state.mode = "explain"
            user_line = text or "(сдаюсь — нужно краткое объяснение и контрольный вопрос в конце)"
            if text:
                _maybe_set_topic(state, text)
            prompt = build_prompt(state.mode, state.topic, state.history)
            reply = await self._router.generate(prompt, user_line, state.mode)
            state.history.append({"role": "user", "content": user_line})
            state.history.append({"role": "assistant", "content": reply})
            return reply, state.mode

        if action == "hint":
            hint_line = text or "(запрошена подсказка)"
            if text:
                _maybe_set_topic(state, text)
            self.update_state(state, hint_line)
            # Явный hint при кнопке (decide_mode мог оставить question при малых attempts)
            state.mode = "explain" if state.attempts >= 4 else "hint"
            prompt = build_prompt(state.mode, state.topic, state.history)
            reply = await self._router.generate(prompt, hint_line, state.mode)
            state.history.append({"role": "user", "content": hint_line})
            state.history.append({"role": "assistant", "content": reply})
            return reply, state.mode

        if not text:
            return "Напиши сообщение или используй кнопки подсказки / сдаться.", state.mode

        _maybe_set_topic(state, text)
        self.update_state(state, text)
        prompt = build_prompt(state.mode, state.topic, state.history)
        reply = await self._router.generate(prompt, text, state.mode)
        state.history.append({"role": "user", "content": text})
        state.history.append({"role": "assistant", "content": reply})
        return reply, state.mode
