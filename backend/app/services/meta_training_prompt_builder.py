from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.meta_training import MetaTrainingPhase, MetaTrainingSessionState


@dataclass(frozen=True)
class MetaTrainingPromptBundle:
    system_prompt: str
    fallback_reply: str


class MetaTrainingPromptBuilder:
    def __init__(self, prompts_dir: Path | None = None) -> None:
        app_dir = Path(__file__).resolve().parents[1]
        self._prompts_dir = prompts_dir or (app_dir / "prompts" / "meta_training")

    def build(self, state: MetaTrainingSessionState) -> MetaTrainingPromptBundle:
        parts = [
            self._read("base.md"),
            self._phase_prompt(state.phase),
            self._session_context(state),
        ]
        if state.phase == MetaTrainingPhase.SPARRING:
            parts.append(self._read("few_shots.md"))
        return MetaTrainingPromptBundle(
            system_prompt="\n\n".join(part.strip() for part in parts if part.strip()),
            fallback_reply=self.fallback_reply(state),
        )

    def phase_intro(self, phase: MetaTrainingPhase) -> str:
        if phase == MetaTrainingPhase.ORIENTATION:
            return (
                "Фаза 1: собери карту вопросов. Не отвечай на тезис. "
                "Задай несколько вопросов и попробуй вскрыть скрытые допущения."
            )
        if phase == MetaTrainingPhase.EXPLORATION:
            return (
                "Фаза 2: выбери рамку. Можно зайти через термодинамику, теорию информации, философию или другую перспективу, "
                "но назови её явно и объясни выбор."
            )
        if phase == MetaTrainingPhase.SPARRING:
            return "Фаза 3: теперь я защищаю тезис. Атакуй мою позицию вопросами и ищи скрытые допущения."
        if phase == MetaTrainingPhase.REFLECTION:
            return "Фаза 4: вынеси вердикт. Что ты теперь думаешь о тезисе, насколько уверен и где видишь границы понимания?"
        return "Сессия завершена."

    def fallback_reply(self, state: MetaTrainingSessionState) -> str:
        if state.phase == MetaTrainingPhase.ORIENTATION:
            return "Сделай вопрос точнее: что именно в тезисе кажется тебе двусмысленным, и какое допущение там уже спрятано?"
        if state.phase == MetaTrainingPhase.EXPLORATION:
            return "Выбери рамку явно: через физику, теорию информации или философию, и добавь, почему она полезна именно здесь."
        if state.phase == MetaTrainingPhase.SPARRING:
            return "Я пока защищаю тезис. Попробуй ударить по предпосылке: что в моей позиции я принимаю как само собой разумеющееся?"
        if state.phase == MetaTrainingPhase.REFLECTION:
            return "Зафиксируй итог: что ты теперь считаешь вероятным, в чем не уверен и какую рамку еще стоило бы проверить?"
        return "Сессия уже завершена. Можно открыть новую мета-тренировку."

    def _phase_prompt(self, phase: MetaTrainingPhase) -> str:
        filename_map = {
            MetaTrainingPhase.ORIENTATION: "orientation.md",
            MetaTrainingPhase.EXPLORATION: "framing.md",
            MetaTrainingPhase.SPARRING: "sparring.md",
            MetaTrainingPhase.REFLECTION: "reflection.md",
        }
        filename = filename_map.get(phase)
        if not filename:
            return ""
        return self._read(filename)

    def _session_context(self, state: MetaTrainingSessionState) -> str:
        questions = "\n".join(
            f"- {question.text} [{question.question_type.value}]"
            + (f" | допущение: {question.assumption}" if question.assumption else "")
            for question in state.questions[-6:]
        ) or "- пока нет"
        frames = "\n".join(
            f"- {frame.name}: {frame.reason or 'без объяснения'}"
            for frame in state.frames[-4:]
        ) or "- пока нет"
        transcript = "\n".join(
            f"{'Ученик' if msg.role == 'user' else 'Socrates-AI'}: {msg.text}"
            for msg in state.transcript[-6:]
        ) or "- пока нет"
        current_frame = state.frames[-1].name if state.frames else "не выбрана"
        return (
            f"Тезис: {state.thesis}\n"
            f"Текущая фаза: {state.phase.value}\n"
            f"Выбранная рамка: {current_frame}\n"
            f"Последние вопросы ученика:\n{questions}\n"
            f"Последние переключения рамок:\n{frames}\n"
            f"Последние реплики:\n{transcript}"
        )

    def _read(self, filename: str) -> str:
        path = self._prompts_dir / filename
        try:
            return path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return ""
