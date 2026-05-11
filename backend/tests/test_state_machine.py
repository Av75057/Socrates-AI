from __future__ import annotations

import unittest

from app.services.state_machine import ALLOWED_TRANSITIONS, DialoguePhase, validate_transition


class TestStateMachine(unittest.TestCase):
    def test_allows_expected_transition(self) -> None:
        self.assertTrue(validate_transition(DialoguePhase.AWAITING_ANSWER, DialoguePhase.ANSWER_ANALYZED))
        self.assertTrue(validate_transition(DialoguePhase.ANSWER_ANALYZED, DialoguePhase.CORRECT))

    def test_blocks_invalid_transition_correct_to_hint(self) -> None:
        self.assertFalse(validate_transition(DialoguePhase.CORRECT, DialoguePhase.HINT_PROVIDED))

    def test_blocks_invalid_transition_give_up_to_correct(self) -> None:
        self.assertFalse(validate_transition(DialoguePhase.GIVE_UP, DialoguePhase.CORRECT))

    def test_all_declared_transitions_are_allowed(self) -> None:
        for current, allowed in ALLOWED_TRANSITIONS.items():
            for new in allowed:
                with self.subTest(current=current, new=new):
                    self.assertTrue(validate_transition(current, new))

    def test_every_undeclared_transition_is_blocked(self) -> None:
        all_phases = list(DialoguePhase)
        for current in all_phases:
            for new in all_phases:
                if new in ALLOWED_TRANSITIONS[current]:
                    continue
                with self.subTest(current=current, new=new):
                    self.assertFalse(validate_transition(current, new))


if __name__ == "__main__":
    unittest.main()
