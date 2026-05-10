from __future__ import annotations

import unittest

from app.services.learning_service import normalize_learning_objectives


class TestLearningObjectives(unittest.TestCase):
    def test_normalize_learning_objectives_filters_invalid_rows(self) -> None:
        rows = normalize_learning_objectives(
            [
                {"title": "Строит аргумент", "skill_id": "structure_argument", "target_level": 70},
                {"title": "", "skill_id": "ask_clarifying"},
                {"title": "Уточняет допущения", "skill_id": "", "target_level": 50},
                {"title": "Ищет контрпример", "skill_id": "use_counterexample", "target_level": 999},
            ]
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["skill_id"], "structure_argument")
        self.assertEqual(rows[0]["target_level"], 70)
        self.assertEqual(rows[1]["skill_id"], "use_counterexample")
        self.assertEqual(rows[1]["target_level"], 100)


if __name__ == "__main__":
    unittest.main()
