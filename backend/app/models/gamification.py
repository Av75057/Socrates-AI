"""Модели и каталоги геймификации (Wisdom Points, достижения, ежедневные вызовы)."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class AchievementDef(BaseModel):
    id: str
    name: str
    description: str
    reward_points: int


ACHIEVEMENTS: list[AchievementDef] = [
    AchievementDef(
        id="first_insight",
        name="Первый инсайт",
        description="Ты обменялся с тьютором десятью осмысленными репликами.",
        reward_points=50,
    ),
    AchievementDef(
        id="deep_thinker",
        name="Глубокий мыслитель",
        description="За один диалог задал пять уточняющих вопросов.",
        reward_points=75,
    ),
    AchievementDef(
        id="logic_master",
        name="Мастер логики",
        description="Три раза подряд дал развёрнутый ответ со связками причинности.",
        reward_points=100,
    ),
    AchievementDef(
        id="persistent",
        name="Упорство",
        description="Трижды ответил после сложных вопросов тьютора и не сдался.",
        reward_points=60,
    ),
    AchievementDef(
        id="challenger",
        name="Искатель вызовов",
        description="Выполнил три ежедневных вызова (в разные дни).",
        reward_points=80,
    ),
]

ACHIEVEMENT_BY_ID: dict[str, AchievementDef] = {a.id: a for a in ACHIEVEMENTS}


class DailyChallengeDef(BaseModel):
    id: str
    text: str


DAILY_CHALLENGES: list[DailyChallengeDef] = [
    DailyChallengeDef(
        id="why_prefix",
        text='Задай тьютору вопрос, начинающийся с «Почему»',
    ),
    DailyChallengeDef(
        id="life_example",
        text="Дай ответ, содержащий пример из жизни",
    ),
    DailyChallengeDef(
        id="no_negation",
        text='Не используй слово «не» в ответе',
    ),
    DailyChallengeDef(
        id="explain_premise",
        text="Попроси тьютора объяснить предпосылку твоего вопроса",
    ),
]


class UserProgressState(BaseModel):
    """Полное состояние в Redis (включая служебные поля)."""

    user_id: str
    wisdom_points: int = 0
    level: int = 1
    achievements: list[str] = Field(default_factory=list)
    daily_challenge_completed: bool = False
    last_daily_challenge_date: date | None = None
    streak_days: int = 0
    last_activity_utc_date: date | None = None
    challenge_utc_date: date | None = None
    daily_challenge_id: str | None = None
    total_user_turns: int = 0
    logic_good_streak: int = 0
    answered_while_hard_session: int = 0
    clarifying_questions_session: int = 0
    give_up_used_session: bool = False
    challenges_completed_total: int = 0

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> UserProgressState | None:
        try:
            return cls.model_validate_json(raw)
        except (ValueError, TypeError):
            return None


class UserProgressPublic(BaseModel):
    """Ответ API: только то, что нужно клиенту."""

    user_id: str
    wisdom_points: int = 0
    level: int = 1
    achievements: list[str] = Field(default_factory=list)
    daily_challenge_completed: bool = False
    last_daily_challenge_date: date | None = None
    streak_days: int = 0
    daily_challenge_id: str | None = None
    total_user_turns: int = 0
    logic_good_streak: int = 0


def merge_user_progress_states(a: UserProgressState, b: UserProgressState) -> UserProgressState:
    """
    Объединить два состояния (например гостевой ключ Redis и аккаунт пользователя).
    Накопительные поля — по максимуму; ежедневные флаги — с той стороны, где больше очков мудрости.
    """
    take_daily_from = a if a.wisdom_points >= b.wisdom_points else b
    out = take_daily_from.model_copy(deep=True)
    out.wisdom_points = max(a.wisdom_points, b.wisdom_points)
    out.achievements = list(dict.fromkeys([*a.achievements, *b.achievements]))
    out.total_user_turns = max(a.total_user_turns, b.total_user_turns)
    out.logic_good_streak = max(a.logic_good_streak, b.logic_good_streak)
    out.streak_days = max(a.streak_days, b.streak_days)
    out.challenges_completed_total = max(a.challenges_completed_total, b.challenges_completed_total)
    out.answered_while_hard_session = max(a.answered_while_hard_session, b.answered_while_hard_session)
    out.clarifying_questions_session = max(a.clarifying_questions_session, b.clarifying_questions_session)
    out.give_up_used_session = a.give_up_used_session or b.give_up_used_session
    act = [d for d in (a.last_activity_utc_date, b.last_activity_utc_date) if d is not None]
    out.last_activity_utc_date = max(act) if act else None
    lcd = [d for d in (a.last_daily_challenge_date, b.last_daily_challenge_date) if d is not None]
    out.last_daily_challenge_date = max(lcd) if lcd else None
    out.level = recalc_level(out.wisdom_points)
    return out


def state_to_public(s: UserProgressState) -> UserProgressPublic:
    return UserProgressPublic(
        user_id=s.user_id,
        wisdom_points=s.wisdom_points,
        level=s.level,
        achievements=list(s.achievements),
        daily_challenge_completed=s.daily_challenge_completed,
        last_daily_challenge_date=s.last_daily_challenge_date,
        streak_days=s.streak_days,
        daily_challenge_id=s.daily_challenge_id,
        total_user_turns=s.total_user_turns,
        logic_good_streak=s.logic_good_streak,
    )


def recalc_level(wisdom_points: int) -> int:
    return max(1, wisdom_points // 150 + 1)


def deep_link_words(text: str) -> bool:
    low = text.lower()
    return any(
        w in low
        for w in (
            "потому что",
            "следовательно",
            "так как",
            "поэтому",
            "значит,",
        )
    )


def is_deep_answer(text: str) -> bool:
    t = text.strip()
    return len(t) > 100 and deep_link_words(t)


def word_count_ru(text: str) -> int:
    return len(re.findall(r"\S+", text.strip()))


def is_logic_master_candidate(text: str) -> bool:
    t = text.strip()
    return word_count_ru(t) > 50 and deep_link_words(t)


def is_clarifying_question(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    low = t.lower()
    if t.endswith("?"):
        return True
    needles = (
        "уточни",
        "что значит",
        "не понял",
        "не понимаю",
        "объясни про",
        "а если",
        "что если",
        "почему именно",
        "как это",
        "распиши",
    )
    return any(n in low for n in needles)


def pick_daily_challenge_id(user_id: str, d: date) -> str:
    import hashlib

    h = hashlib.sha256(f"{user_id}\n{d.isoformat()}".encode()).hexdigest()
    idx = int(h[:8], 16) % len(DAILY_CHALLENGES)
    return DAILY_CHALLENGES[idx].id


def challenge_text(ch_id: str | None) -> str:
    if not ch_id:
        return ""
    for c in DAILY_CHALLENGES:
        if c.id == ch_id:
            return c.text
    return ""


def matches_daily_challenge(ch_id: str, user_message: str, action: str) -> bool:
    msg = (user_message or "").strip()
    if not msg or action == "give_up":
        return False
    low = msg.lower()
    if ch_id == "why_prefix":
        return low.startswith("почему")
    if ch_id == "life_example":
        return any(
            x in low
            for x in (
                "жизн",
                "в жизни",
                "из жизни",
                "реальн",
                "например",
                "когда я",
                "у меня был",
                "случай",
            )
        )
    if ch_id == "no_negation":
        words = re.findall(r"[а-яёa-z0-9]+", low)
        return "не" not in words
    if ch_id == "explain_premise":
        return any(
            x in low
            for x in (
                "предпосылк",
                "предпосыла",
                "зачем ты",
                "почему ты спросил",
                "почему ты зада",
                "объясни предпосыл",
            )
        )
    return False


def bump_activity_streak(s: UserProgressState, today: date) -> None:
    if s.last_activity_utc_date is None:
        s.streak_days = max(1, s.streak_days or 1)
    elif s.last_activity_utc_date == today:
        pass
    else:
        delta = (today - s.last_activity_utc_date).days
        if delta == 1:
            s.streak_days += 1
        else:
            s.streak_days = 1
    s.last_activity_utc_date = today


def ensure_challenge_day(s: UserProgressState, today: date) -> None:
    if s.challenge_utc_date != today:
        s.challenge_utc_date = today
        s.daily_challenge_completed = False
        s.daily_challenge_id = pick_daily_challenge_id(s.user_id, today)


def grant_achievement(s: UserProgressState, aid: str, new_ids: list[str]) -> int:
    if aid in s.achievements:
        return 0
    spec = ACHIEVEMENT_BY_ID.get(aid)
    if not spec:
        return 0
    s.achievements.append(aid)
    new_ids.append(aid)
    return spec.reward_points


def process_user_response(
    s: UserProgressState,
    ctx: dict[str, Any],
    today: date,
) -> tuple[list[str], list[str]]:
    """
    Обновляет состояние по ответу пользователя.
    Возвращает (toast_messages, new_achievement_ids).
    """
    new_achievement_ids: list[str] = []
    toasts: list[str] = []

    ensure_challenge_day(s, today)
    bump_activity_streak(s, today)

    user_message = str(ctx.get("user_message") or "").strip()
    action = str(ctx.get("action") or "none")
    attempts_before = int(ctx.get("attempts_before") or 0)

    if action == "give_up":
        s.give_up_used_session = True

    wp_delta = 0
    is_deep = False
    if user_message:
        wp_delta += 1
        if is_deep_answer(user_message):
            wp_delta += 5
            is_deep = True

    if wp_delta:
        s.wisdom_points += wp_delta
        deep_extra = " (бонус за глубокий ответ)" if is_deep else ""
        toasts.append(f"+{wp_delta} очков мудрости{deep_extra}")

    if user_message and action != "give_up":
        s.total_user_turns += 1
        if s.total_user_turns >= 10 and "first_insight" not in s.achievements:
            bonus = grant_achievement(s, "first_insight", new_achievement_ids)
            if bonus:
                s.wisdom_points += bonus
                toasts.append(f"Достижение: {ACHIEVEMENT_BY_ID['first_insight'].name} (+{bonus} WP)")

    if user_message and action == "none":
        if is_clarifying_question(user_message):
            s.clarifying_questions_session += 1
            if s.clarifying_questions_session >= 5 and "deep_thinker" not in s.achievements:
                bonus = grant_achievement(s, "deep_thinker", new_achievement_ids)
                if bonus:
                    s.wisdom_points += bonus
                    toasts.append(f"Достижение: {ACHIEVEMENT_BY_ID['deep_thinker'].name} (+{bonus} WP)")

        if is_logic_master_candidate(user_message):
            s.logic_good_streak += 1
        else:
            s.logic_good_streak = 0
        if s.logic_good_streak >= 3 and "logic_master" not in s.achievements:
            bonus = grant_achievement(s, "logic_master", new_achievement_ids)
            if bonus:
                s.wisdom_points += bonus
                toasts.append(f"Достижение: {ACHIEVEMENT_BY_ID['logic_master'].name} (+{bonus} WP)")

        if attempts_before >= 2 and not s.give_up_used_session:
            s.answered_while_hard_session += 1
            if s.answered_while_hard_session >= 3 and "persistent" not in s.achievements:
                bonus = grant_achievement(s, "persistent", new_achievement_ids)
                if bonus:
                    s.wisdom_points += bonus
                    toasts.append(f"Достижение: {ACHIEVEMENT_BY_ID['persistent'].name} (+{bonus} WP)")

    ch_id = s.daily_challenge_id
    if (
        ch_id
        and not s.daily_challenge_completed
        and matches_daily_challenge(ch_id, user_message, action)
    ):
        s.daily_challenge_completed = True
        s.last_daily_challenge_date = today
        s.wisdom_points += 20
        s.challenges_completed_total += 1
        toasts.append("+20 очков мудрости за ежедневный вызов")
        if s.challenges_completed_total >= 3 and "challenger" not in s.achievements:
            bonus = grant_achievement(s, "challenger", new_achievement_ids)
            if bonus:
                s.wisdom_points += bonus
                toasts.append(f"Достижение: {ACHIEVEMENT_BY_ID['challenger'].name} (+{bonus} WP)")

    s.level = recalc_level(s.wisdom_points)
    return toasts, new_achievement_ids


def reset_session_counters(s: UserProgressState) -> None:
    s.answered_while_hard_session = 0
    s.clarifying_questions_session = 0
    s.give_up_used_session = False
    s.logic_good_streak = 0
