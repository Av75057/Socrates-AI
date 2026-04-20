#!/usr/bin/env python3
"""Создать пользователя с ролью admin или повысить существующего.

Создание (email свободен):
  cd backend && .venv/bin/python scripts/create_admin.py admin@example.com SecretPass123 --name Админ

Повысить уже зарегистрированного пользователя до admin:
  cd backend && .venv/bin/python scripts/create_admin.py --promote user@example.com

Сменить пароль при повышении:
  cd backend && .venv/bin/python scripts/create_admin.py --promote user@example.com NewSecretPass123
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
    p = argparse.ArgumentParser(description="Создать admin или выдать роль admin существующему пользователю.")
    p.add_argument("--promote", action="store_true", help="Повысить существующего пользователя (иначе — только создание нового)")
    p.add_argument("email")
    p.add_argument("password", nargs="?", default=None, help="Пароль: обязателен при создании; при --promote — опционально сменить пароль")
    p.add_argument("--name", default=None)
    args = p.parse_args()
    email = args.email.strip().lower()

    with SessionLocal() as db:
        existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

        if args.promote:
            if existing is None:
                print(f"Пользователь {email!r} не найден. Сначала зарегистрируйтесь или создайте запись без --promote.", file=sys.stderr)
                sys.exit(1)
            existing.role = "admin"
            if args.password:
                existing.hashed_password = hash_password(args.password)
            if args.name is not None:
                existing.full_name = args.name
            db.commit()
            print(f"Роль admin выдана: id={existing.id} email={existing.email}")
            print("Выйдите из аккаунта в браузере и войдите снова (или обновите страницу), чтобы фронт подтянул роль.")
            return

        if existing is not None:
            print(
                "Пользователь с таким email уже есть. Чтобы выдать роль admin: "
                f".venv/bin/python scripts/create_admin.py --promote {email}",
                file=sys.stderr,
            )
            sys.exit(1)
        if not args.password:
            print("Укажите пароль для нового пользователя.", file=sys.stderr)
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
                has_seen_onboarding=False,
                show_typing_indicator=True,
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
