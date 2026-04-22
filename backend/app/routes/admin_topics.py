from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_educator
from app.db.models import Topic, User
from app.db.session import get_db
from app.deps import redis_dep
from app.routes.topics import TopicListResponse, TopicOut
from app.services.topic_cache import invalidate_topics_cache
from app.services.topic_generator import generate_topic_draft

router = APIRouter(prefix="/admin", tags=["admin-topics"])


class TopicUpsertBody(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = Field(None, max_length=512)
    initial_prompt: str = Field(..., min_length=3, max_length=8000)
    difficulty: int = Field(2, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    is_premium: bool = False
    is_active: bool = True


class TopicGenerateBody(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=255)


class TopicGenerateResponse(TopicUpsertBody):
    model: str


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
    return out[:8]


def _serialize_topic(topic: Topic) -> dict[str, Any]:
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
        "can_start": True,
        "progress": None,
    }


@router.get("/topics", response_model=TopicListResponse)
def admin_list_topics(
    _: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
    q: str = Query("", max_length=120),
    include_inactive: bool = Query(True),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    rows = db.execute(select(Topic)).scalars().all()
    items: list[Topic] = []
    search = q.strip().lower()
    for topic in rows:
        if not include_inactive and not topic.is_active:
            continue
        if search:
            hay = " ".join(
                [
                    str(topic.title or ""),
                    str(topic.description or ""),
                    " ".join(_normalize_tags(topic.tags)),
                ]
            ).lower()
            if search not in hay:
                continue
        items.append(topic)
    items.sort(key=lambda item: item.created_at, reverse=True)
    total = len(items)
    page = items[offset : offset + limit]
    return TopicListResponse(
        items=[TopicOut(**_serialize_topic(topic)) for topic in page],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/topics", response_model=TopicOut)
async def admin_create_topic(
    body: TopicUpsertBody,
    user: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
    r=Depends(redis_dep),
):
    topic = Topic(
        title=body.title.strip(),
        description=(body.description or "").strip() or None,
        initial_prompt=body.initial_prompt.strip(),
        difficulty=body.difficulty,
        tags=_normalize_tags(body.tags),
        is_premium=body.is_premium,
        is_active=body.is_active,
        created_by=user.id,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    await invalidate_topics_cache(r)
    return TopicOut(**_serialize_topic(topic))


@router.put("/topics/{topic_id}", response_model=TopicOut)
async def admin_update_topic(
    topic_id: int,
    body: TopicUpsertBody,
    _: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
    r=Depends(redis_dep),
):
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic.title = body.title.strip()
    topic.description = (body.description or "").strip() or None
    topic.initial_prompt = body.initial_prompt.strip()
    topic.difficulty = body.difficulty
    topic.tags = _normalize_tags(body.tags)
    topic.is_premium = body.is_premium
    topic.is_active = body.is_active
    db.commit()
    db.refresh(topic)
    await invalidate_topics_cache(r)
    return TopicOut(**_serialize_topic(topic))


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_topic(
    topic_id: int,
    _: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
    r=Depends(redis_dep),
):
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic.is_active = False
    db.commit()
    await invalidate_topics_cache(r)
    return None


@router.post("/topics/generate", response_model=TopicGenerateResponse)
async def admin_generate_topic(
    body: TopicGenerateBody,
    _: User = Depends(get_current_educator),
):
    draft = await generate_topic_draft(body.prompt)
    return TopicGenerateResponse(
        title=str(draft.get("title") or body.prompt).strip(),
        description=str(draft.get("description") or "").strip() or None,
        initial_prompt=str(draft.get("initial_prompt") or "").strip(),
        difficulty=int(draft.get("difficulty") or 2),
        tags=_normalize_tags(draft.get("tags")),
        is_premium=False,
        is_active=True,
        model=str(draft.get("model") or ""),
    )
