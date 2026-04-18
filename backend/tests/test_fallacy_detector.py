"""Мок-уровневые проверки эвристик (без сети)."""

from __future__ import annotations

import unittest

from app.services.pedagogy_heuristics import build_fallacy_instruction, heuristic_depth


class TestHeuristicDepth(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(heuristic_depth(""), 0.0)

    def test_short_low(self) -> None:
        self.assertLess(heuristic_depth("ок"), 0.25)

    def test_substantial_with_links(self) -> None:
        t = (
            "во-первых, я думаю так потому что есть пример из жизни; "
            "следовательно вывод логичен, как ты сказал ранее."
        )
        d = heuristic_depth(t)
        self.assertGreaterEqual(d, 0.65)


class TestFallacyInstruction(unittest.TestCase):
    def test_no_fallacy(self) -> None:
        self.assertEqual(build_fallacy_instruction("friendly", {"has_fallacy": False}), "")

    def test_friendly_non_empty(self) -> None:
        s = build_fallacy_instruction(
            "friendly",
            {
                "has_fallacy": True,
                "fallacy_type": "straw_man",
                "fallacy_description": "описание",
                "suggestion": "совет",
            },
        )
        self.assertIn("straw_man", s)
        self.assertIn("совет", s)


if __name__ == "__main__":
    unittest.main()
