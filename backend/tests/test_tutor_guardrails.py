from __future__ import annotations

import unittest

from app.models.state import TutorState
from app.services.prompt_builder import _history_to_text
from app.services.tutor_controller import TutorController
from app.services.tutor_prompt import (
    build_tutor_system_prompt,
    is_tutor_answering_for_student,
)


class _FakeRouter:
    def __init__(self, replies: list[str] | None = None, stream_chunks: list[str] | None = None) -> None:
        self._replies = list(replies or [])
        self._stream_chunks = list(stream_chunks or [])

    async def generate(self, prompt: str, user_line: str, mode: str) -> str:
        if not self._replies:
            raise AssertionError("No fake reply configured")
        return self._replies.pop(0)

    async def generate_stream(self, prompt: str, user_line: str, mode: str):
        for chunk in self._stream_chunks:
            yield chunk


class TestTutorPromptGuardrails(unittest.TestCase):
    def test_system_prompt_explicitly_forbids_answering_for_student(self) -> None:
        prompt = build_tutor_system_prompt("friendly", 3)
        self.assertIn("Только пользователь может давать ответы", prompt)
        self.assertIn("Ты НИКОГДА не отвечаешь на свои вопросы", prompt)
        self.assertIn("Правильный ответ:", prompt)

    def test_answering_for_student_detector(self) -> None:
        self.assertTrue(is_tutor_answering_for_student("Правильный ответ: это добродетель"))
        self.assertTrue(is_tutor_answering_for_student("Например, ученик скажет, что это свобода"))
        self.assertFalse(is_tutor_answering_for_student("Почему ты так считаешь?"))

    def test_history_to_text_keeps_last_five_exchanges(self) -> None:
        history = []
        for idx in range(6):
            history.append({"role": "user", "content": f"u{idx}"})
            history.append({"role": "assistant", "content": f"a{idx}"})
        text = _history_to_text(history, max_messages=10)
        self.assertNotIn("u0", text)
        self.assertNotIn("a0", text)
        self.assertIn("u1", text)
        self.assertIn("a5", text)


class TestTutorControllerGuardrails(unittest.IsolatedAsyncioTestCase):
    async def test_handle_turn_retries_and_uses_safe_reply_if_model_answers_for_student(self) -> None:
        controller = TutorController(
            _FakeRouter(
                replies=[
                    "Правильный ответ: справедливость — это равенство.",
                    "Ученик мог бы ответить, что это честность.",
                ]
            )
        )
        state = TutorState(
            topic="философия",
            history=[{"role": "assistant", "content": "Что такое справедливость?"}],
        )

        reply, mode = await controller.handle_turn(state, "Это когда все честно")

        self.assertEqual(reply, "Хорошо. А как бы ты ответил сам?")
        self.assertEqual(mode, "question")
        self.assertEqual(state.history[-1]["content"], "Хорошо. А как бы ты ответил сам?")

    async def test_stream_turn_emits_only_final_safe_reply(self) -> None:
        controller = TutorController(
            _FakeRouter(
                stream_chunks=[
                    "Правильный ответ: ",
                    "сначала нужно дать определение, ",
                    "а потом перейти дальше.",
                ]
            )
        )
        state = TutorState(
            topic="логика",
            history=[{"role": "assistant", "content": "Что такое аргумент?"}],
        )

        chunks = [chunk async for chunk in controller.stream_turn(state, "Это довод")]

        self.assertEqual(chunks, ["Хорошо. А как бы ты ответил сам?"])
        self.assertEqual(state.history[-1]["content"], "Хорошо. А как бы ты ответил сам?")


if __name__ == "__main__":
    unittest.main()
