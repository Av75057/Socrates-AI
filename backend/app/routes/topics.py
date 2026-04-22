from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_user, get_current_user_optional
from app.db.models import Topic, User, UserTopicProgress
from app.db.session import get_db
from app.deps import redis_dep
from app.models.state import TutorState
from app.services.conversation_db import append_tutor_opening, conversation_message_count, create_conversation
from app.services.redis_state import save_state
from app.services.topic_cache import invalidate_topics_cache, read_topics_cache, write_topics_cache

router = APIRouter(tags=["topics"])


class TopicProgressOut(BaseModel):
    completed: bool = False
    last_used: str | None = None
    rating: int | None = None


class TopicOut(BaseModel):
    id: int
    title: str
    description: str | None = None
    initial_prompt: str
    difficulty: int
    tags: list[str] = Field(default_factory=list)
    is_premium: bool = False
    usage_count: int = 0
    is_active: bool = True
    created_at: str
    created_by: int
    can_start: bool = True
    progress: TopicProgressOut | None = None


class TopicListResponse(BaseModel):
    items: list[TopicOut]
    total: int
    offset: int
    limit: int


class TopicStartResponse(BaseModel):
    conversation_id: int
    session_key: str
    title: str
    opening_message: str
    first_message: str
    started_at: str
    last_updated_at: str
    message_count: int


def _normalize_tags(raw: Any) -> list[str]:
    items = raw if isinstance(raw, list) else []
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        tag = str(item or "").strip().lower()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        out.append(tag[:48])
    return out


def _is_pro_user(user: User | None) -> bool:
    if user is None:
        return False
    plan = (user.subscription_plan or "free").strip().lower() or "free"
    status_value = (user.subscription_status or "active").strip().lower() or "active"
    return status_value == "active" and plan in {"pro", "yearly", "team"}


def _serialize_topic(topic: Topic, user: User | None, progress: UserTopicProgress | None) -> dict[str, Any]:
    return {
        "id": topic.id,
        "title": topic.title,
        "description": topic.description,
        "initial_prompt": topic.initial_prompt,
        "difficulty": int(topic.difficulty or 1),
        "tags": _normalize_tags(topic.tags),
        "is_premium": bool(topic.is_premium),
        "usage_count": int(topic.usage_count or 0),
        "is_active": bool(topic.is_active),
        "created_at": topic.created_at.isoformat(),
        "created_by": topic.created_by,
        "can_start": not topic.is_premium or _is_pro_user(user),
        "progress": {
            "completed": bool(progress.completed),
            "last_used": progress.last_used.isoformat() if progress and progress.last_used else None,
            "rating": progress.rating if progress else None,
        }
        if progress is not None
        else None,
    }


def _apply_topic_filters(
    topics: list[Topic],
    *,
    q: str,
    tags: list[str],
    difficulty_min: int,
    difficulty_max: int,
    free_only: bool,
) -> list[Topic]:
    search = q.strip().lower()
    tag_set = {tag.strip().lower() for tag in tags if tag.strip()}
    out: list[Topic] = []
    for topic in topics:
        if not topic.is_active:
            continue
        if free_only and topic.is_premium:
            continue
        difficulty = int(topic.difficulty or 1)
        if difficulty < difficulty_min or difficulty > difficulty_max:
            continue
        normalized_tags = set(_normalize_tags(topic.tags))
        if tag_set and not tag_set.issubset(normalized_tags):
            continue
        if search:
            hay = " ".join(
                [
                    str(topic.title or ""),
                    str(topic.description or ""),
                    " ".join(normalized_tags),
                ]
            ).lower()
            if search not in hay:
                continue
        out.append(topic)
    return out


