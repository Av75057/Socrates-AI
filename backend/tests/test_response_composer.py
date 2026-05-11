from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.services.response_composer import TutorResponseComposer, guard_tutor_reply
from app.services.state_machine import DialoguePhase


class _FakeMemory:
    def __init__(self, *, user_type: str = "lazy") -> None:
        self.user_type = user_type
        self.skill_status = {"algebra": "ok"}

    def to_dict(self):
        return {
            "topics": ["fractions"],
            "mistakes": [],
            "progress": {"fractions": "started"},
            "user_type": self.user_type,
            "skill_status": dict(self.skill_status),
            "thinking_profile": {"pace": "steady"},
        }


class _FakeController:
    def __init__(self, reply: str = "Сначала подумай о знаменателе.") -> None:
        self.reply = reply
        self.commit_calls: list[tuple[object, object, str]] = []

    async def finalize_planned_reply(self, state, plan, raw_reply, allow_retry=True):
        return self.reply

    def commit_turn(self, state, plan, guarded_reply: str) -> None:
        self.commit_calls.append((state, plan, guarded_reply))


def _build_context(
    *,
    action: str = "none",
    msg_stripped: str = "мой ответ",
    cheat: bool = False,
    idle_turn: bool = False,
    analysis: dict | None = None,
    attempts: int = 1,
    current_phase: DialoguePhase = DialoguePhase.AWAITING_ANSWER,
):
    return SimpleNamespace(
        body=SimpleNamespace(
            action=action,
            message="мой ответ",
            session_id="sess-1",
            client_message_id="cmid-1",
        ),
        state=SimpleNamespace(
            attempts=attempts,
            frustration=1,
            user_type="lazy",
            topic="fractions",
            topic_id=101,
            mode="question",
            phase=current_phase,
        ),
        current_phase=current_phase,
        msg_stripped=msg_stripped,
        cheat=cheat,
        idle_turn=idle_turn,
        analysis=analysis,
        memory=_FakeMemory(),
        prev_skill={"algebra": "ok"},
        pedagogy_state=SimpleNamespace(
            mode="friendly",
            difficulty_level=2,
            last_response_depth=0.25,
        ),
        original_reply="",
        guarded_reply="",
        reply_mode="",
        db_user=None,
        active_conversation_id=None,
        tutor_state={},
        latency_ms=12,
    )


class TestTutorResponseComposer(unittest.IsolatedAsyncioTestCase):
    def test_determine_outcome_phase_returns_correct_for_deep_answer(self) -> None:
        composer = TutorResponseComposer()
        context = _build_context(analysis={"depth_combined": 0.8})

        phase = composer.determine_outcome_phase(context)

        self.assertEqual(phase, DialoguePhase.CORRECT)

    def test_determine_outcome_phase_returns_give_up_after_fourth_attempt(self) -> None:
        composer = TutorResponseComposer()
        context = _build_context(analysis={"depth_combined": 0.4}, attempts=4)

        phase = composer.determine_outcome_phase(context)

        self.assertEqual(phase, DialoguePhase.GIVE_UP)

    def test_determine_outcome_phase_preserves_phase_for_empty_or_cheat_turn(self) -> None:
        composer = TutorResponseComposer()

        self.assertEqual(
            composer.determine_outcome_phase(_build_context(msg_stripped="", current_phase=DialoguePhase.HINT_PROVIDED)),
            DialoguePhase.HINT_PROVIDED,
        )
        self.assertEqual(
            composer.determine_outcome_phase(_build_context(cheat=True, current_phase=DialoguePhase.INCORRECT_RETRY)),
            DialoguePhase.INCORRECT_RETRY,
        )

    def test_guard_tutor_reply_replaces_invalid_reply(self) -> None:
        with patch("app.services.response_composer.is_tutor_answering_for_student", return_value=True), patch(
            "app.services.response_composer.is_invalid_tutor_reply", return_value=False
        ):
            guarded = guard_tutor_reply("42", session_id="sess-1", conversation_id=11, source="chat")

        self.assertEqual(guarded, "Хорошо. С какой математической задачи начнём?")

    async def test_compose_updates_response_and_applies_depth_adjustment(self) -> None:
        composer = TutorResponseComposer()
        controller = _FakeController(reply="Попробуй ещё раз и сравни дроби.")
        plan = SimpleNamespace(mode="question")
        context = _build_context(analysis={"depth_combined": 0.6, "has_fallacy": False})
        updated_memory = _FakeMemory()
        composer._build_skill_tree = Mock(return_value={"track": "math"})  # type: ignore[method-assign]
        composer._persist_conversation_turn = AsyncMock(return_value=(10, 11))  # type: ignore[method-assign]

        with patch("app.services.response_composer.update_memory_after_turn", return_value=updated_memory) as update_memory, patch(
            "app.services.response_composer.apply_after_user_turn"
        ) as after_turn, patch("app.services.response_composer.apply_hint_penalty") as hint_penalty:
            response = await composer.compose(context, controller, plan, "raw-reply", source="chat")

        self.assertEqual(response.reply, "Попробуй ещё раз и сравни дроби.")
        self.assertEqual(response.mode, "question")
        self.assertEqual(response.persisted_user_message_id, 10)
        self.assertEqual(response.persisted_assistant_message_id, 11)
        self.assertEqual(response.conversation_id, None)
        self.assertEqual(response.session_key, "sess-1")
        self.assertEqual(response.skill_tree, {"track": "math"})
        self.assertEqual(response.memory.user_type, "lazy")
        self.assertEqual(context.original_reply, "Попробуй ещё раз и сравни дроби.")
        self.assertEqual(context.guarded_reply, "Попробуй ещё раз и сравни дроби.")
        self.assertEqual(context.reply_mode, "question")
        self.assertEqual(context.state.mode, "question")
        self.assertEqual(len(controller.commit_calls), 1)
        update_memory.assert_called_once()
        after_turn.assert_called_once_with(context.pedagogy_state, 0.6)
        hint_penalty.assert_not_called()

    async def test_compose_applies_hint_penalty_on_hint_action(self) -> None:
        composer = TutorResponseComposer()
        controller = _FakeController(reply="Подумай, что меняется только сверху.")
        plan = SimpleNamespace(mode="hint")
        context = _build_context(action="hint", msg_stripped="нужна подсказка", analysis=None)
        composer._build_skill_tree = Mock(return_value={})  # type: ignore[method-assign]
        composer._persist_conversation_turn = AsyncMock(return_value=None)  # type: ignore[method-assign]

        with patch("app.services.response_composer.update_memory_after_turn", return_value=context.memory), patch(
            "app.services.response_composer.apply_after_user_turn"
        ) as after_turn, patch("app.services.response_composer.apply_hint_penalty") as hint_penalty:
            response = await composer.compose(context, controller, plan, "raw-reply", source="chat")

        self.assertEqual(response.mode, "hint")
        hint_penalty.assert_called_once_with(context.pedagogy_state)
        after_turn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
