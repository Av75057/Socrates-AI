from __future__ import annotations

import unittest

from app.services.prompt_builder import build_prompt


class TestPromptBuilderRuntimeContract(unittest.TestCase):
    def test_build_prompt_supports_minimal_inputs(self) -> None:
        prompt = build_prompt(
            mode="question",
            topic=None,
            history=[],
            tutor_state={},
        )

        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 100)
        self.assertIn("Socrates AI", prompt)
        self.assertIn("Ты НЕ даешь готовые ответы сразу", prompt)
        self.assertIn("не указана", prompt)
        self.assertIn("Диалог: (пока пусто)", prompt)

    def test_build_prompt_supports_extended_tutor_state(self) -> None:
        prompt = build_prompt(
            mode="question",
            topic="линейные уравнения",
            history=[],
            tutor_state={
                "topic": "линейные уравнения",
                "last_fallacy": "ложная дилемма",
                "step": 3,
                "attempted_concepts": ["перенос слагаемых", "проверка"],
            },
        )

        self.assertIn("линейные уравнения", prompt)
        self.assertIn("ложная дилемма", prompt)
        self.assertIn("перенос слагаемых, проверка", prompt)

    def test_build_prompt_supports_modes_and_russian_topic(self) -> None:
        for mode in ("question", "hint", "explain"):
            with self.subTest(mode=mode):
                prompt = build_prompt(
                    mode=mode,
                    topic="квадратные уравнения",
                    history=[],
                    tutor_state={"topic": "квадратные уравнения"},
                )
                self.assertIsInstance(prompt, str)
                self.assertGreater(len(prompt), 100)
                self.assertIn("Socrates AI", prompt)
                self.assertIn("квадратные уравнения", prompt)
                self.assertIn("Всегда отвечай только по-русски", prompt)

    def test_build_prompt_supports_empty_history_and_empty_tutor_state(self) -> None:
        prompt = build_prompt(
            mode="hint",
            topic="дроби",
            history=[],
            tutor_state={},
        )

        self.assertIn("дроби", prompt)
        self.assertIn("Диалог: (пока пусто)", prompt)

    def test_build_prompt_supports_none_history(self) -> None:
        prompt = build_prompt(
            mode="explain",
            topic="геометрия",
            history=None,
            tutor_state={"step": None},
        )

        self.assertIsInstance(prompt, str)
        self.assertIn("геометрия", prompt)


if __name__ == "__main__":
    unittest.main()
