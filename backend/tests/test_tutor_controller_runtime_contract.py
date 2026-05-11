from __future__ import annotations

import unittest

from app.models.state import TutorState
from app.services.tutor_controller import TutorController


class _FakeRouter:
    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls: list[tuple[str, str, str]] = []

    async def generate(self, prompt: str, user_line: str, mode: str) -> str:
        self.calls.append((prompt, user_line, mode))
        if not self.replies:
            raise AssertionError("No fake reply configured")
        return self.replies.pop(0)


class TestTutorControllerRuntimeContract(unittest.IsolatedAsyncioTestCase):
    async def test_handle_turn_returns_non_empty_reply_with_minimal_state(self) -> None:
        controller = TutorController(_FakeRouter(["Хорошая попытка. Какое действие удобно сделать первым?"]))
        state = TutorState()

        reply, mode = await controller.handle_turn(state, "хочу изучить уравнения")

        self.assertEqual(mode, "question")
        self.assertIsInstance(reply, str)
        self.assertTrue(reply.strip())

    async def test_handle_turn_uses_safe_fallback_for_invalid_model_reply(self) -> None:
        controller = TutorController(
            _FakeRouter(
                [
                    "Translate this to English. The English translation is: solve it.",
                    "Правильный ответ: x = 5.",
                ]
            )
        )
        state = TutorState(
            topic="уравнения",
            history=[{"role": "assistant", "content": "Какое действие удобно сделать первым в уравнении 3x + 5 = 20?"}],
        )

        reply, mode = await controller.handle_turn(state, "хочу изучить уравнения")

        self.assertEqual(mode, "question")
        self.assertIn("какое действие удобно сделать первым", reply.lower())
        self.assertEqual(len(controller._router.calls), 2)


if __name__ == "__main__":
    unittest.main()
