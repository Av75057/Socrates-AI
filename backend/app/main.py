from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.config import get_settings
from app.limiter_instance import limiter
from app.routes import admin, auth, chat, educator, gamification, pedagogy, public_sharing, users

log = logging.getLogger(__name__)


def _run_alembic_upgrade_if_sqlite() -> None:
    """Локальная SQLite без прогнанных миграций ломает /chat (user_pedagogy и др.)."""
    s = get_settings()
    if not (s.database_url or "").strip().lower().startswith("sqlite"):
        return
    try:
        ini = Path(__file__).resolve().parents[1] / "alembic.ini"
        cfg = Config(str(ini))
        command.upgrade(cfg, "head")
    except Exception:
        log.exception("Не удалось выполнить alembic upgrade при старте (проверьте БД вручную)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_alembic_upgrade_if_sqlite()
    yield


app = FastAPI(title="Socrates AI", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
# Dev: фронт с телефона/другого ПК по LAN (Vite на :5173+ или preview :4173+; Tailscale 100.x).
_lan_dev_regex = (
    r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    r":(5173|5174|5175|5176|4173|4174|4175)$"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_origin_regex=_lan_dev_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(public_sharing.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(educator.router)
app.include_router(chat.router, tags=["chat"])
app.include_router(gamification.router, prefix="/gamification", tags=["gamification"])
app.include_router(pedagogy.router, prefix="/pedagogy", tags=["pedagogy"])


@app.get("/health")
def health():
    return {"status": "ok"}
