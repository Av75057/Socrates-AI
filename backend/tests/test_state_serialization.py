from __future__ import annotations

import unittest

from app.models.state import TutorState
from app.services.state_machine import DialoguePhase


class TestTutorStateSerialization(unittest.TestCase):
    def test_phase_roundtrip(self) -> None:
        state = TutorState(attempts=2, frustration=1, phase=DialoguePhase.HINT_PROVIDED)
        restored = TutorState.from_dict(state.to_dict())
        self.assertEqual(restored.phase, DialoguePhase.HINT_PROVIDED)

    def test_topic_id_roundtrip(self) -> None:
        state = TutorState(topic="геометрия", topic_id=42)
        restored = TutorState.from_dict(state.to_dict())
        self.assertEqual(restored.topic_id, 42)
        self.assertEqual(restored.topic, "геометрия")

    def test_invalid_phase_falls_back_to_greeting(self) -> None:
        restored = TutorState.from_dict({"phase": "broken"})
        self.assertEqual(restored.phase, DialoguePhase.GREETING)


if __name__ == "__main__":
    unittest.main()
