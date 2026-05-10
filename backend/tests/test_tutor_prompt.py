from __future__ import annotations

import unittest

from app.services.tutor_prompt import build_socratic_system_prompt


class TestSocraticTutorPrompt(unittest.TestCase):
    def test_prompt_contains_required_format_sections(self) -> None:
        scenarios = [
            {"level": 1, "mode": "friendly", "topic": "линейные уравнения"},
            {"level": 2, "mode": "friendly", "topic": "системы уравнений"},
            {"level": 3, "mode": "strict", "topic": "геометрия"},
            {"level": 4, "mode": "provocateur", "topic": "дроби"},
            {"level": 5, "mode": "strict", "topic": "квадратные уравнения"},
            {"level": 2, "mode": "friendly", "topic": "графики функций"},
            {"level": 3, "mode": "friendly", "topic": "проценты"},
            {"level": 4, "mode": "provocateur", "topic": "логические ошибки"},
            {"level": 1, "mode": "friendly", "topic": "арифметика"},
            {"level": 5, "mode": "strict", "topic": "доказательства"},
        ]

        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                prompt = build_socratic_system_prompt(
                    level=scenario["level"],
                    mode=scenario["mode"],
                    topic=scenario["topic"],
                    last_fallacy="ad hominem",
                    step_count=3,
                    attempted_concepts=["пример", "контраргумент"],
                )
                self.assertIn("[Анализ]", prompt)
                self.assertIn("[Вопрос]", prompt)
                self.assertIn("[Подсказка]", prompt)
                self.assertIn("максимум 1 вопрос за раз", prompt)
                self.assertIn(scenario["topic"], prompt)
                self.assertIn("ad hominem", prompt)
                self.assertIn("пример, контраргумент", prompt)

    def test_prompt_contains_forbidden_phrases_section(self) -> None:
        prompt = build_socratic_system_prompt()
        self.assertIn("Правильный ответ — 42", prompt)
        self.assertIn("Давай я объясню тему", prompt)
        self.assertIn("Подведём итог", prompt)


if __name__ == "__main__":
    unittest.main()
