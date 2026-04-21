"""Публичный просмотр диалогов, OG-карточка и превью-картинка (без авторизации)."""

from __future__ import annotations

import html
import io
import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Conversation, Message, PublicConversation
from app.db.session import get_db
from app.services.conversation_db import display_title_for_conversation
from app.services.public_share_service import anonymize_public_text

log = logging.getLogger(__name__)

router = APIRouter(tags=["public"])


def _frontend_base() -> str:
    s = get_settings()
    u = (s.public_site_url or "").strip().rstrip("/")
    if u:
        return u
    return "http://localhost:5173"


def _api_base(request: Request) -> str:
    return str(request.base_url).rstrip("/")


class PublicMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class PublicSharePayload(BaseModel):
    slug: str
    title: str
    views: int
    author_label: str = "Ученик"
    messages: list[PublicMessageOut]
    share_url: str
    preview_card_url: str


def _get_active_share(db: Session, slug: str) -> PublicConversation | None:
    row = db.get(PublicConversation, slug)
    if row is None or not row.is_active:
        return None
    return row


def _wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    cur: list[str] = []
    n = 0
    for w in words:
        add = len(w) if not cur else len(w) + 1
        if n + add <= width:
            cur.append(w)
            n += add
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
            n = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines[:6]


@router.get("/public/share/{slug}", response_model=PublicSharePayload)
@router.get("/public/share/{slug}/raw", response_model=PublicSharePayload)
def get_public_share(slug: str, request: Request, db: Session = Depends(get_db)) -> PublicSharePayload:
    row = _get_active_share(db, slug)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")

    msgs = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == row.conversation_id)
            .order_by(Message.created_at.asc())
        )
        .scalars()
        .all()
    )

    row.views = (row.views or 0) + 1
    db.add(row)
    db.commit()
    db.refresh(row)

    front = _frontend_base()
    share_url = f"{front}/share/{row.slug}"
    preview_card_url = f"{_api_base(request)}/public/share/{quote(slug, safe='')}/card"

    title_plain = row.title or "Диалог"
    return PublicSharePayload(
        slug=row.slug,
        title=title_plain,
        views=row.views,
        messages=[
            PublicMessageOut(
                id=m.id,
                role="user" if m.role == "user" else "assistant",
                content=anonymize_public_text(m.content),
                created_at=m.created_at.isoformat(),
            )
            for m in msgs
        ],
        share_url=share_url,
        preview_card_url=preview_card_url,
    )


@router.get("/public/share/{slug}/card", response_class=HTMLResponse)
def public_share_og_card(slug: str, request: Request, db: Session = Depends(get_db)):
    row = _get_active_share(db, slug)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    title = html.escape(row.title or "Диалог в Socrates AI")
    desc = "Смотри, как Socrates-AI помогает мыслить глубже — диалог без личных данных."
    front = _frontend_base()
    spa_url = f"{front}/share/{row.slug}"
    abs_img = f"{_api_base(request)}/public/share/{quote(slug, safe='')}/og.png"
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{html.escape(desc)}" />
<meta property="og:image" content="{html.escape(abs_img)}" />
<meta property="og:type" content="article" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<meta name="twitter:description" content="{html.escape(desc)}" />
<meta name="twitter:image" content="{html.escape(abs_img)}" />
<meta http-equiv="refresh" content="0;url={html.escape(spa_url)}" />
<link rel="canonical" href="{html.escape(spa_url)}" />
</head>
<body>
<p><a href="{html.escape(spa_url)}">Открыть диалог в Socrates AI</a></p>
</body>
</html>"""
    )


@router.get("/public/share/{slug}/og.png")
def public_share_og_image(slug: str, db: Session = Depends(get_db)):
    row = _get_active_share(db, slug)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    title = row.title or "Диалог"
    try:
        from PIL import Image, ImageDraw, ImageFont

        w, h = 1200, 630
        img = Image.new("RGB", (w, h), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)
        for i in range(h):
            g = int(15 + (28 - 15) * (i / h))
            draw.line([(0, i), (w, i)], fill=(g, min(60, g + 15), min(80, g + 35)))

        try:
            font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
            font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
        except OSError:
            font_lg = font_md = font_sm = ImageFont.load_default()

        draw.text((72, 100), "Socrates AI", fill=(251, 191, 36), font=font_md)
        t = title if len(title) < 90 else title[:87] + "…"
        y = 200
        for line in _wrap_text(t, 38):
            draw.text((72, y), line, fill=(248, 250, 252), font=font_lg)
            y += 56
            if y > 500:
                break
        draw.text((72, 560), "Учись мыслить глубже", fill=(148, 163, 184), font=font_sm)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception:
        log.exception("og.png failed slug=%s", slug)
        raise HTTPException(status_code=500, detail="Preview unavailable") from None


