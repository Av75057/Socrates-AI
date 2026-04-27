from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.db.models import MetaTrainingSession, User
from app.db.session import SessionLocal
from app.models.meta_training import (
    MetaFrameChoice,
    MetaMessage,
    MetaQuestion,
    MetaScores,
    MetaTrainingAction,
    MetaTrainingPhase,
    MetaTrainingSessionState,
    QuestionType,
    phase_role_label,
    session_public_payload,
)
from app.services.db_gamification import apply_redis_state_to_db
from app.services.gamification_store import load_progress, save_progress
from app.services.meta_training_evaluator import MetaTrainingEvaluator
from app.services.model_router import ModelRouter
from app.services.meta_training_prompt_builder import MetaTrainingPromptBuilder
from app.services.meta_training_question_classifier import MetaTrainingQuestionClassifier
from app.services.user_settings_db import build_model_router_for_user

_THESIS_LIBRARY: list[dict[str, str]] = [
    {
        "slug": "entropy",
        "thesis": "Энтропия — это мера нашего незнания, а не свойство системы. Разберись, что это значит.",
    },
    {
        "slug": "observer",
        "thesis": "В квантовой механике наблюдатель влияет на реальность. Поставь этот тезис под сомнение, даже если не знаешь физику.",
    },
    {
        "slug": "map-territory",
        "thesis": "Любая карта мира неизбежно искажает сам мир. Проверь, где здесь знание, а где удобная иллюзия.",
    },
    {
        "slug": "algorithmic-fairness",
        "thesis": "Справедливый алгоритм невозможен без политического выбора. Разбери этот тезис как исследователь, а не как моралист.",
    },
    {
        "slug": "evolution-language",
        "thesis": "Язык не описывает реальность, а дрессирует внимание. Попробуй атаковать этот тезис вопросами.",
    },
]

_PHASE_ORDER = [
    MetaTrainingPhase.ORIENTATION,
    MetaTrainingPhase.EXPLORATION,
    MetaTrainingPhase.SPARRING,
    MetaTrainingPhase.REFLECTION,
    MetaTrainingPhase.COMPLETED,
]

def detect_assumption(text: str) -> str | None:
    lowered = (text or "").strip().lower()
    if "это" in lowered and "?" in lowered:
        return "Вопрос предполагает, что у ключевого термина уже есть единое значение."
    if any(x in lowered for x in ("почему", "зачем")):
        return "Вопрос предполагает, что у явления есть одна главная причина."
    if any(x in lowered for x in ("доказ", "верно ли", "правда ли")):
        return "Вопрос предполагает, что тезис можно проверить в одной шкале истинности."
    return None


def detect_frame(message: str, explicit_frame: str | None = None) -> str | None:
    if explicit_frame:
        return explicit_frame.strip() or None
    lowered = (message or "").strip().lower()
    for candidate in ("термодинамика", "теория информации", "философия", "эпистемология", "этика", "математика"):
        if candidate in lowered:
            return candidate
    if "рамк" in lowered:
        return "новая рамка"
    return None


def score_reflection(summary: str, confidence_label: str | None) -> MetaScores:
    summary_low = (summary or "").lower()
    scores = MetaScores()
    if any(x in summary_low for x in ("не знаю", "не уверен", "границ", "предел", "непонят")):
        scores.meta_reflection += 4
        scores.uncertainty_tolerance += 3
    if any(x in summary_low for x in ("скорее", "вероятно", "пока думаю", "мне кажется")):
        scores.uncertainty_tolerance += 2
    if any(x in summary_low for x in ("допущ", "предпосыл", "рамк")):
        scores.assumption_detection += 2
        scores.frame_agility += 1
    if (confidence_label or "").strip():
        scores.meta_reflection += 2
    return scores


def calc_reward(scores: MetaScores) -> int:
    capped = scores.capped()
    return max(15, capped.total * 3)


