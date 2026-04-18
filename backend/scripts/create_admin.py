#!/usr/bin/env python3
"""Создать пользователя с ролью admin. Пример:
  cd backend && .venv/bin/python scripts/create_admin.py admin@example.com SecretPass123 --name Админ
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import GamificationProgress, User, UserSettings
from app.db.session import SessionLocal


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("email")
    p.add_argument("password")
    p.add_argument("--name", default=None)
    args = p.parse_args()
    email = args.email.strip().lower()
    with SessionLocal() as db:
        if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
            print("Пользователь с таким email уже есть.", file=sys.stderr)
            sys.exit(1)
        u = User(
            email=email,
            hashed_password=hash_password(args.password),
            full_name=args.name,
            role="admin",
            is_active=True,
        )
        db.add(u)
        db.flush()
        db.add(
            UserSettings(
                user_id=u.id,
                tutor_mode="friendly",
                theme="dark",
                notifications_enabled=True,
            )
        )
        db.add(
            GamificationProgress(
                user_id=u.id,
                wisdom_points=0,
                level=1,
                achievements=[],
                streak_days=0,
                last_daily_challenge_date=None,
                extra_state=None,
            )
        )
        db.commit()
        print(f"Админ создан: id={u.id} email={u.email}")


if __name__ == "__main__":
    main()
