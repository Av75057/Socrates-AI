from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.config import get_settings
from app.limiter_instance import limiter
from app.routes import admin, auth, chat, gamification, pedagogy, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Socrates AI", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(chat.router, tags=["chat"])
app.include_router(gamification.router, prefix="/gamification", tags=["gamification"])
app.include_router(pedagogy.router, prefix="/pedagogy", tags=["pedagogy"])


@app.get("/health")
def health():
    return {"status": "ok"}
