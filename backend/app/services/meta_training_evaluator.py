from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.meta_training import MetaEvaluation, MetaScores, MetaTrainingSessionState
from app.services.model_router import ModelRouter


@dataclass(frozen=True)
class MetaTrainingEvaluationResult:
    scores: MetaScores
    evaluation: MetaEvaluation


class MetaTrainingEvaluator:
    def __init__(self, prompt_path: Path | None = None) -> None:
        app_dir = Path(__file__).resolve().parents[1]
        self._prompt_path = prompt_path or (app_dir / "prompts" / "meta_training" / "evaluator.md")

    async def evaluate(
        self,
        state: MetaTrainingSessionState,
        router: ModelRouter,
    ) -> MetaTrainingEvaluationResult:
        prompt = self._system_prompt()
        context = self._evaluation_context(state)
        try:
            parsed = await router.call_model_json(
                [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": context},
                ],
                router.pedagogy_model(),
                temperature=0.1,
                max_tokens=260,
            )
            scores = MetaScores(
                inquisitiveness=parsed.get("inquisitiveness", 0),
                frame_agility=parsed.get("frame_agility", 0),
                uncertainty_tolerance=parsed.get("uncertainty_tolerance", 0),
                assumption_detection=parsed.get("assumption_detection", 0),
                meta_reflection=parsed.get("meta_reflection", 0),
            ).capped()
            comment = str(parsed.get("comment") or parsed.get("summary") or "").strip() or None
            confidence = self._normalized_confidence(parsed.get("confidence"))
            flags = self._normalized_flags(parsed.get("flags"))
            user_turns = sum(1 for message in state.transcript if message.role == "user")
            if user_turns < 4 and "short_dialog" not in flags:
                flags.append("short_dialog")
            if user_turns < 4:
                confidence = min(confidence, 0.55)
            return MetaTrainingEvaluationResult(
                scores=scores,
                evaluation=MetaEvaluation(
                    comment=comment,
                    confidence=confidence,
                    flags=flags,
                ),
            )
        except Exception:
            user_turns = sum(1 for message in state.transcript if message.role == "user")
            flags = ["short_dialog"] if user_turns < 4 else []
            confidence = 0.55 if user_turns < 4 else 0.7
            return MetaTrainingEvaluationResult(
                scores=MetaScores(),
                evaluation=MetaEvaluation(
                    comment=None,
                    confidence=confidence,
                    flags=flags,
                ),
            )

    def _system_prompt(self) -> str:
        try:
            return self._prompt_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return (
                "Оцени качество мышления ученика по 5 шкалам и верни только JSON с полями "
                "inquisitiveness, frame_agility, uncertainty_tolerance, assumption_detection, "
                "meta_reflection, comment, confidence, flags."
            )

    @staticmethod
    def _evaluation_context(state: MetaTrainingSessionState) -> str:
        questions = "\n".join(
            f"- {question.text} [{question.question_type.value}]"
            + (f" | допущение: {question.assumption}" if question.assumption else "")
            for question in state.questions
        ) or "- нет"
        frames = "\n".join(
            f"- {frame.name}: {frame.reason or 'без причины'}"
            for frame in state.frames
        ) or "- нет"
        transcript = "\n".join(
            f"{'Ученик' if message.role == 'user' else 'Socrates-AI'} ({message.phase.value}): {message.text}"
            for message in state.transcript[-32:]
        ) or "- нет"
        current_frame = state.frames[-1].name if state.frames else "не выбрана"
        return (
            f"Тезис: {state.thesis}\n"
            f"Выбранная рамка: {current_frame}\n"
            f"Итоговая рефлексия ученика: {state.reflection_summary or 'нет'}\n"
            f"Уровень уверенности: {state.confidence_label or 'не указан'}\n"
            f"Вопросы ученика:\n{questions}\n"
            f"Выбранные рамки:\n{frames}\n"
            f"Фрагмент истории:\n{transcript}"
        )

    @staticmethod
    def _normalized_confidence(value: object) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.8
        return max(0.0, min(1.0, numeric))

    @staticmethod
    def _normalized_flags(value: object) -> list[str]:
        allowed = {
            "short_dialog",
            "low_engagement",
            "high_performance",
            "possible_gaming",
            "short_reflection",
        }
        if not isinstance(value, list):
            return []
        flags: list[str] = []
        for raw in value:
            item = str(raw).strip().lower()
            if item and item in allowed and item not in flags:
                flags.append(item)
        return flags
