from __future__ import annotations

import unittest

from app.services.state_machine import DialoguePhase, validate_transition


class TestStateMachine(unittest.TestCase):
    def test_allows_expected_transition(self) -> None:
        self.assertTrue(validate_transition(DialoguePhase.AWAITING_ANSWER, DialoguePhase.ANSWER_ANALYZED))
        self.assertTrue(validate_transition(DialoguePhase.ANSWER_ANALYZED, DialoguePhase.CORRECT))

    def test_blocks_invalid_transition_correct_to_hint(self) -> None:
        self.assertFalse(validate_transition(DialoguePhase.CORRECT, DialoguePhase.HINT_PROVIDED))

    def test_blocks_invalid_transition_give_up_to_correct(self) -> None:
        self.assertFalse(validate_transition(DialoguePhase.GIVE_UP, DialoguePhase.CORRECT))


if __name__ == "__main__":
    unittest.main()
