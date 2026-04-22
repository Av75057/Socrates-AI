from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_user
from app.config import get_settings
from app.db.models import (
    Assignment,
    ClassStudent,
    Classroom,
    Conversation,
    Message,
    PublicConversation,
    User,
    UserSettings,
)
from app.db.session import get_db
from app.deps import redis_dep
from app.services.memory_store import load_memory
from app.services.conversation_db import (
    append_tutor_opening,
    conversation_message_count,
    create_conversation,
    delete_user_message_and_following,
    display_title_for_conversation,
    fallacy_summary_for_user,
    update_user_message_content,
)
from app.services.conversation_opening import generate_conversation_opening_message
from app.services.db_gamification import ensure_gamification_row, gamification_row_to_public
from app.services.learning_service import (
    get_recommendation,
    get_user_pedagogy_public,
    get_user_skills_summary,
    reset_user_learning,
)
from app.services.public_share_service import make_share_slug

router = APIRouter(prefix="/users", tags=["users"])
log = logging.getLogger(__name__)


def _share_frontend_base() -> str:
    s = get_settings()
    u = (s.public_site_url or "").strip().rstrip("/")
    return u or "http://localhost:5173"


def _avatar_url(path: str | None) -> str | None:
    if not path:
        return None
    s = get_settings()
    rel = f"/{path.lstrip('/')}"
    base = (s.public_api_url or "").strip().rstrip("/")
    return f"{base}{rel}" if base else rel


def _profile_out(user: User) -> ProfileOut:
    return ProfileOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=_avatar_url(user.avatar_path),
        role=user.role,
        is_active=user.is_active,
    )


