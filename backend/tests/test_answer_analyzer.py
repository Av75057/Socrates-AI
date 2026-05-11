from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services.answer_analyzer import AnswerAnalyzer


def _build_context(
    *,
    action: str = "none",
    msg_stripped: str = "answer",
    cheat: bool = False,
    idle_turn: bool = False,
    history: list[dict[str, str]] | None = None,
    common_fallacies: list[str] | None = None,
):
    return SimpleNamespace(
        cheat=cheat,
        idle_turn=idle_turn,
        body=SimpleNamespace(action=action),
        msg_stripped=msg_stripped,
        router=SimpleNamespace(),
        state=SimpleNamespace(phase="awaiting_answer", history=history or []),
        pedagogy_state=SimpleNamespace(common_fallacies=list(common_fallacies or [])),
    )


class TestAnswerAnalyzer(unittest.IsolatedAsyncioTestCase):
    async def test_skips_analysis_for_guard_conditions(self) -> None:
        cases = [
            _build_context(cheat=True),
            _build_context(idle_turn=True),
            _build_context(action="hint"),
            _build_context(msg_stripped=""),
        ]
        analyzer = AnswerAnalyzer()

        for context in cases:
            with self.subTest(context=context):
                mocked = AsyncMock()
                with patch("app.services.answer_analyzer.analyze_response", mocked):
                    result = await analyzer.analyze(context)
                self.assertIsNone(result)
                mocked.assert_not_awaited()

    async def test_passes_last_assistant_question_and_history_to_detector(self) -> None:
        history = [
            {"role": "user", "content": "Сначала я ответил"},
            {"role": "assistant", "content": "Первый вопрос?"},
            {"role": "assistant", "content": "Последний вопрос?  "},
            {"role": "user", "content": "И потом уточнил"},
        ]
        context = _build_context(history=history)
        analyzer = AnswerAnalyzer()
        expected = {"has_fallacy": False, "fallacy_type": "none", "depth_combined": 0.8}
        mocked = AsyncMock(return_value=expected)

        with patch("app.services.answer_analyzer.analyze_response", mocked), patch(
            "app.services.answer_analyzer._detected_skills",
            return_value=["structure_argument"],
        ):
            result = await analyzer.analyze(context)

        self.assertEqual(result["score"], 1.0)
        self.assertEqual(result["detected_skills"], ["structure_argument"])
        mocked.assert_awaited_once_with(
            context.router,
            "answer",
            "Последний вопрос?",
            "Ученик: Сначала я ответил\n"
            "Тьютор: Первый вопрос?\n"
            "Тьютор: Последний вопрос?\n"
            "Ученик: И потом уточнил",
        )

    async def test_appends_new_fallacy_and_trims_to_last_fifteen(self) -> None:
        context = _build_context(common_fallacies=[f"fallacy_{idx}" for idx in range(15)])
        analyzer = AnswerAnalyzer()
        mocked = AsyncMock(
            return_value={"has_fallacy": True, "fallacy_type": "ad_hominem", "depth_combined": 0.4}
        )

        with patch("app.services.answer_analyzer.analyze_response", mocked), patch(
            "app.services.answer_analyzer._detected_skills",
            return_value=[],
        ):
            await analyzer.analyze(context)

        self.assertEqual(len(context.pedagogy_state.common_fallacies), 15)
        self.assertEqual(context.pedagogy_state.common_fallacies[0], "fallacy_1")
        self.assertEqual(context.pedagogy_state.common_fallacies[-1], "ad_hominem")

    async def test_does_not_duplicate_existing_fallacy(self) -> None:
        context = _build_context(common_fallacies=["ad_hominem"])
        analyzer = AnswerAnalyzer()
        mocked = AsyncMock(
            return_value={"has_fallacy": True, "fallacy_type": "ad_hominem", "depth_combined": 0.4}
        )

        with patch("app.services.answer_analyzer.analyze_response", mocked), patch(
            "app.services.answer_analyzer._detected_skills",
            return_value=[],
        ):
            await analyzer.analyze(context)

        self.assertEqual(context.pedagogy_state.common_fallacies, ["ad_hominem"])

    async def test_score_uses_depth_and_fallacy_penalty(self) -> None:
        context = _build_context()
        analyzer = AnswerAnalyzer()
        mocked = AsyncMock(
            return_value={"has_fallacy": True, "fallacy_type": "straw_man", "depth_combined": 0.8}
        )

        with patch("app.services.answer_analyzer.analyze_response", mocked), patch(
            "app.services.answer_analyzer._detected_skills",
            return_value=["avoid_straw_man"],
        ):
            result = await analyzer.analyze(context)

        self.assertEqual(result["score"], 0.4)
        self.assertEqual(result["detected_skills"], ["avoid_straw_man"])


if __name__ == "__main__":
    unittest.main()
