from __future__ import annotations

import unittest

from app.models.state import TutorState
from app.services.prompt_builder import _history_to_text
from app.services.response_validator import normalize_response_text
from app.services.tutor_controller import TutorController
from app.services.tutor_prompt import (
    build_tutor_system_prompt,
    is_invalid_tutor_reply,
    is_repeating_question,
    is_tutor_answering_for_student,
    postprocess_tutor_response,
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
        self.assertIn("Ты — Сократический тьютор по математике", prompt)
        self.assertIn("Ты отвечаешь только на русском языке", prompt)
        self.assertIn("Только пользователь может давать ответы", prompt)
        self.assertIn("Ты НИКОГДА не отвечаешь на свои вопросы", prompt)
        self.assertIn("Правильный ответ:", prompt)

    def test_answering_for_student_detector(self) -> None:
        self.assertTrue(is_tutor_answering_for_student("Правильный ответ: это добродетель"))
        self.assertTrue(is_tutor_answering_for_student("Например, ученик скажет, что это свобода"))
        self.assertTrue(
            is_tutor_answering_for_student(
                "Чтобы решить уравнение, выполним следующие шаги: сначала вычтем 5, потом получим x = 5."
            )
        )
        self.assertFalse(is_tutor_answering_for_student("Почему ты так считаешь?"))

    def test_invalid_tutor_reply_detector(self) -> None:
        self.assertTrue(
            is_invalid_tutor_reply("Translate this to English? The English translation is: Ask me questions.")
        )
        self.assertTrue(is_invalid_tutor_reply("You're welcome! Feel free to ask! 🙏"))
        self.assertTrue(is_invalid_tutor_reply("Продифференцируем обе части уравнения по x и найдём производную."))
        self.assertTrue(is_invalid_tutor_reply("0 голосов. Лучший ответ. В категории Математика. 98 просмотров."))
        self.assertFalse(is_invalid_tutor_reply("Хорошо. Какое действие удобно сделать первым?"))

    def test_repeating_question_detector(self) -> None:
        self.assertTrue(
            is_repeating_question(
                "Какое действие удобно сделать первым в уравнении 3x + 5 = 20?",
                "Какое действие удобно сделать первым в уравнении 3x + 5 = 20?",
            )
        )
        self.assertFalse(
            is_repeating_question(
                "Какой следующий шаг поможет оставить x без коэффициента?",
                "Какое действие удобно сделать первым в уравнении 3x + 5 = 20?",
            )
        )

    def test_postprocess_tutor_response_returns_four_item_contract(self) -> None:
        processed = postprocess_tutor_response(
            "Правильный ответ: сначала вычтем 5.",
            "Какое действие удобно сделать первым в уравнении 3x + 5 = 20?",
        )

        self.assertEqual(len(processed), 4)
        text, repeated, answered_for_student, invalid = processed
        self.assertEqual(text, "Правильный ответ: сначала вычтем 5.")
        self.assertFalse(repeated)
        self.assertTrue(answered_for_student)
        self.assertFalse(invalid)

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

    def test_normalize_response_text_removes_trailing_technical_artifacts(self) -> None:
        raw = "Хорошо. Что получится после переноса? _pairs_2"
        self.assertEqual(normalize_response_text(raw), "Хорошо. Что получится после переноса?")


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

        self.assertEqual(reply, "Хорошо. Начнём по теме «философия»: какой первый шаг ты бы предложил?")
        self.assertEqual(mode, "question")
        self.assertEqual(
            state.history[-1]["content"],
            "Хорошо. Начнём по теме «философия»: какой первый шаг ты бы предложил?",
        )

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

        self.assertEqual(chunks, ["Хорошо. Начнём по теме «логика»: какой первый шаг ты бы предложил?"])
        self.assertEqual(
            state.history[-1]["content"],
            "Хорошо. Начнём по теме «логика»: какой первый шаг ты бы предложил?",
        )

    async def test_start_question_request_returns_topic_question_immediately(self) -> None:
        controller = TutorController(_FakeRouter())
        state = TutorState(
            topic="уравнения",
            history=[{"role": "assistant", "content": "Какую тему из 8-го класса вы хотели бы обсудить сегодня?"}],
        )

        reply, mode = await controller.handle_turn(state, "Задавай вопросы")

        self.assertEqual(mode, "question")
        self.assertIn("какое действие удобно сделать первым", reply.lower())

    async def test_topic_choice_returns_equation_question_immediately(self) -> None:
        controller = TutorController(_FakeRouter())
        state = TutorState(
            topic="математика",
            history=[{"role": "assistant", "content": "Хорошо. А какую тему из 8-го класса вы хотели бы обсудить сегодня?"}],
        )

        reply, mode = await controller.handle_turn(state, "уравнения")

        self.assertEqual(mode, "question")
        self.assertIn("какое действие удобно сделать первым", reply.lower())

    async def test_equation_progress_answer_gets_next_local_question(self) -> None:
        controller = TutorController(_FakeRouter())
        state = TutorState(
            topic="уравнения",
            history=[{"role": "assistant", "content": "Хорошо. Начнём с простого: какое действие удобно сделать первым в уравнении 3x + 5 = 20?"}],
        )

        reply, mode = await controller.handle_turn(state, "3х=20-5")

        self.assertEqual(mode, "question")
        self.assertIn("как из записи 3х=20-5 получить значение x", reply.lower())

    async def test_solved_x_answer_requests_substitution_check(self) -> None:
        controller = TutorController(_FakeRouter())
        state = TutorState(
            topic="уравнения",
            history=[{"role": "assistant", "content": "Хорошо. Теперь как из записи 3х=20-5 получить значение x?"}],
        )

        reply, mode = await controller.handle_turn(state, "х=5")

        self.assertEqual(mode, "question")
        self.assertIn("подставь это значение", reply.lower())

    async def test_verification_answer_moves_to_conclusion_question(self) -> None:
        controller = TutorController(_FakeRouter())
        state = TutorState(
            topic="уравнения",
            history=[{"role": "assistant", "content": "Хорошо. Теперь подставь это значение в исходное уравнение 3x + 5 = 20. Что получится?"}],
        )

        reply, mode = await controller.handle_turn(state, "20=20")

        self.assertEqual(mode, "question")
        self.assertIn("подтверждает", reply.lower())

    async def test_typo_in_variable_gets_local_correction_question(self) -> None:
        controller = TutorController(_FakeRouter())
        state = TutorState(
            topic="уравнения",
            history=[{"role": "assistant", "content": "Хорошо. Теперь как из записи х= 15/3 получить значение x?"}],
        )

        reply, mode = await controller.handle_turn(state, "ч=5")

        self.assertEqual(mode, "question")
        self.assertIn("опечатка", reply.lower())


if __name__ == "__main__":
    unittest.main()
