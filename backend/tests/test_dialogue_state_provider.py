from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.services.dialogue_state import DialogueStateProvider
from app.services.state_machine import DialoguePhase


class _FakeMemory:
    def __init__(self, *, user_type: str = "lazy", skill_status: dict[str, str] | None = None) -> None:
        self.user_type = user_type
        self.skill_status = skill_status or {"algebra": "learning"}

    def to_dict(self):
        return {
            "topics": [],
            "mistakes": [],
            "progress": {},
            "user_type": self.user_type,
            "skill_status": dict(self.skill_status),
            "thinking_profile": {},
        }


def _build_body(
    *,
    message: str = "",
    action: str = "none",
    session_id: str = "sess-1",
    conversation_id=None,
    assignment_id=None,
    memory_user_id: str | None = None,
    client_message_id: str | None = None,
):
    return SimpleNamespace(
        message=message,
        action=action,
        session_id=session_id,
        conversation_id=conversation_id,
        assignment_id=assignment_id,
        memory_user_id=memory_user_id,
        client_message_id=client_message_id,
    )


class TestDialogueStateProvider(unittest.IsolatedAsyncioTestCase):
    async def test_load_or_create_for_anonymous_idle_turn_uses_session_memory_and_skips_conversation(self) -> None:
        provider = DialogueStateProvider()
        body = _build_body(message="   ", action="none", session_id="anon-sess")
        state = SimpleNamespace(topic="fractions", phase=DialoguePhase.GREETING, user_type="lazy")
        memory = _FakeMemory(user_type="thinker", skill_status={"fractions": "started"})
        pedagogy_state = SimpleNamespace(difficulty_level=2, mode="friendly")
        router = object()
        response_composer = Mock()

        with patch("app.services.dialogue_state.load_state", AsyncMock(return_value=state)) as load_state, patch(
            "app.services.dialogue_state.load_memory", AsyncMock(return_value=memory)
        ) as load_memory, patch(
            "app.services.dialogue_state.load_pedagogy", AsyncMock(return_value=pedagogy_state)
        ) as load_pedagogy, patch(
            "app.services.dialogue_state.is_cheating", return_value=False
        ) as is_cheating, patch.object(
            provider, "_build_router", AsyncMock(return_value=router)
        ) as build_router, patch.object(
            provider, "_load_duplicate_response", AsyncMock(return_value=None)
        ) as load_duplicate, patch.object(
            provider, "_ensure_conversation", AsyncMock()
        ) as ensure_conversation, patch.object(
            provider, "_verify_conversation_access", AsyncMock()
        ) as verify_conversation, patch.object(
            provider, "_hydrate_conversation_history", AsyncMock()
        ) as hydrate_history, patch.object(
            provider, "_hydrate_profile", AsyncMock()
        ) as hydrate_profile:
            context = await provider.load_or_create(body, object(), None, "corr-1", response_composer)

        self.assertTrue(context.idle_turn)
        self.assertFalse(context.cheat)
        self.assertEqual(context.mid, "anon-sess")
        self.assertEqual(context.prepared_turn.user_id, "anon-sess")
        self.assertEqual(context.prepared_turn.conversation_id, "")
        self.assertEqual(context.active_conversation_id, None)
        self.assertEqual(context.msg_stripped, "")
        self.assertEqual(context.current_phase, DialoguePhase.GREETING)
        self.assertEqual(context.prev_skill, {"fractions": "started"})
        self.assertEqual(context.configuration.topic, "fractions")
        self.assertEqual(context.configuration.tutor_mode, "friendly")
        self.assertTrue(context.configuration.russian_only)
        self.assertEqual(state.user_type, "thinker")
        load_state.assert_awaited_once()
        load_memory.assert_awaited_once_with(unittest.mock.ANY, "anon-sess")
        load_pedagogy.assert_awaited_once()
        is_cheating.assert_not_called()
        build_router.assert_awaited_once_with(None)
        load_duplicate.assert_awaited_once()
        ensure_conversation.assert_not_awaited()
        verify_conversation.assert_not_awaited()
        hydrate_history.assert_not_awaited()
        hydrate_profile.assert_not_awaited()

    async def test_load_or_create_for_authenticated_turn_hydrates_profile_and_duplicate_response(self) -> None:
        provider = DialogueStateProvider()
        body = _build_body(
            message="Решение такое",
            action="none",
            session_id="sess-2",
            conversation_id=None,
            assignment_id=88,
            client_message_id="client-1",
        )
        db_user = SimpleNamespace(id=7)
        state = SimpleNamespace(topic="geometry", phase=DialoguePhase.AWAITING_ANSWER, user_type="lazy")
        memory = _FakeMemory(user_type="anxious", skill_status={"geometry": "ok"})
        pedagogy_state = SimpleNamespace(difficulty_level=4, mode="friendly")
        router = object()
        duplicate_response = SimpleNamespace(mode="question", reply="cached")
        response_composer = Mock()

        with patch("app.services.dialogue_state.load_state", AsyncMock(return_value=state)), patch(
            "app.services.dialogue_state.load_memory", AsyncMock(return_value=memory)
        ), patch(
            "app.services.dialogue_state.load_pedagogy", AsyncMock(return_value=pedagogy_state)
        ), patch(
            "app.services.dialogue_state.is_cheating", return_value=True
        ) as is_cheating, patch(
            "app.services.dialogue_state.get_tutor_state", AsyncMock(return_value={"step": 6, "topic": "geometry"})
        ) as get_tutor_state, patch.object(
            provider, "_verify_assignment", AsyncMock(return_value=88)
        ) as verify_assignment, patch.object(
            provider, "_ensure_conversation", AsyncMock(return_value=321)
        ) as ensure_conversation, patch.object(
            provider, "_verify_conversation_access", AsyncMock()
        ) as verify_conversation, patch.object(
            provider, "_hydrate_conversation_history", AsyncMock()
        ) as hydrate_history, patch.object(
            provider, "_hydrate_profile", AsyncMock(return_value=("strict", "любит доказательства", False))
        ) as hydrate_profile, patch.object(
            provider, "_build_router", AsyncMock(return_value=router)
        ) as build_router, patch.object(
            provider, "_load_duplicate_response", AsyncMock(return_value=duplicate_response)
        ) as load_duplicate:
            context = await provider.load_or_create(body, object(), db_user, "corr-2", response_composer)

        self.assertFalse(context.idle_turn)
        self.assertTrue(context.cheat)
        self.assertEqual(context.mid, "7")
        self.assertEqual(context.prepared_turn.user_id, "7")
        self.assertEqual(context.prepared_turn.conversation_id, "321")
        self.assertEqual(context.active_conversation_id, 321)
        self.assertEqual(context.msg_stripped, "Решение такое")
        self.assertEqual(context.current_phase, DialoguePhase.AWAITING_ANSWER)
        self.assertEqual(context.duplicate_response, duplicate_response)
        self.assertEqual(context.prev_skill, {"geometry": "ok"})
        self.assertEqual(context.configuration.topic, "geometry")
        self.assertEqual(context.configuration.difficulty_level, 4)
        self.assertEqual(context.configuration.tutor_mode, "strict")
        self.assertFalse(context.configuration.russian_only)
        self.assertEqual(context.configuration.persistent_profile, "любит доказательства")
        self.assertEqual(context.configuration.tutor_state, {"step": 6, "topic": "geometry"})
        self.assertEqual(context.tutor_state, {"step": 6, "topic": "geometry"})
        self.assertEqual(state.user_type, "anxious")
        self.assertEqual(pedagogy_state.mode.value, "strict")
        is_cheating.assert_called_once_with("Решение такое")
        verify_assignment.assert_awaited_once_with(db_user, 88)
        ensure_conversation.assert_awaited_once_with(db_user, "sess-2", body, 88)
        verify_conversation.assert_awaited_once_with(db_user, 321, "sess-2")
        hydrate_history.assert_awaited_once_with(7, 321, state)
        hydrate_profile.assert_awaited_once_with(db_user, pedagogy_state)
        build_router.assert_awaited_once_with(db_user)
        get_tutor_state.assert_awaited_once_with(321)
        load_duplicate.assert_awaited_once_with(context, response_composer)

    async def test_save_persists_phase_memory_and_pedagogy(self) -> None:
        provider = DialogueStateProvider()
        context = SimpleNamespace(
            current_phase=DialoguePhase.CORRECT,
            state=SimpleNamespace(phase=DialoguePhase.AWAITING_ANSWER),
            redis_client=object(),
            body=SimpleNamespace(session_id="sess-3"),
            mid="user-3",
            memory=object(),
            pedagogy_state=object(),
            active_conversation_id=77,
            prepared_turn=SimpleNamespace(user_id="user-3"),
        )

        with patch("app.services.dialogue_state.save_state", AsyncMock()) as save_state, patch(
            "app.services.dialogue_state.save_memory", AsyncMock()
        ) as save_memory, patch(
            "app.services.dialogue_state.save_pedagogy", AsyncMock()
        ) as save_pedagogy:
            await provider.save(context)

        self.assertEqual(context.state.phase, DialoguePhase.CORRECT)
        save_state.assert_awaited_once_with(context.redis_client, "sess-3", context.state)
        save_memory.assert_awaited_once_with(context.redis_client, "user-3", context.memory)
        save_pedagogy.assert_awaited_once_with(context.redis_client, "sess-3", context.pedagogy_state)


if __name__ == "__main__":
    unittest.main()
