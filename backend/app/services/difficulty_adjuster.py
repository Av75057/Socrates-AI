"""Правила изменения difficulty_level (1–5)."""

from __future__ import annotations

from app.models.pedagogy import UserPedagogyState


def apply_after_user_turn(state: UserPedagogyState, depth: float) -> None:
    """После осмысленного ответа пользователя (action=none)."""
    state.last_response_depth = depth
    if depth > 0.7:
        state.consecutive_deep += 1
        state.consecutive_shallow = 0
        state.deep_turns_in_dialog += 1
        cond_chain = state.consecutive_deep >= 3
        cond_total = state.deep_turns_in_dialog >= 5
        if cond_chain or cond_total:
            state.difficulty_level = min(5, state.difficulty_level + 1)
            state.consecutive_deep = 0
            state.deep_turns_in_dialog = 0
    elif depth < 0.3:
        state.consecutive_shallow += 1
        state.consecutive_deep = 0
        if state.consecutive_shallow >= 2:
            state.difficulty_level = max(1, state.difficulty_level - 1)
            state.consecutive_shallow = 0
    else:
        state.consecutive_deep = 0
        state.consecutive_shallow = 0


def apply_hint_penalty(state: UserPedagogyState) -> None:
    """Подсказка (кнопка или отдельный эндпоинт) понижает сложность."""
    state.difficulty_level = max(1, state.difficulty_level - 1)
    state.consecutive_deep = 0
    state.consecutive_shallow = 0
