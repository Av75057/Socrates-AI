from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps_auth import get_current_user_optional
from app.db.models import User
from app.deps import redis_dep
from app.dto.meta_training import (
    MetaTrainingEndRequest,
    MetaTrainingMessageRequest,
    MetaTrainingResponse,
    MetaTrainingStartRequest,
)
from app.services.meta_training_service import MetaTrainingService

router = APIRouter(prefix="/api/v1/meta-training", tags=["meta-training"])
service = MetaTrainingService()


@router.post("/start", response_model=MetaTrainingResponse)
async def start_meta_training(
    body: MetaTrainingStartRequest,
    redis=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    return await service.start(redis, body.session_id, db_user, body.preferred_topic)


@router.post("/message", response_model=MetaTrainingResponse)
async def message_meta_training(
    body: MetaTrainingMessageRequest,
    redis=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    return await service.message(redis, body.session_id, db_user, body.message, body.action, body.frame_name)


@router.get("/status/{session_id}", response_model=MetaTrainingResponse)
async def status_meta_training_by_id(
    session_id: str,
    redis=Depends(redis_dep),
):
    return await service.status(redis, session_id)


@router.get("/status", response_model=MetaTrainingResponse)
async def status_meta_training_legacy(
    session_id: str,
    redis=Depends(redis_dep),
):
    return await service.status(redis, session_id)


@router.post("/end", response_model=MetaTrainingResponse)
async def end_meta_training(
    body: MetaTrainingEndRequest,
    redis=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    return await service.end(redis, body.session_id, db_user, body.summary, body.confidence_label)