def _sort_topics(topics: list[Topic], sort: str) -> list[Topic]:
    key = (sort or "popular").strip().lower()
    if key == "new":
        return sorted(topics, key=lambda item: (item.created_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    if key == "title":
        return sorted(topics, key=lambda item: str(item.title or "").lower())
    return sorted(
        topics,
        key=lambda item: (
            int(item.usage_count or 0),
            item.created_at or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )


@router.get("/topics/tags", response_model=list[str])
async def list_topic_tags(
    db: Session = Depends(get_db),
    r=Depends(redis_dep),
):
    cached = await read_topics_cache(r, "tags", {})
    if isinstance(cached, list):
        return [str(item) for item in cached]
    rows = db.execute(select(Topic).where(Topic.is_active.is_(True))).scalars().all()
    tags = sorted({tag for topic in rows for tag in _normalize_tags(topic.tags)})
    await write_topics_cache(r, "tags", {}, tags)
    return tags


@router.get("/topics", response_model=TopicListResponse)
async def list_topics(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    r=Depends(redis_dep),
    q: str = Query("", max_length=120),
    tags: list[str] = Query([]),
    difficulty_min: int = Query(1, ge=1, le=5),
    difficulty_max: int = Query(5, ge=1, le=5),
    free_only: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=100),
    sort: str = Query("popular"),
):
    if difficulty_min > difficulty_max:
        raise HTTPException(status_code=400, detail="difficulty_min must be <= difficulty_max")
    cache_payload = {
        "q": q.strip().lower(),
        "tags": sorted([tag.strip().lower() for tag in tags if tag.strip()]),
        "difficulty_min": difficulty_min,
        "difficulty_max": difficulty_max,
        "free_only": free_only,
        "offset": offset,
        "limit": limit,
        "sort": sort,
    }
    if user is None:
        cached = await read_topics_cache(r, "list", cache_payload)
        if isinstance(cached, dict):
            return TopicListResponse(**cached)

    rows = db.execute(select(Topic)).scalars().all()
    filtered = _sort_topics(
        _apply_topic_filters(
            rows,
            q=q,
            tags=tags,
            difficulty_min=difficulty_min,
            difficulty_max=difficulty_max,
            free_only=free_only,
        ),
        sort,
    )
    total = len(filtered)
    page = filtered[offset : offset + limit]
    progress_map: dict[int, UserTopicProgress] = {}
    if user is not None and page:
        progress_rows = (
            db.execute(
                select(UserTopicProgress).where(
                    UserTopicProgress.user_id == user.id,
                    UserTopicProgress.topic_id.in_([topic.id for topic in page]),
                )
            )
            .scalars()
            .all()
        )
        progress_map = {row.topic_id: row for row in progress_rows}
    payload = {
        "items": [_serialize_topic(topic, user, progress_map.get(topic.id)) for topic in page],
        "total": total,
        "offset": offset,
        "limit": limit,
    }
    if user is None:
        await write_topics_cache(r, "list", cache_payload, payload)
    return TopicListResponse(**payload)


@router.get("/topics/{topic_id}", response_model=TopicOut)
def get_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    topic = db.get(Topic, topic_id)
    if topic is None or not topic.is_active:
        raise HTTPException(status_code=404, detail="Topic not found")
    progress = None
    if user is not None:
        progress = db.get(UserTopicProgress, {"user_id": user.id, "topic_id": topic.id})
    return TopicOut(**_serialize_topic(topic, user, progress))


@router.post("/topics/{topic_id}/start", response_model=TopicStartResponse)
async def start_topic(
    topic_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    r=Depends(redis_dep),
):
    topic = db.get(Topic, topic_id)
    if topic is None or not topic.is_active:
        raise HTTPException(status_code=404, detail="Topic not found")
    if topic.is_premium and not _is_pro_user(user):
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Тема доступна только в Pro")

    session_key = str(uuid.uuid4())
    conversation = create_conversation(db, user.id, topic.title, session_key)
    append_tutor_opening(db, conversation.id, user.id, topic.initial_prompt)

    topic.usage_count = int(topic.usage_count or 0) + 1
    progress = db.get(UserTopicProgress, {"user_id": user.id, "topic_id": topic.id})
    now = datetime.now(timezone.utc)
    if progress is None:
        progress = UserTopicProgress(
            user_id=user.id,
            topic_id=topic.id,
            completed=False,
            last_used=now,
            rating=None,
        )
        db.add(progress)
    else:
        progress.last_used = now
    db.commit()
    db.refresh(conversation)

    state = TutorState(topic=topic.title, history=[{"role": "assistant", "content": topic.initial_prompt.strip()}])
    await save_state(r, session_key, state)
    await invalidate_topics_cache(r)

    message_count = conversation_message_count(db, conversation.id)
    opening = topic.initial_prompt.strip()
    return TopicStartResponse(
        conversation_id=conversation.id,
        session_key=conversation.session_key,
        title=conversation.title,
        opening_message=opening,
        first_message=opening,
        started_at=conversation.started_at.isoformat(),
        last_updated_at=conversation.last_updated_at.isoformat(),
        message_count=message_count,
    )
