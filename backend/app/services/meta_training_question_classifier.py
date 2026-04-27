from __future__ import annotations

from pathlib import Path

from app.models.meta_training import QuestionType
from app.services.model_router import ModelRouter


class MetaTrainingQuestionClassifier:
    def __init__(self, prompt_path: Path | None = None) -> None:
        app_dir = Path(__file__).resolve().parents[1]
        self._prompt_path = prompt_path or (app_dir / "prompts" / "meta_training" / "question_classifier.md")

    async def classify(
        self,
        text: str,
        thesis: str,
        router: ModelRouter | None = None,
    ) -> tuple[QuestionType, str | None]:
        heuristic_type = self._heuristic_type(text)
        heuristic_assumption = self._heuristic_assumption(text)
        if router is None:
            return heuristic_type, heuristic_assumption
        try:
            parsed = await router.call_model_json(
                [
                    {"role": "system", "content": self._system_prompt()},
                    {
                        "role": "user",
                        "content": (
                            f"Тезис: {thesis}\n"
                            f"Вопрос ученика: {text.strip() or '(пусто)'}"
                        ),
                    },
                ],
                router.pedagogy_model(),
                temperature=0.0,
                max_tokens=120,
            )
            raw_type = str(parsed.get("question_type") or "").strip().lower()
            llm_type = self._safe_question_type(raw_type) or heuristic_type
            assumption = str(parsed.get("assumption_hint") or "").strip() or heuristic_assumption
            return llm_type, assumption
        except Exception:
            return heuristic_type, heuristic_assumption

    def _system_prompt(self) -> str:
        try:
            return self._prompt_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return (
                'Верни только JSON с полями "question_type" и "assumption_hint". '
                'question_type должен быть одним из factual, conceptual, provocative, meta.'
            )

    @staticmethod
    def _safe_question_type(value: str) -> QuestionType | None:
        try:
            return QuestionType(value)
        except ValueError:
            return None

    @staticmethod
    def _heuristic_type(text: str) -> QuestionType:
        lowered = (text or "").strip().lower()
        if any(x in lowered for x in ("что считать знанием", "как понять", "по каким критериям", "как мы узнаем")):
            return QuestionType.META
        if any(x in lowered for x in ("почему", "зачем", "что если", "а если", "поставить под сомнение")):
            return QuestionType.PROVOCATIVE
        if any(x in lowered for x in ("что значит", "в каком смысле", "чем отличается", "какая разница")):
            return QuestionType.CONCEPTUAL
        return QuestionType.FACTUAL

    @staticmethod
    def _heuristic_assumption(text: str) -> str | None:
        lowered = (text or "").strip().lower()
        if "это" in lowered and "?" in lowered:
            return "Вопрос предполагает, что у ключевого термина уже есть единое значение."
        if any(x in lowered for x in ("почему", "зачем")):
            return "Вопрос предполагает, что у явления есть одна главная причина."
        if any(x in lowered for x in ("доказ", "верно ли", "правда ли")):
            return "Вопрос предполагает, что тезис можно проверить в одной шкале истинности."
        return None
