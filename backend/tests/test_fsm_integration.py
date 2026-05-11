from __future__ import annotations

import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from app.services.chat_orchestrator import ChatOrchestrator
from app.services.state_machine import DialoguePhase


class _FakeComposer:
    def __init__(self, outcome: DialoguePhase) -> None:
        self.outcome = outcome

    def determine_outcome_phase(self, context) -> DialoguePhase:
        return self.outcome


def _build_context(
    phase: DialoguePhase,
    *,
    action: str = "none",
    msg_stripped: str = "answer",
    cheat: bool = False,
    idle_turn: bool = False,
):
    return SimpleNamespace(
        body=SimpleNamespace(action=action),
        current_phase=phase,
        state=SimpleNamespace(phase=phase),
        msg_stripped=msg_stripped,
        cheat=cheat,
        idle_turn=idle_turn,
        transition_history=[],
    )


class TestFSMIntegration(unittest.TestCase):
    def test_regular_answer_flows_from_greeting_to_outcome(self) -> None:
        context = _build_context(DialoguePhase.GREETING)
        orchestrator = ChatOrchestrator(response_composer=_FakeComposer(DialoguePhase.CORRECT))

        orchestrator.advance_state_for_turn(context)

        self.assertEqual(context.current_phase, DialoguePhase.CORRECT)
        self.assertEqual(
            context.transition_history,
            [
                DialoguePhase.AWAITING_ANSWER,
                DialoguePhase.ANSWER_ANALYZED,
                DialoguePhase.CORRECT,
            ],
        )

    def test_hint_from_terminal_runtime_phase_is_recovered_via_awaiting_answer(self) -> None:
        context = _build_context(DialoguePhase.CORRECT, action="hint", msg_stripped="need help")
        orchestrator = ChatOrchestrator(response_composer=_FakeComposer(DialoguePhase.CORRECT))

        orchestrator.advance_state_for_turn(context)

        self.assertEqual(context.current_phase, DialoguePhase.HINT_PROVIDED)
        self.assertEqual(
            context.transition_history,
            [DialoguePhase.AWAITING_ANSWER, DialoguePhase.HINT_PROVIDED],
        )

    def test_give_up_after_retry_uses_valid_fsm_path(self) -> None:
        context = _build_context(DialoguePhase.INCORRECT_RETRY, action="give_up", msg_stripped="done")
        orchestrator = ChatOrchestrator(response_composer=_FakeComposer(DialoguePhase.CORRECT))

        orchestrator.advance_state_for_turn(context)

        self.assertEqual(context.current_phase, DialoguePhase.GIVE_UP)
        self.assertEqual(
            context.transition_history,
            [DialoguePhase.AWAITING_ANSWER, DialoguePhase.GIVE_UP],
        )

    def test_closing_phase_still_rejects_hint_transition(self) -> None:
        context = _build_context(DialoguePhase.CLOSING, action="hint", msg_stripped="need help")
        orchestrator = ChatOrchestrator(response_composer=_FakeComposer(DialoguePhase.CORRECT))

        with self.assertRaises(HTTPException) as raised:
            orchestrator.advance_state_for_turn(context)

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(context.current_phase, DialoguePhase.CLOSING)
        self.assertEqual(context.transition_history, [])


if __name__ == "__main__":
    unittest.main()
