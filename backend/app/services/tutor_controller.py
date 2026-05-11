"""
Controller v2: поведение сессии. Порядок: Controller → Prompt Builder → Model Router → Validator (внутри router).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Literal

from app.models.pedagogy import PedagogyTurnContext
from app.models.state import TutorState
from app.models.user_memory import UserMemory
from app.services.cheat_detector import CHEAT_REPLY, is_cheating
from app.services.memory_manager import format_memory_for_prompt
from app.services.model_router import ModelRouter
from app.services.prompt_builder import build_prompt
from app.services.response_validator import normalize_response_text
from app.services.skill_tree_manager import canonical_subject_topic
from app.services.tutor_prompt import postprocess_tutor_response
from app.services.user_profiler import detect_user_type

ChatAction = Literal["none", "hint", "give_up"]
log = logging.getLogger(__name__)
_START_QUESTION_MARKERS = (
    "задавай вопросы",
    "задавай вопрос",
    "спрашивай",
    "начинай",
    "погнали",
    "давай",
)
_TOPIC_CHOICE_MARKERS = (
    "уравнения",
    "системы уравнений",
    "система уравнений",
    "геометрия",
    "дроби",
    "линейные уравнения",
    "квадратные уравнения",
)
_EQUATION_STEP_RE = re.compile(r"[0-9a-zа-яёxх]+\s*=\s*[^?=]+", re.IGNORECASE)
_SOLVED_X_RE = re.compile(r"^[xх]\s*=\s*[-+]?\d+(?:[.,]\d+)?$", re.IGNORECASE)
_VERIFICATION_RE = re.compile(r"^\s*\d+(?:[.,]\d+)?\s*=\s*\d+(?:[.,]\d+)?(?:\s|$)", re.IGNORECASE)
_CYRILLIC_CHE_RE = re.compile(r"^ч\s*=\s*[-+]?\d+(?:[.,]\d+)?$", re.IGNORECASE)


@dataclass
class TurnPlan:
    user_line: str
    mode: str
    prompt: str | None = None
    immediate_reply: str | None = None
    persist_history: bool = True


_TOPIC_PATTERNS = [
    re.compile(r"хочу\s+изучить\s+(?P<t>.+)", re.IGNORECASE),
    re.compile(r"тема:\s*(?P<t>.+)", re.IGNORECASE),
    re.compile(r"учим\s+(?P<t>.+)", re.IGNORECASE),
    re.compile(
        r"(?:выбрал|выбрала|выбираю|занимаемся|учимся)\s+(?P<t>.+)",
        re.IGNORECASE,
    ),
    re.compile(r"предмет\s*[:\-]?\s*(?P<t>.+)", re.IGNORECASE),
]

_FRUSTRATION_MARKERS = ("не знаю", "хз", "без понятия")

# Не считать «застреванием» явные запросы помощи (иначе «Дай пример» крутит счётчик).
_HELP_REQUEST_MARKERS = (
    "дай пример",
    "дай подсказку",
    "подсказку",
    "запрошена подсказка",
    "сдаюсь",
    "объясни",
)


def _maybe_set_topic(state: TutorState, user_text: str) -> None:
    t = user_text.strip()
    for pat in _TOPIC_PATTERNS:
        m = pat.search(t)
        if m:
            state.topic = m.group("t").strip().rstrip(".")
            return
    subj = canonical_subject_topic(t)
    if subj:
        state.topic = subj


def _safe_tutor_fallback(state: TutorState, user_line: str = "") -> str:
    topic = (state.topic or "").strip().lower()
    text = (user_line or "").strip().lower()
    if "уравн" in topic or "уравн" in text:
        return "Хорошо. Начнём с простого: какое действие удобно сделать первым в уравнении 3x + 5 = 20?"
    if "систем" in topic or "систем" in text:
        return "Хорошо. С чего обычно удобно начать решение системы из двух уравнений?"
    if "геометр" in topic or "геометр" in text:
        return "Хорошо. Какую фигуру или теорему из геометрии ты хочешь разобрать сначала?"
    if "дроб" in topic or "дроб" in text:
        return "Хорошо. Какое первое действие ты бы сделал при решении уравнения с дробями?"
    if topic:
        return f"Хорошо. Начнём по теме «{state.topic}»: какой первый шаг ты бы предложил?"
    return "Хорошо. С какой математической задачи начнём?"


def _is_start_question_request(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return False
    return any(marker in normalized for marker in _START_QUESTION_MARKERS)


def _is_topic_choice(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized or len(normalized.split()) > 4:
        return False
    return any(marker == normalized for marker in _TOPIC_CHOICE_MARKERS)


def _equation_followup_question(user_line: str) -> str | None:
    text = (user_line or "").strip()
    lowered = text.lower()
    compact = re.sub(r"\s+", "", lowered)
    if _CYRILLIC_CHE_RE.match(lowered):
        return "Похоже, здесь опечатка в переменной. Какая буква должна стоять вместо «ч»?"
    if _SOLVED_X_RE.match(compact):
        return "Хорошо. Теперь подставь это значение в исходное уравнение 3x + 5 = 20. Что получится?"
    if _VERIFICATION_RE.match(lowered):
        left, right = [part.strip() for part in text.split("=", 1)]
        if left == right:
            return "Хорошо. Значит, решение найдено. Почему равенство " + text + " подтверждает, что x = 5 подходит?"
        return "Хорошо. Что говорит эта проверка о найденном значении x?"
    if not _EQUATION_STEP_RE.search(lowered):
        return None
    if "=" not in text:
        return None
    left, right = [part.strip() for part in text.split("=", 1)]
    if ("х" in left or "x" in left) and not ("х" in right or "x" in right):
        return "Хорошо. Теперь как из записи " + text + " получить значение x?"
    if ("х" in left or "x" in left) and ("-" in right or "+" in right):
        return "Хорошо. Что нужно сделать дальше, чтобы в левой части осталось только 3x?"
    if ("х" in left or "x" in left) and any(ch.isdigit() for ch in right):
        return "Хорошо. Какой следующий шаг поможет оставить x без коэффициента?"
    return None


class TutorController:
    def __init__(self, router: ModelRouter | None = None) -> None:
        self._router = router or ModelRouter()
        self.last_prompt: str | None = None
        self.last_user_line: str | None = None
        self.last_mode: str | None = None
        self.used_llm: bool = False

    def update_state(self, state: TutorState, user_input: str) -> TutorState:
        raw = (user_input or "").strip()
        low = raw.lower()
        prev_attempts = state.attempts
        state.attempts += 1

        marker = any(x in low for x in _FRUSTRATION_MARKERS)
        very_short = 0 < len(raw) < 5

        if marker or very_short:
            state.frustration += 1

        # «Застрял» после пары шагов: короткие ответы без маркеров и без явной просьбы о помощи
        help_request = any(x in low for x in _HELP_REQUEST_MARKERS)
        if prev_attempts >= 2 and 5 <= len(raw) < 15 and not marker and not help_request:
            state.frustration += 1

        if len(raw) > 200:
            state.frustration += 1

        state.mode = self.decide_mode(state)
        return state

    def decide_mode(self, state: TutorState) -> str:
        ut = getattr(state, "user_type", "lazy") or "lazy"
        if ut not in ("lazy", "anxious", "thinker"):
            ut = "lazy"

        fr_th = 3 if ut == "anxious" else 2
        if state.frustration >= fr_th:
            return "hint"

        if state.attempts < 2:
            return "question"

        if ut == "thinker":
            if state.attempts < 5:
                return "question"
            if state.attempts < 8:
                return "hint"
            return "explain"

        if ut == "lazy":
            if state.attempts < 4:
                return "hint"
            return "explain"

        if state.attempts < 4:
            return "hint"
        return "explain"

    def _prepare_turn(
        self,
        state: TutorState,
        user_message: str,
        action: ChatAction = "none",
        long_term_memory: UserMemory | None = None,
        pedagogy: PedagogyTurnContext | None = None,
    ) -> TurnPlan:
        text = (user_message or "").strip()
        mem = long_term_memory or UserMemory()
        ped = pedagogy or PedagogyTurnContext()

        if text and is_cheating(text):
            return TurnPlan(
                user_line=text,
                mode=state.mode,
                immediate_reply=CHEAT_REPLY,
            )

        if action == "give_up":
            attempts_before = state.attempts
            state.mode = "explain"
            user_line = text or "(сдаюсь — нужно краткое объяснение и контрольный вопрос в конце)"
            if text:
                state.user_type = detect_user_type(text, state.user_type)
                _maybe_set_topic(state, text)
            mb = format_memory_for_prompt(mem, state, text, attempts_before == 0)
            prompt = self._build_turn_prompt(
                state.mode,
                state.topic,
                state.history,
                state.user_type,
                memory_block=mb,
                tutor_mode=ped.tutor_mode,
                difficulty_level=ped.difficulty_level,
                adaptive_difficulty=ped.adaptive_difficulty,
                russian_only=ped.russian_only,
                fallacy_instruction=ped.fallacy_instruction,
                persistent_profile=ped.persistent_profile,
                tutor_state=ped.tutor_state,
            )
            return TurnPlan(user_line=user_line, mode=state.mode, prompt=prompt)

        if action == "hint":
            attempts_before = state.attempts
            hint_line = text or "(запрошена подсказка)"
            if text:
                _maybe_set_topic(state, text)
            state.user_type = detect_user_type(hint_line, state.user_type)
            mb = format_memory_for_prompt(mem, state, hint_line, attempts_before == 0)
            self.update_state(state, hint_line)
            # Явный hint при кнопке (decide_mode мог оставить question при малых attempts)
            state.mode = "explain" if state.attempts >= 4 else "hint"
            prompt = self._build_turn_prompt(
                state.mode,
                state.topic,
                state.history,
                state.user_type,
                memory_block=mb,
                tutor_mode=ped.tutor_mode,
                difficulty_level=ped.difficulty_level,
                adaptive_difficulty=ped.adaptive_difficulty,
                russian_only=ped.russian_only,
                fallacy_instruction=ped.fallacy_instruction,
                persistent_profile=ped.persistent_profile,
                tutor_state=ped.tutor_state,
            )
            return TurnPlan(user_line=hint_line, mode=state.mode, prompt=prompt)

        if not text:
            return TurnPlan(
                user_line="",
                mode=state.mode,
                immediate_reply="Напиши сообщение или используй кнопки подсказки / сдаться.",
                persist_history=False,
            )

        if _is_start_question_request(text):
            _maybe_set_topic(state, text)
            return TurnPlan(
                user_line=text,
                mode="question",
                immediate_reply=_safe_tutor_fallback(state, text),
            )

        if _is_topic_choice(text):
            state.topic = text
            return TurnPlan(
                user_line=text,
                mode="question",
                immediate_reply=_safe_tutor_fallback(state, text),
            )

        if "уравн" in (state.topic or "").lower():
            followup = _equation_followup_question(text)
            if followup:
                return TurnPlan(
                    user_line=text,
                    mode="question",
                    immediate_reply=followup,
                )

        attempts_before = state.attempts
        _maybe_set_topic(state, text)
        state.user_type = detect_user_type(text, state.user_type)
        mb = format_memory_for_prompt(mem, state, text, attempts_before == 0)
        self.update_state(state, text)
        prompt = self._build_turn_prompt(
            state.mode,
            state.topic,
            state.history,
            state.user_type,
            memory_block=mb,
            tutor_mode=ped.tutor_mode,
            difficulty_level=ped.difficulty_level,
            adaptive_difficulty=ped.adaptive_difficulty,
            russian_only=ped.russian_only,
            fallacy_instruction=ped.fallacy_instruction,
            persistent_profile=ped.persistent_profile,
            tutor_state=ped.tutor_state,
        )
        return TurnPlan(user_line=text, mode=state.mode, prompt=prompt)

    def _build_turn_prompt(
        self,
        mode: str,
        topic: str,
        history: list[dict[str, Any]],
        user_type: str,
        **kwargs: Any,
    ) -> str:
        prompt = build_prompt(mode, topic, history, user_type, **kwargs)
        last_question = self._last_assistant_question(history)
        if not last_question:
            return prompt
        anti_repeat = (
            "\n\nАнти-повтор предыдущего шага (обязательно):\n"
            f"Предыдущий вопрос тьютора: «{last_question}»\n"
            "Считай, что этот шаг уже был. Не повторяй этот вопрос и не перефразируй его слишком близко. "
            "Если ученик ответил удовлетворительно, переходи к следующему более глубокому вопросу. "
            "Если ответ слабый, задай новый уточняющий вопрос, но не копию предыдущего."
        )
        return prompt + anti_repeat

    @staticmethod
    def _last_assistant_question(history: list[dict[str, Any]]) -> str:
        for h in reversed(history):
            if not isinstance(h, dict):
                continue
            if h.get("role") == "assistant":
                return str(h.get("content") or "").strip()
        return ""

    async def _finalize_reply(
        self,
        state: TutorState,
        plan: TurnPlan,
        reply: str,
        *,
        allow_retry: bool = True,
    ) -> str:
        normalized = normalize_response_text(reply)
        last_question = self._last_assistant_question(state.history)
        processed, repeated, answered_for_student, invalid = postprocess_tutor_response(
            normalized, last_question
        )
        if (
            (not repeated and not answered_for_student and not invalid)
            or not last_question
            or plan.immediate_reply is not None
            or not plan.prompt
            or not allow_retry
        ):
            if repeated and last_question:
                log.warning(
                    "tutor repeated question without retry topic=%s mode=%s question=%r response=%r",
                    state.topic,
                    plan.mode,
                    last_question[:200],
                    processed[:200],
                )
            if answered_for_student:
                log.warning(
                    "tutor answered for student without retry topic=%s mode=%s response=%r",
                    state.topic,
                    plan.mode,
                    processed[:200],
                )
                return _safe_tutor_fallback(state, plan.user_line)
            if invalid:
                log.warning(
                    "tutor produced invalid/meta reply without retry topic=%s mode=%s response=%r",
                    state.topic,
                    plan.mode,
                    processed[:200],
                )
                return _safe_tutor_fallback(state, plan.user_line)
            return processed

        log.warning(
            "tutor invalid reply, retrying topic=%s mode=%s repeated=%s answered_for_student=%s invalid=%s question=%r response=%r",
            state.topic,
            plan.mode,
            repeated,
            answered_for_student,
            invalid,
            last_question[:200],
            processed[:200],
        )
        retry_prompt = (
            plan.prompt
            + "\n\nКритическое требование:\n"
            + f"Ты только что почти повторил старый вопрос: «{last_question}».\n"
            + "Перегенерируй ответ так, чтобы он двигал диалог дальше. Не повторяй и не перефразируй этот вопрос.\n"
            + "Ты не имеешь права отвечать за ученика, писать «правильный ответ», «ответ:», "
            + "«ученик мог бы ответить» и любые похожие формулировки.\n"
            + "Пиши только по-русски. Не вставляй переводов, английских абзацев, эмодзи, служебных хвостов и мета-комментариев."
        )
        retry_user_line = (
            plan.user_line
            + "\n\nНе повторяй предыдущий вопрос тьютора. Сразу перейди к следующему логическому шагу. "
            + "Не отвечай за ученика и не говори от его имени."
        )
        retried = await self._router.generate(retry_prompt, retry_user_line, plan.mode)
        retried = normalize_response_text(retried)
        retried_processed, retried_repeated, retried_answered_for_student, retried_invalid = (
            postprocess_tutor_response(retried, last_question)
        )
        if retried_repeated or retried_answered_for_student or retried_invalid:
            log.warning(
                "tutor invalid reply after retry topic=%s mode=%s repeated=%s answered_for_student=%s invalid=%s question=%r response=%r",
                state.topic,
                plan.mode,
                retried_repeated,
                retried_answered_for_student,
                retried_invalid,
                last_question[:200],
                retried_processed[:200],
            )
        if retried_answered_for_student or retried_invalid:
            return _safe_tutor_fallback(state, plan.user_line)
        return retried_processed

    def _commit_turn(self, state: TutorState, plan: TurnPlan, reply: str) -> None:
        if not plan.persist_history:
            return
        state.history.append({"role": "user", "content": plan.user_line})
        state.history.append({"role": "assistant", "content": reply})

    def plan_turn(
        self,
        state: TutorState,
        user_message: str,
        action: ChatAction = "none",
        long_term_memory: UserMemory | None = None,
        pedagogy: PedagogyTurnContext | None = None,
    ) -> TurnPlan:
        return self._prepare_turn(state, user_message, action, long_term_memory, pedagogy)

    async def finalize_planned_reply(
        self,
        state: TutorState,
        plan: TurnPlan,
        reply: str,
        *,
        allow_retry: bool = True,
    ) -> str:
        return await self._finalize_reply(state, plan, reply, allow_retry=allow_retry)

    def commit_turn(self, state: TutorState, plan: TurnPlan, reply: str) -> None:
        self._commit_turn(state, plan, reply)

    async def handle_turn(
        self,
        state: TutorState,
        user_message: str,
        action: ChatAction = "none",
        long_term_memory: UserMemory | None = None,
        pedagogy: PedagogyTurnContext | None = None,
    ) -> tuple[str, str]:
        plan = self._prepare_turn(state, user_message, action, long_term_memory, pedagogy)
        self.last_prompt = plan.prompt
        self.last_user_line = plan.user_line
        self.last_mode = plan.mode
        self.used_llm = plan.immediate_reply is None and bool(plan.prompt)
        reply = (
            plan.immediate_reply
            if plan.immediate_reply is not None
            else await self._router.generate(plan.prompt or "", plan.user_line, plan.mode)
        )
        reply = await self._finalize_reply(state, plan, reply, allow_retry=True)
        self._commit_turn(state, plan, reply)
        return reply, plan.mode

    async def stream_turn(
        self,
        state: TutorState,
        user_message: str,
        action: ChatAction = "none",
        long_term_memory: UserMemory | None = None,
        pedagogy: PedagogyTurnContext | None = None,
    ):
        plan = self._prepare_turn(state, user_message, action, long_term_memory, pedagogy)
        self.last_prompt = plan.prompt
        self.last_user_line = plan.user_line
        self.last_mode = plan.mode
        self.used_llm = plan.immediate_reply is None and bool(plan.prompt)
        if plan.immediate_reply is not None:
            reply = normalize_response_text(plan.immediate_reply)
            if reply:
                yield reply
            self._commit_turn(state, plan, reply)
            return

        parts: list[str] = []
        async for chunk in self._router.generate_stream(plan.prompt or "", plan.user_line, plan.mode):
            if not chunk:
                continue
            parts.append(chunk)
        reply = await self._finalize_reply(state, plan, "".join(parts).strip() or "…", allow_retry=False)
        self._commit_turn(state, plan, reply)
        if reply:
            yield reply