class MetaTrainingService:
    def __init__(
        self,
        prompt_builder: MetaTrainingPromptBuilder | None = None,
        evaluator: MetaTrainingEvaluator | None = None,
        question_classifier: MetaTrainingQuestionClassifier | None = None,
    ) -> None:
        self.prompt_builder = prompt_builder or MetaTrainingPromptBuilder()
        self.evaluator = evaluator or MetaTrainingEvaluator()
        self.question_classifier = question_classifier or MetaTrainingQuestionClassifier()

    async def start(self, redis_client: Any, session_id: str, db_user: User | None, preferred_topic: str | None = None) -> dict[str, Any]:
        thesis_item = self._pick_thesis(session_id, preferred_topic)
        now = datetime.now(timezone.utc)
        state = MetaTrainingSessionState(
            session_id=session_id,
            user_id=str(db_user.id) if db_user else None,
            thesis=thesis_item["thesis"],
            topic_slug=thesis_item["slug"],
            phase=MetaTrainingPhase.ORIENTATION,
            created_at=now,
            phase_started_at=now,
            updated_at=now,
            current_role_label=phase_role_label(MetaTrainingPhase.ORIENTATION),
        )
        intro = self.prompt_builder.phase_intro(MetaTrainingPhase.ORIENTATION)
        state.transcript.append(self._assistant_message(intro, state.phase))
        await self._save(redis_client, state)
        return {
            "session": session_public_payload(state),
            "reply": intro,
            "messages": self._messages_payload(state),
            "detected_question_type": None,
        }

    async def status(self, redis_client: Any, session_id: str) -> dict[str, Any]:
        state = await self._load(redis_client, session_id)
        return {
            "session": session_public_payload(state),
            "reply": None,
            "messages": self._messages_payload(state),
            "detected_question_type": None,
        }

    async def message(
        self,
        redis_client: Any,
        session_id: str,
        db_user: User | None,
        message: str,
        action: MetaTrainingAction,
        frame_name: str | None = None,
    ) -> dict[str, Any]:
        state = await self._load(redis_client, session_id)
        detected_question_type: QuestionType | None = None
        if state.phase == MetaTrainingPhase.COMPLETED and action != MetaTrainingAction.MESSAGE:
            raise HTTPException(status_code=400, detail="Meta-training session is already completed")
        if action == MetaTrainingAction.ADVANCE_PHASE:
            reply = self._advance_phase(state)
        else:
            if message.strip() or action == MetaTrainingAction.SWITCH_FRAME:
                state.transcript.append(self._user_message(message or frame_name or "", state.phase))
            if action == MetaTrainingAction.SWITCH_FRAME:
                reply = self._apply_frame_switch(state, message, frame_name)
            else:
                reply, detected_question_type = await self._phase_reply(state, message, db_user)
        state.updated_at = datetime.now(timezone.utc)
        if reply:
            state.transcript.append(self._assistant_message(reply, state.phase))
        await self._save(redis_client, state)
        return {
            "session": session_public_payload(state),
            "reply": reply,
            "messages": self._messages_payload(state),
            "detected_question_type": detected_question_type,
        }

    async def end(
        self,
        redis_client: Any,
        session_id: str,
        db_user: User | None,
        summary: str | None,
        confidence_label: str | None,
    ) -> dict[str, Any]:
        state = await self._load(redis_client, session_id)
        if summary and summary.strip():
            state.reflection_summary = summary.strip()
            state.transcript.append(self._user_message(summary.strip(), state.phase))
            state.scores = self._merge_scores(state.scores, score_reflection(summary, confidence_label))
        if confidence_label:
            state.confidence_label = confidence_label.strip()
        router = await self._build_router(db_user)
        evaluation = await self.evaluator.evaluate(state, router)
        state.scores = self._finalize_scores(state.scores, evaluation.scores)
        state.evaluation = evaluation.evaluation
        state.phase = MetaTrainingPhase.COMPLETED
        state.current_role_label = phase_role_label(MetaTrainingPhase.COMPLETED)
        state.completed_at = datetime.now(timezone.utc)
        if not state.reward_applied:
            state.awarded_wisdom_points = calc_reward(state.scores)
            await self._award_wisdom(redis_client, session_id, db_user, state.awarded_wisdom_points)
            state.reward_applied = True
        reply = self._build_final_reflection(state)
        state.transcript.append(self._assistant_message(reply, state.phase))
        await self._save(redis_client, state)
        if db_user:
            await self._persist_result(db_user.id, state)
        return {
            "session": session_public_payload(state),
            "reply": reply,
            "messages": self._messages_payload(state),
            "detected_question_type": None,
        }

    async def _phase_reply(
        self,
        state: MetaTrainingSessionState,
        message: str,
        db_user: User | None,
    ) -> tuple[str, QuestionType | None]:
        text = (message or "").strip()
        router = await self._build_router(db_user)
        if state.phase == MetaTrainingPhase.ORIENTATION:
            question_type: QuestionType | None = None
            if text:
                question_type, assumption = await self.question_classifier.classify(text, state.thesis, router)
                q = MetaQuestion(
                    id=str(uuid4()),
                    text=text,
                    question_type=question_type,
                    assumption=assumption,
                )
                state.questions.append(q)
                state.scores.inquisitiveness += 2
                if q.question_type in {QuestionType.CONCEPTUAL, QuestionType.META, QuestionType.PROVOCATIVE}:
                    state.scores.inquisitiveness += 1
                if q.assumption:
                    state.scores.assumption_detection += 2
            return await self._llm_reply(state, text, router), question_type
        if state.phase == MetaTrainingPhase.EXPLORATION:
            frame = detect_frame(text)
            if frame:
                state.frames.append(MetaFrameChoice(name=frame, reason=text))
                state.scores.frame_agility += 2
            if any(x in text.lower() for x in ("не знаю", "пока не понимаю", "не уверен", "вероятно")):
                state.scores.uncertainty_tolerance += 2
            return await self._llm_reply(state, text, router), None
        if state.phase == MetaTrainingPhase.SPARRING:
            if any(x in text.lower() for x in ("допущ", "предпосыл", "противореч", "альтернатив")):
                state.scores.assumption_detection += 2
                state.scores.inquisitiveness += 1
            return await self._llm_reply(state, text, router), None
        if state.phase == MetaTrainingPhase.REFLECTION:
            if text:
                state.reflection_summary = text
                state.scores = self._merge_scores(state.scores, score_reflection(text, state.confidence_label))
            return await self._llm_reply(state, text, router), None
        return "Сессия уже завершена. Можно открыть новую мета-тренировку.", None

    def _apply_frame_switch(self, state: MetaTrainingSessionState, message: str, frame_name: str | None) -> str:
        frame = detect_frame(message, frame_name)
        if not frame:
            return "Назови рамку явно: например, «философия», «теория информации» или «термодинамика»."
        state.frames.append(MetaFrameChoice(name=frame, reason=(message or "").strip()))
        state.scores.frame_agility += 3
        state.scores.uncertainty_tolerance += 1
        return f"Рамка переключена на «{frame}». Теперь зафиксируй, почему эта перспектива поможет разобраться в тезисе."

    def _advance_phase(self, state: MetaTrainingSessionState) -> str:
        idx = _PHASE_ORDER.index(state.phase)
        next_phase = _PHASE_ORDER[min(idx + 1, len(_PHASE_ORDER) - 1)]
        state.phase = next_phase
        state.phase_started_at = datetime.now(timezone.utc)
        state.current_role_label = phase_role_label(next_phase)
        if next_phase in {
            MetaTrainingPhase.EXPLORATION,
            MetaTrainingPhase.SPARRING,
            MetaTrainingPhase.REFLECTION,
        }:
            return self.prompt_builder.phase_intro(next_phase)
        if next_phase == MetaTrainingPhase.COMPLETED:
            state.completed_at = datetime.now(timezone.utc)
            return self._build_final_reflection(state)
        return "Фаза обновлена."

    async def _llm_reply(self, state: MetaTrainingSessionState, user_message: str, router: ModelRouter) -> str:
        prompt_bundle = self.prompt_builder.build(state)
        messages = [
            {"role": "system", "content": prompt_bundle.system_prompt},
            {"role": "user", "content": user_message or "(пауза)"},
        ]
        try:
            reply = await router.call_model(
                messages,
                router.pedagogy_model(),
                temperature=0.4,
                max_tokens=320,
            )
            text = (reply or "").strip()
            return text or prompt_bundle.fallback_reply
        except Exception:
            return prompt_bundle.fallback_reply

    def _build_final_reflection(self, state: MetaTrainingSessionState) -> str:
        scores = state.scores.capped()
        base = (
            "Сессия закрыта. "
            f"Сильнее всего проявились: вопросы {scores.inquisitiveness}/10, рамки {scores.frame_agility}/10, "
            f"работа с неопределённостью {scores.uncertainty_tolerance}/10, допущения {scores.assumption_detection}/10, "
            f"рефлексия {scores.meta_reflection}/10. "
            f"Начислено {state.awarded_wisdom_points} Wisdom Points."
        )
        extras: list[str] = []
        if state.evaluation.comment:
            extras.append(state.evaluation.comment)
        if state.evaluation.confidence is not None:
            extras.append(f"Уверенность оценки: {state.evaluation.confidence:.2f}.")
        if state.evaluation.flags:
            extras.append("Флаги: " + ", ".join(state.evaluation.flags) + ".")
        if extras:
            return f"{base} {' '.join(extras)}"
        return base

    async def _build_router(self, db_user: User | None) -> ModelRouter:
        if db_user is None:
            return ModelRouter()

        def _run() -> ModelRouter:
            with SessionLocal() as db:
                return build_model_router_for_user(db, db_user.id)

        return await run_in_threadpool(_run)

    async def _award_wisdom(self, redis_client: Any, session_id: str, db_user: User | None, reward: int) -> None:
        account_user_id = db_user.id if db_user else None
        progress, _ = await load_progress(redis_client, session_id, account_user_id)
        progress.wisdom_points += reward
        progress.level = max(1, progress.wisdom_points // 150 + 1)
        await save_progress(redis_client, session_id, progress, account_user_id)
        if db_user:
            def _persist() -> None:
                with SessionLocal() as db:
                    apply_redis_state_to_db(db, db_user.id, progress)

            await run_in_threadpool(_persist)

    async def _persist_result(self, user_id: int, state: MetaTrainingSessionState) -> None:
        def _run() -> None:
            with SessionLocal() as db:
                row = MetaTrainingSession(
                    user_id=user_id,
                    session_key=state.session_id,
                    thesis=state.thesis,
                    topic_slug=state.topic_slug,
                    final_phase=state.phase.value,
                    scores={
                        **state.scores.capped().model_dump(),
                        "total": state.scores.capped().total,
                        "evaluation": state.evaluation.model_dump(mode="json"),
                    },
                    questions=[q.model_dump(mode="json") for q in state.questions],
                    frames=[f.model_dump(mode="json") for f in state.frames],
                    transcript=[m.model_dump(mode="json") for m in state.transcript[-40:]],
                    reflection_summary=state.reflection_summary,
                    confidence_label=state.confidence_label,
                    awarded_wisdom_points=state.awarded_wisdom_points,
                    started_at=state.created_at,
                    ended_at=state.completed_at or datetime.now(timezone.utc),
                )
                db.add(row)
                db.commit()

        await run_in_threadpool(_run)

    async def _load(self, redis_client: Any, session_id: str) -> MetaTrainingSessionState:
        from app.services.meta_training_store import load_meta_training_state

        state = await load_meta_training_state(redis_client, session_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Meta-training session not found")
        return state

    async def _save(self, redis_client: Any, state: MetaTrainingSessionState) -> None:
        from app.services.meta_training_store import save_meta_training_state

        await save_meta_training_state(redis_client, state)

    @staticmethod
    def _assistant_message(text: str, phase: MetaTrainingPhase) -> MetaMessage:
        return MetaMessage(id=str(uuid4()), role="assistant", text=text, phase=phase)

    @staticmethod
    def _user_message(text: str, phase: MetaTrainingPhase) -> MetaMessage:
        return MetaMessage(id=str(uuid4()), role="user", text=text, phase=phase)

    @staticmethod
    def _messages_payload(state: MetaTrainingSessionState) -> list[dict[str, Any]]:
        return [m.model_dump(mode="json") for m in state.transcript]

    @staticmethod
    def _merge_scores(current: MetaScores, extra: MetaScores) -> MetaScores:
        return MetaScores(
            inquisitiveness=current.inquisitiveness + extra.inquisitiveness,
            frame_agility=current.frame_agility + extra.frame_agility,
            uncertainty_tolerance=current.uncertainty_tolerance + extra.uncertainty_tolerance,
            assumption_detection=current.assumption_detection + extra.assumption_detection,
            meta_reflection=current.meta_reflection + extra.meta_reflection,
        ).capped()

    @staticmethod
    def _finalize_scores(heuristic_scores: MetaScores, evaluated_scores: MetaScores) -> MetaScores:
        heuristic = heuristic_scores.capped()
        evaluated = evaluated_scores.capped()
        return MetaScores(
            inquisitiveness=max(heuristic.inquisitiveness, evaluated.inquisitiveness),
            frame_agility=max(heuristic.frame_agility, evaluated.frame_agility),
            uncertainty_tolerance=max(heuristic.uncertainty_tolerance, evaluated.uncertainty_tolerance),
            assumption_detection=max(heuristic.assumption_detection, evaluated.assumption_detection),
            meta_reflection=max(heuristic.meta_reflection, evaluated.meta_reflection),
        ).capped()

    @staticmethod
    def _pick_thesis(session_id: str, preferred_topic: str | None) -> dict[str, str]:
        if preferred_topic and preferred_topic.strip():
            topic = preferred_topic.strip()
            return {
                "slug": topic.lower().replace(" ", "-")[:64],
                "thesis": f"{topic}: выбери такую рамку исследования, которая заставит тебя сначала задавать вопросы, а не отвечать.",
            }
        digest = hashlib.sha256(session_id.encode()).hexdigest()
        idx = int(digest[:8], 16) % len(_THESIS_LIBRARY)
        return _THESIS_LIBRARY[idx]
