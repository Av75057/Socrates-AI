from __future__ import annotations

import unittest

from app.models.meta_training import MetaEvaluation, MetaScores, MetaTrainingAction, MetaTrainingPhase
from app.services.meta_training_evaluator import MetaTrainingEvaluationResult
from app.services.meta_training_question_classifier import MetaTrainingQuestionClassifier
from app.services.meta_training_service import (
    MetaTrainingService,
    calc_reward,
    detect_assumption,
)


class _MemoryRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str) -> str:
        self.data[key] = value
        return "OK"


class _FakeEvaluator:
    def __init__(
        self,
        scores: MetaScores | None = None,
        comment: str | None = None,
        confidence: float | None = None,
        flags: list[str] | None = None,
    ) -> None:
        self.scores = scores or MetaScores()
        self.comment = comment
        self.confidence = confidence
        self.flags = flags or []

    async def evaluate(self, state, router):
        return MetaTrainingEvaluationResult(
            scores=self.scores,
            evaluation=MetaEvaluation(
                comment=self.comment,
                confidence=self.confidence,
                flags=self.flags,
            ),
        )


class _FakeQuestionClassifier:
    async def classify(self, text, thesis, router):
        if "что значит" in text.lower():
            return "conceptual", "Вопрос предполагает, что у формулировки есть единый смысл."
        return "factual", None


class TestMetaTrainingHeuristics(unittest.TestCase):
    def test_detect_assumption_finds_single_cause_pattern(self) -> None:
        assumption = detect_assumption("Почему наблюдатель вообще влияет на систему?")
        self.assertIsNotNone(assumption)

    def test_reward_scales_with_total_score(self) -> None:
        reward = calc_reward(
            MetaScores(
                inquisitiveness=8,
                frame_agility=6,
                uncertainty_tolerance=7,
                assumption_detection=5,
                meta_reflection=4,
            )
        )
        self.assertEqual(reward, 90)


class TestMetaTrainingService(unittest.IsolatedAsyncioTestCase):
    async def test_start_message_advance_end_flow(self) -> None:
        redis = _MemoryRedis()
        service = MetaTrainingService(
            evaluator=_FakeEvaluator(
                MetaScores(
                    inquisitiveness=6,
                    frame_agility=4,
                    uncertainty_tolerance=5,
                    assumption_detection=3,
                    meta_reflection=7,
                ),
                "Ученик честно описал пределы понимания.",
                0.84,
                ["high_performance"],
            ),
            question_classifier=_FakeQuestionClassifier(),
        )

        started = await service.start(redis, "meta-sess-1", None)
        self.assertEqual(started["session"]["phase"], MetaTrainingPhase.ORIENTATION.value)

        replied = await service.message(
            redis,
            "meta-sess-1",
            None,
            "Что значит «мера незнания» и какое допущение тут уже спрятано?",
            MetaTrainingAction.MESSAGE,
        )
        self.assertEqual(replied["session"]["questions"][0]["question_type"], "conceptual")

        advanced = await service.message(
            redis,
            "meta-sess-1",
            None,
            "",
            MetaTrainingAction.ADVANCE_PHASE,
        )
        self.assertEqual(advanced["session"]["phase"], MetaTrainingPhase.EXPLORATION.value)

        ended = await service.end(
            redis,
            "meta-sess-1",
            None,
            "Я пока скорее понимаю, где границы тезиса, чем сам тезис.",
            "Средняя",
        )
        self.assertEqual(ended["session"]["phase"], MetaTrainingPhase.COMPLETED.value)
        self.assertGreaterEqual(ended["session"]["awarded_wisdom_points"], 15)
        self.assertEqual(ended["session"]["evaluation"]["comment"], "Ученик честно описал пределы понимания.")
        self.assertEqual(ended["session"]["evaluation"]["confidence"], 0.84)
        self.assertEqual(ended["session"]["evaluation"]["flags"], ["high_performance"])
        self.assertIn("Ученик честно описал пределы понимания.", ended["reply"])
        self.assertIn("Уверенность оценки: 0.84.", ended["reply"])


if __name__ == "__main__":
    unittest.main()
