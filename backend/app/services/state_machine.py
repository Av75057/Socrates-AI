from __future__ import annotations

from enum import Enum


class DialoguePhase(str, Enum):
    GREETING = "greeting"
    AWAITING_ANSWER = "awaiting_answer"
    HINT_PROVIDED = "hint_provided"
    ANSWER_ANALYZED = "answer_analyzed"
    CORRECT = "correct"
    INCORRECT_RETRY = "incorrect_retry"
    GIVE_UP = "give_up"
    CLOSING = "closing"


ALLOWED_TRANSITIONS: dict[DialoguePhase, set[DialoguePhase]] = {
    DialoguePhase.GREETING: {
        DialoguePhase.GREETING,
        DialoguePhase.AWAITING_ANSWER,
        DialoguePhase.HINT_PROVIDED,
        DialoguePhase.GIVE_UP,
        DialoguePhase.CLOSING,
    },
    DialoguePhase.AWAITING_ANSWER: {
        DialoguePhase.AWAITING_ANSWER,
        DialoguePhase.HINT_PROVIDED,
        DialoguePhase.ANSWER_ANALYZED,
        DialoguePhase.CLOSING,
    },
    DialoguePhase.HINT_PROVIDED: {
        DialoguePhase.HINT_PROVIDED,
        DialoguePhase.AWAITING_ANSWER,
        DialoguePhase.CLOSING,
    },
    DialoguePhase.ANSWER_ANALYZED: {
        DialoguePhase.ANSWER_ANALYZED,
        DialoguePhase.CORRECT,
        DialoguePhase.INCORRECT_RETRY,
        DialoguePhase.GIVE_UP,
        DialoguePhase.CLOSING,
    },
    DialoguePhase.CORRECT: {
        DialoguePhase.CORRECT,
        DialoguePhase.AWAITING_ANSWER,
        DialoguePhase.CLOSING,
    },
    DialoguePhase.INCORRECT_RETRY: {
        DialoguePhase.INCORRECT_RETRY,
        DialoguePhase.AWAITING_ANSWER,
        DialoguePhase.GIVE_UP,
        DialoguePhase.CLOSING,
    },
    DialoguePhase.GIVE_UP: {
        DialoguePhase.GIVE_UP,
        DialoguePhase.AWAITING_ANSWER,
        DialoguePhase.CLOSING,
    },
    DialoguePhase.CLOSING: {
        DialoguePhase.CLOSING,
    },
}


def validate_transition(current: DialoguePhase, new: DialoguePhase) -> bool:
    return new in ALLOWED_TRANSITIONS.get(current, set())
