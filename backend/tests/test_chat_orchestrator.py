from __future__ import annotations

import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from app.dto.chat_schema import ChatResponse, FallacyOut, MemoryOut, PedagogyOut
from app.services.chat_orchestrator import ChatOrchestrator
from app.services.state_machine import DialoguePhase


class _FakeProvider:
    def __init__(self, context) -> None:
        self.context = context
        self.calls: list[str] = []

    async def load_or_create(self, body, redis_client, db_user, correlation_id, response_composer):
        self.calls.append("load_or_create")
        return self.context

    async def save(self, context) -> None:
        self.calls.append("save")


class _FakeAnalyzer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def analyze(self, context):
        self.calls.append("analyze")
        return {"depth_combined": 0.9, "has_fallacy": False}


class _FakeBuilder:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def build_prompt(self, context, controller):
        self.calls.append("build_prompt")
        return SimpleNamespace(prompt="prompt", user_line="user", mode="question", immediate_reply=None)


class _FakeComposer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def determine_outcome_phase(self, context):
        return DialoguePhase.CORRECT

    async def compose(self, context, controller, plan, raw_reply, *, source: str):
        self.calls.append("compose")
        context.original_reply = raw_reply
        context.current_phase = DialoguePhase.CORRECT
        return ChatResponse(
            reply=raw_reply,
            mode=plan.mode,
            attempts=1,
            frustration=0,
            frustration_level=0,
            user_type="lazy",
            topic="math",
            memory=MemoryOut(),
            skill_tree={},
            pedagogy=PedagogyOut(fallacy=FallacyOut()),
        )


class _FakeController:
    used_llm = False
    last_prompt = None
    last_user_line = None
    last_mode = None


class TestChatOrchestrator(unittest.IsolatedAsyncioTestCase):
    async def test_process_message_uses_services_in_order(self) -> None:
        context = SimpleNamespace(
            duplicate_response=None,
            prepared_turn=SimpleNamespace(user_id="u-1"),
            body=SimpleNamespace(action="none", session_id="sess-1"),
            active_conversation_id=11,
            router=SimpleNamespace(),
            state=SimpleNamespace(phase=DialoguePhase.AWAITING_ANSWER, mode="question"),
            current_phase=DialoguePhase.AWAITING_ANSWER,
            msg_stripped="answer",
            cheat=False,
            idle_turn=False,
            analysis=None,
            latency_ms=0,
        )
        provider = _FakeProvider(context)
        analyzer = _FakeAnalyzer()
        builder = _FakeBuilder()
        composer = _FakeComposer()
        orchestrator = ChatOrchestrator(
            state_provider=provider,
            answer_analyzer=analyzer,
            instruction_builder=builder,
            response_composer=composer,
            llm_call=lambda context, plan: _async_value("model reply"),
            controller_factory=lambda router: _FakeController(),
        )

        result = await orchestrator.process_message(context.body, object(), None, "corr-1")

        self.assertEqual(provider.calls, ["load_or_create", "save"])
        self.assertEqual(analyzer.calls, ["analyze"])
        self.assertEqual(builder.calls, ["build_prompt"])
        self.assertEqual(composer.calls, ["compose"])
        self.assertEqual(result.response.reply, "model reply")

    async def test_hint_from_persisted_correct_phase_recovers_to_awaiting_answer(self) -> None:
        context = SimpleNamespace(
            duplicate_response=None,
            prepared_turn=SimpleNamespace(user_id="u-1"),
            body=SimpleNamespace(action="hint", session_id="sess-1"),
            active_conversation_id=11,
            router=SimpleNamespace(),
            state=SimpleNamespace(phase=DialoguePhase.CORRECT, mode="question"),
            current_phase=DialoguePhase.CORRECT,
            msg_stripped="need help",
            cheat=False,
            idle_turn=False,
            analysis=None,
        )
        orchestrator = ChatOrchestrator()
        orchestrator.advance_state_for_turn(context)
        self.assertEqual(context.current_phase, DialoguePhase.HINT_PROVIDED)

    async def test_closing_transition_still_raises_http_500(self) -> None:
        context = SimpleNamespace(
            duplicate_response=None,
            prepared_turn=SimpleNamespace(user_id="u-1"),
            body=SimpleNamespace(action="hint", session_id="sess-1"),
            active_conversation_id=11,
            router=SimpleNamespace(),
            state=SimpleNamespace(phase=DialoguePhase.CLOSING, mode="question"),
            current_phase=DialoguePhase.CLOSING,
            msg_stripped="need help",
            cheat=False,
            idle_turn=False,
            analysis=None,
        )
        orchestrator = ChatOrchestrator()
        with self.assertRaises(HTTPException) as raised:
            orchestrator.advance_state_for_turn(context)
        self.assertEqual(raised.exception.status_code, 500)

    async def test_terminal_phase_is_normalized_before_persistence(self) -> None:
        context = SimpleNamespace(
            current_phase=DialoguePhase.CORRECT,
            transition_history=[],
        )
        orchestrator = ChatOrchestrator()
        orchestrator.normalize_phase_for_persistence(context)
        self.assertEqual(context.current_phase, DialoguePhase.AWAITING_ANSWER)


async def _async_value(value):
    return value


if __name__ == "__main__":
    unittest.main()