def _normalize_llm_base_url(url: str | None) -> str | None:
    if url is None:
        return None
    s = url.strip()
    if not s:
        return ""
    if not (s.startswith("http://") or s.startswith("https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="llm_base_url должен начинаться с http:// или https://",
        )
    return s


def _settings_to_out(s: UserSettings) -> SettingsOut:
    key_set = bool((s.llm_api_key or "").strip())
    return SettingsOut(
        tutor_mode=s.tutor_mode,
        theme=s.theme,
        notifications_enabled=s.notifications_enabled,
        has_seen_onboarding=bool(s.has_seen_onboarding),
        show_typing_indicator=bool(s.show_typing_indicator),
        russian_only=bool(s.russian_only),
        llm_base_url=(s.llm_base_url or "").strip() or None,
        llm_model_name=(s.llm_model_name or "").strip() or None,
        llm_api_key_set=key_set,
    )


def _normalize_fallacy_detected(raw: Any) -> dict[str, Any] | None:
    """SQLite/драйверы могут отдать JSON строкой; Pydantic ждёт dict | None."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


class ProfileOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    avatar_url: str | None = None
    role: str
    is_active: bool


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)


class SettingsOut(BaseModel):
    tutor_mode: str
    theme: str | None
    notifications_enabled: bool
    has_seen_onboarding: bool
    show_typing_indicator: bool
    russian_only: bool = True
    llm_base_url: str | None = None
    llm_model_name: str | None = None
    llm_api_key_set: bool = False


class SettingsUpdate(BaseModel):
    tutor_mode: str | None = None
    theme: str | None = None
    notifications_enabled: bool | None = None
    has_seen_onboarding: bool | None = None
    show_typing_indicator: bool | None = None
    russian_only: bool | None = None
    llm_base_url: str | None = None
    llm_model_name: str | None = None
    llm_api_key: str | None = None  # None = не менять; "" = очистить


class TestLLMConnectionBody(BaseModel):
    llm_base_url: str = Field(..., min_length=8, max_length=512)
    llm_api_key: str | None = Field(None, max_length=4096)
    llm_model_name: str | None = Field(None, max_length=256)

    @field_validator("llm_base_url")
    @classmethod
    def _url_scheme(cls, v: str) -> str:
        s = (v or "").strip()
        if not (s.startswith("http://") or s.startswith("https://")):
            raise ValueError("URL должен начинаться с http:// или https://")
        return s


class TestLLMConnectionOut(BaseModel):
    ok: bool
    message: str
    model_ids: list[str] = Field(default_factory=list)


class MessageContentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=65535)


class ConversationCreate(BaseModel):
    title: str | None = Field(None, max_length=512)


class ConversationSummary(BaseModel):
    id: int
    title: str
    started_at: str
    last_updated_at: str
    message_count: int
    session_key: str
    opening_message: str | None = None
    public_slug: str | None = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    fallacy_detected: dict[str, Any] | None
    created_at: str


class ConversationDetail(BaseModel):
    id: int
    title: str
    started_at: str
    last_updated_at: str
    session_key: str
    messages: list[MessageOut]
    public_slug: str | None = None


class EducatorLinkOut(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    class_name: str


class StudentAssignmentOut(BaseModel):
    id: int
    class_id: int
    class_name: str
    educator_name: str
    title: str
    prompt: str
    due_date: str | None = None
    created_at: str


class PublishConversationOut(BaseModel):
    slug: str
    share_url: str
    preview_card_url: str


class AvatarUploadOut(BaseModel):
    avatar_url: str


class SubscriptionOut(BaseModel):
    plan: str
    status: str
    is_pro: bool
    current_period_end: str | None = None


@router.get("/me/memory-profile")
async def get_memory_profile_me(
    user: User = Depends(get_current_user),
    r=Depends(redis_dep),
):
    """
    Долговременная память тьютора из Redis (тот же ключ, что и в /chat для аккаунта).
    Нужна UI при смене диалога без нового сообщения — иначе панель «Память тьютора» остаётся пустой/устаревшей.
    """
    memory = await load_memory(r, str(user.id))
    ut = memory.user_type if memory.user_type in ("lazy", "anxious", "thinker") else "lazy"
    out = memory.to_dict()
    out["user_type"] = ut
    return out


@router.get("/me/educators", response_model=list[EducatorLinkOut])
def get_my_educators(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.execute(
            select(Classroom, User)
            .join(ClassStudent, ClassStudent.class_id == Classroom.id)
            .join(User, User.id == Classroom.educator_id)
            .where(ClassStudent.student_id == user.id)
            .order_by(Classroom.name.asc())
        )
        .all()
    )
    return [
        EducatorLinkOut(
            id=educator.id,
            email=educator.email,
            full_name=educator.full_name,
            class_name=classroom.name,
        )
        for classroom, educator in rows
    ]


@router.get("/me/assignments", response_model=list[StudentAssignmentOut])
def get_my_assignments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.execute(
            select(Assignment, Classroom, User)
            .join(Classroom, Classroom.id == Assignment.class_id)
            .join(User, User.id == Classroom.educator_id)
            .join(ClassStudent, ClassStudent.class_id == Classroom.id)
            .where(
                ClassStudent.student_id == user.id,
                (Assignment.due_date.is_(None)) | (Assignment.due_date >= func.now()),
            )
            .order_by(Assignment.created_at.desc())
        )
        .all()
    )
    return [
        StudentAssignmentOut(
            id=assignment.id,
            class_id=classroom.id,
            class_name=classroom.name,
            educator_name=educator.full_name or educator.email,
            title=assignment.title,
            prompt=assignment.prompt,
            due_date=assignment.due_date.isoformat() if assignment.due_date else None,
            created_at=assignment.created_at.isoformat(),
        )
        for assignment, classroom, educator in rows
    ]


@router.get("/me/assignments/{assignment_id}", response_model=StudentAssignmentOut)
def get_my_assignment(
    assignment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.execute(
            select(Assignment, Classroom, User)
            .join(Classroom, Classroom.id == Assignment.class_id)
            .join(User, User.id == Classroom.educator_id)
            .join(ClassStudent, ClassStudent.class_id == Classroom.id)
            .where(
                Assignment.id == assignment_id,
                ClassStudent.student_id == user.id,
            )
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment, classroom, educator = row
    return StudentAssignmentOut(
        id=assignment.id,
        class_id=classroom.id,
        class_name=classroom.name,
        educator_name=educator.full_name or educator.email,
        title=assignment.title,
        prompt=assignment.prompt,
        due_date=assignment.due_date.isoformat() if assignment.due_date else None,
        created_at=assignment.created_at.isoformat(),
    )


@router.get("/me", response_model=ProfileOut)
def get_me(user: User = Depends(get_current_user)):
    return _profile_out(user)


@router.put("/me", response_model=ProfileOut)
def update_me(body: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.full_name is not None:
        user.full_name = body.full_name
    db.commit()
    db.refresh(user)
    return _profile_out(user)


@router.post("/me/avatar", response_model=AvatarUploadOut)
async def upload_my_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content_type = (file.content_type or "").lower()
    ext_by_type = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    ext = ext_by_type.get(content_type)
    if ext is None:
        raise HTTPException(status_code=400, detail="Поддерживаются только JPG, PNG, WEBP и GIF")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Файл пустой")
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Максимальный размер файла — 5 MB")

    uploads_root = Path(get_settings().uploads_dir).resolve()
    avatar_dir = uploads_root / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"user-{user.id}-{uuid.uuid4().hex}{ext}"
    dest = avatar_dir / filename
    dest.write_bytes(data)

    if user.avatar_path:
        old_abs = uploads_root / "avatars" / Path(user.avatar_path).name
        if old_abs.exists():
            try:
                old_abs.unlink()
            except OSError:
                log.warning("Could not delete previous avatar for user_id=%s path=%s", user.id, old_abs)

    user.avatar_path = f"uploads/avatars/{filename}"
    db.commit()
    db.refresh(user)
    return AvatarUploadOut(avatar_url=_avatar_url(user.avatar_path) or "")


@router.delete("/me/avatar", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_avatar(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.avatar_path:
        uploads_root = Path(get_settings().uploads_dir).resolve()
        try:
            old_abs = uploads_root / "avatars" / Path(user.avatar_path).name
            if old_abs.exists():
                old_abs.unlink()
        except OSError:
            log.warning("Could not remove avatar for user_id=%s path=%s", user.id, user.avatar_path)
    user.avatar_path = None
    db.commit()


@router.get("/me/subscription", response_model=SubscriptionOut)
def get_my_subscription(user: User = Depends(get_current_user)):
    plan = (user.subscription_plan or "free").strip().lower() or "free"
    status_value = (user.subscription_status or "active").strip().lower() or "active"
    return SubscriptionOut(
        plan=plan,
        status=status_value,
        is_pro=plan in {"pro", "yearly", "team"},
        current_period_end=user.subscription_current_period_end.isoformat()
        if user.subscription_current_period_end
        else None,
    )


def _settings_for_user(db: Session, user_id: int) -> UserSettings | None:
    return db.execute(select(UserSettings).where(UserSettings.user_id == user_id)).scalar_one_or_none()


@router.get("/me/settings", response_model=SettingsOut)
def get_settings_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = _settings_for_user(db, user.id)
    if s is None:
        s = UserSettings(
            user_id=user.id,
            tutor_mode="friendly",
            theme="dark",
            notifications_enabled=True,
            has_seen_onboarding=False,
            show_typing_indicator=True,
            russian_only=True,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
    return _settings_to_out(s)


@router.put("/me/settings", response_model=SettingsOut)
def update_settings_me(
    body: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = _settings_for_user(db, user.id)
    if s is None:
        s = UserSettings(
            user_id=user.id,
            tutor_mode="friendly",
            theme="dark",
            notifications_enabled=True,
            has_seen_onboarding=False,
            show_typing_indicator=True,
            russian_only=True,
        )
        db.add(s)
        db.flush()
    if body.tutor_mode is not None:
        if body.tutor_mode not in ("strict", "friendly", "provocateur"):
            raise HTTPException(status_code=400, detail="Invalid tutor_mode")
        s.tutor_mode = body.tutor_mode
    if body.theme is not None:
        if body.theme not in ("light", "dark"):
            raise HTTPException(status_code=400, detail="Invalid theme")
        s.theme = body.theme
    if body.notifications_enabled is not None:
        s.notifications_enabled = body.notifications_enabled
    if body.has_seen_onboarding is not None:
        s.has_seen_onboarding = body.has_seen_onboarding
    if body.show_typing_indicator is not None:
        s.show_typing_indicator = body.show_typing_indicator
    if body.russian_only is not None:
        s.russian_only = body.russian_only
    if body.llm_base_url is not None:
        n = _normalize_llm_base_url(body.llm_base_url)
        s.llm_base_url = n if n else None
    if body.llm_model_name is not None:
        m = (body.llm_model_name or "").strip()
        s.llm_model_name = m if m else None
    if body.llm_api_key is not None:
        k = (body.llm_api_key or "").strip()
        s.llm_api_key = k if k else None
    db.commit()
    db.refresh(s)
    return _settings_to_out(s)


@router.post("/me/settings/test-llm", response_model=TestLLMConnectionOut)
async def test_llm_connection(
    body: TestLLMConnectionBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base = body.llm_base_url.rstrip("/")
    models_url = f"{base}/models"
    key = (body.llm_api_key or "").strip()
    if not key:
        s_row = _settings_for_user(db, user.id)
        if s_row and (s_row.llm_api_key or "").strip():
            key = s_row.llm_api_key.strip()
        else:
            key = "sk-no-key-required"
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(models_url, headers=headers)
    except httpx.RequestError as e:
        return TestLLMConnectionOut(
            ok=False,
            message=f"Сервер недоступен: {e!s}. Проверь URL, firewall и CORS на стороне LLM.",
            model_ids=[],
        )
    if r.status_code != 200:
        t = (r.text or "")[:300]
        return TestLLMConnectionOut(
            ok=False,
            message=f"HTTP {r.status_code}: {t}",
            model_ids=[],
        )
    try:
        data = r.json()
    except Exception:
        return TestLLMConnectionOut(ok=False, message="Ответ не JSON (ожидался список моделей).", model_ids=[])
    ids: list[str] = []
    for item in data.get("data") or []:
        if isinstance(item, dict) and item.get("id"):
            ids.append(str(item["id"]))
    msg = "Успешно подключено"
    want = (body.llm_model_name or "").strip()
    if want and ids and want not in ids:
        msg = f"Соединение есть, но модели «{want}» нет в списке. Доступные: {', '.join(ids[:8])}{'…' if len(ids) > 8 else ''}"
    return TestLLMConnectionOut(ok=True, message=msg, model_ids=ids[:80])


@router.post("/me/conversations", response_model=ConversationSummary)
async def create_conversation_me(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_key = str(uuid.uuid4())
    c = create_conversation(db, user.id, body.title, session_key)
    opening: str | None = None
    try:
        raw = await generate_conversation_opening_message(user.id, c.title)
        if raw:
            append_tutor_opening(db, c.id, user.id, raw)
            opening = raw
    except Exception:
        log.exception("conversation opening failed user_id=%s conv_id=%s", user.id, c.id)
    db.refresh(c)
    mc = conversation_message_count(db, c.id)
    return ConversationSummary(
        id=c.id,
        title=c.title,
        started_at=c.started_at.isoformat(),
        last_updated_at=c.last_updated_at.isoformat(),
        message_count=mc,
        session_key=c.session_key,
        opening_message=opening,
        public_slug=None,
    )


@router.get("/me/conversations", response_model=list[ConversationSummary])
def list_conversations_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    rows = (
        db.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.last_updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    ids = [c.id for c in rows]
    slug_by: dict[int, str] = {}
    if ids:
        pubs = (
            db.execute(
                select(PublicConversation).where(
                    PublicConversation.conversation_id.in_(ids),
                    PublicConversation.is_active.is_(True),
                )
            )
            .scalars()
            .all()
        )
        slug_by = {p.conversation_id: p.slug for p in pubs}

    out: list[ConversationSummary] = []
    for c in rows:
        out.append(
            ConversationSummary(
                id=c.id,
                title=display_title_for_conversation(db, c),
                started_at=c.started_at.isoformat(),
                last_updated_at=c.last_updated_at.isoformat(),
                message_count=conversation_message_count(db, c.id),
                session_key=c.session_key,
                public_slug=slug_by.get(c.id),
            )
        )
    return out


@router.get("/me/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation_me(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.get(Conversation, conversation_id)
    if c is None or c.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    msgs = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == c.id)
            .order_by(Message.created_at.asc())
        )
        .scalars()
        .all()
    )
    pub_slug = db.execute(
        select(PublicConversation.slug).where(
            PublicConversation.conversation_id == c.id,
            PublicConversation.is_active.is_(True),
        )
    ).scalar_one_or_none()

    return ConversationDetail(
        id=c.id,
        title=display_title_for_conversation(db, c),
        started_at=c.started_at.isoformat(),
        last_updated_at=c.last_updated_at.isoformat(),
        session_key=c.session_key,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                fallacy_detected=_normalize_fallacy_detected(m.fallacy_detected),
                created_at=m.created_at.isoformat(),
            )
            for m in msgs
        ],
        public_slug=pub_slug,
    )


@router.post("/me/conversations/{conversation_id}/publish", response_model=PublishConversationOut)
def publish_conversation_me(
    conversation_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.get(Conversation, conversation_id)
    if c is None or c.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    title = (display_title_for_conversation(db, c) or "Диалог")[:512]
    existing = db.execute(
        select(PublicConversation).where(PublicConversation.conversation_id == c.id)
    ).scalar_one_or_none()
    api_base = str(request.base_url).rstrip("/")
    front = _share_frontend_base()

    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.title = title
            db.commit()
            db.refresh(existing)
        slug = existing.slug
    else:
        slug = ""
        for _ in range(16):
            cand = make_share_slug()
            if db.get(PublicConversation, cand) is None:
                slug = cand
                break
        if not slug:
            raise HTTPException(status_code=500, detail="Could not allocate slug")
        pub = PublicConversation(
            slug=slug,
            user_id=user.id,
            conversation_id=c.id,
            title=title,
            views=0,
            is_active=True,
        )
        db.add(pub)
        db.commit()

    return PublishConversationOut(
        slug=slug,
        share_url=f"{front}/share/{slug}",
        preview_card_url=f"{api_base}/public/share/{slug}/card",
    )


@router.delete("/me/conversations/{conversation_id}/unpublish", status_code=status.HTTP_204_NO_CONTENT)
def unpublish_conversation_me(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.execute(
        select(PublicConversation).where(
            PublicConversation.conversation_id == conversation_id,
            PublicConversation.user_id == user.id,
        )
    ).scalar_one_or_none()
    if row:
        db.delete(row)
        db.commit()
    return None


@router.put("/me/messages/{message_id}", response_model=MessageOut)
def update_message_me(
    message_id: int,
    body: MessageContentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok = update_user_message_content(db, user.id, message_id, body.content)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found or not editable")
    m = db.get(Message, message_id)
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return MessageOut(
        id=m.id,
        role=m.role,
        content=m.content,
        fallacy_detected=_normalize_fallacy_detected(m.fallacy_detected),
        created_at=m.created_at.isoformat(),
    )


@router.delete("/me/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message_me(
    message_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = delete_user_message_and_following(db, user.id, message_id)
    if n == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found or not deletable")
    return None


@router.delete("/me/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation_me(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.get(Conversation, conversation_id)
    if c is None or c.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    db.delete(c)
    db.commit()
    return None


@router.get("/me/gamification")
def get_gamification_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = ensure_gamification_row(db, user.id)
    return gamification_row_to_public(row)


def _dialog_statistics(db: Session, user_id: int) -> dict[str, Any]:
    n_conv = db.scalar(select(func.count()).select_from(Conversation).where(Conversation.user_id == user_id)) or 0
    n_msg = (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
        )
        or 0
    )
    n_user_msgs = (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id, Message.role == "user")
        )
        or 0
    )
    avg_len = 0.0
    if n_user_msgs:
        total = db.scalar(
            select(func.sum(func.length(Message.content)))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id, Message.role == "user")
        )
        if total:
            avg_len = round(float(total) / n_user_msgs, 2)
    return {
        "conversations_total": n_conv,
        "messages_total": n_msg,
        "user_messages_total": n_user_msgs,
        "avg_user_message_length": avg_len,
        "common_fallacies": fallacy_summary_for_user(db, user_id, limit=10),
    }


@router.get("/me/statistics")
def get_statistics_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _dialog_statistics(db, user.id)


@router.get("/me/skills")
def get_skills_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_skills_summary(db, user.id)


@router.get("/me/pedagogy")
def get_pedagogy_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_pedagogy_public(db, user.id)


@router.get("/me/progress")
def get_progress_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "skills": get_user_skills_summary(db, user.id),
        "pedagogy": get_user_pedagogy_public(db, user.id),
        "dialog_statistics": _dialog_statistics(db, user.id),
    }


@router.get("/me/recommendation")
def get_recommendation_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_recommendation(db, user.id)


@router.post("/me/reset_progress", status_code=status.HTTP_204_NO_CONTENT)
def reset_progress_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reset_user_learning(db, user.id)
    return None
