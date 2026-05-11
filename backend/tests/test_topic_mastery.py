from __future__ import annotations

import unittest
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps_auth import get_current_user, get_current_user_optional
from app.db.models import Base, Skill, Topic, User, UserSkill, UserTopicProgress
from app.db.session import get_db
from app.deps import redis_dep
from app.routes import topics as topics_routes
from app.services.learning_service import (
    recompute_topic_mastery_for_all_sync,
    recompute_topic_mastery_sync,
)


class TestTopicMastery(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_recompute_topic_mastery_sync_creates_goal_progress_from_skills(self) -> None:
        with self.SessionLocal() as db:
            user = self._make_user(db, email="student@example.com")
            topic = self._make_topic(
                db,
                learning_objectives=[
                    {"title": "Строит аргумент", "skill_id": "structure_argument", "target_level": 80},
                    {"title": "Ищет контрпример", "skill_id": "use_counterexample", "target_level": 40},
                ],
            )
            self._make_skill(db, "structure_argument")
            self._make_skill(db, "use_counterexample")
            db.add(UserSkill(user_id=user.id, skill_id="structure_argument", level=40))
            db.add(UserSkill(user_id=user.id, skill_id="use_counterexample", level=40))
            db.commit()

            recompute_topic_mastery_sync(db, user.id, topic.id)
            db.commit()

            progress = db.get(UserTopicProgress, {"user_id": user.id, "topic_id": topic.id})
            assert progress is not None
            self.assertEqual(progress.mastery_score, 75)
            self.assertFalse(progress.completed)
            self.assertEqual(len(progress.goals_state), 2)
            self.assertEqual(progress.goals_state[0]["progress_percent"], 50)
            self.assertTrue(progress.goals_state[1]["achieved"])
            self.assertIsNotNone(progress.last_assessed_at)

    def test_recompute_topic_mastery_for_all_sync_refreshes_existing_progress_rows(self) -> None:
        with self.SessionLocal() as db:
            first_user = self._make_user(db, email="first@example.com")
            second_user = self._make_user(db, email="second@example.com")
            topic = self._make_topic(
                db,
                learning_objectives=[
                    {"title": "Строит аргумент", "skill_id": "structure_argument", "target_level": 80},
                ],
            )
            self._make_skill(db, "structure_argument")
            db.add_all(
                [
                    UserSkill(user_id=first_user.id, skill_id="structure_argument", level=80),
                    UserSkill(user_id=second_user.id, skill_id="structure_argument", level=40),
                    UserTopicProgress(user_id=first_user.id, topic_id=topic.id, mastery_score=0, goals_state=[]),
                    UserTopicProgress(user_id=second_user.id, topic_id=topic.id, mastery_score=0, goals_state=[]),
                ]
            )
            db.commit()

            topic.learning_objectives = [
                {"title": "Строит аргумент", "skill_id": "structure_argument", "target_level": 40},
            ]
            recompute_topic_mastery_for_all_sync(db, topic.id)
            db.commit()

            first_progress = db.get(UserTopicProgress, {"user_id": first_user.id, "topic_id": topic.id})
            second_progress = db.get(UserTopicProgress, {"user_id": second_user.id, "topic_id": topic.id})
            assert first_progress is not None
            assert second_progress is not None
            self.assertEqual(first_progress.mastery_score, 100)
            self.assertTrue(first_progress.completed)
            self.assertEqual(second_progress.mastery_score, 100)
            self.assertTrue(second_progress.completed)

    def test_start_topic_endpoint_creates_progress_and_returns_mastery_payload(self) -> None:
        with self.SessionLocal() as db:
            user = self._make_user(db, email="starter@example.com")
            self._make_skill(db, "structure_argument")
            topic = self._make_topic(
                db,
                learning_objectives=[
                    {"title": "Строит аргумент", "skill_id": "structure_argument", "target_level": 60},
                ],
            )
            db.add(UserSkill(user_id=user.id, skill_id="structure_argument", level=30))
            db.commit()
            db.refresh(user)

            app = FastAPI()
            app.include_router(topics_routes.router)

            def override_get_db():
                test_db = self.SessionLocal()
                try:
                    yield test_db
                finally:
                    test_db.close()

            class _RedisStub:
                def __init__(self) -> None:
                    self.data: dict[str, str] = {}

                async def get(self, key: str) -> str | None:
                    return self.data.get(key)

                async def set(self, key: str, value: str) -> str:
                    self.data[key] = value
                    return "OK"

                async def delete(self, *keys: str) -> int:
                    removed = 0
                    for key in keys:
                        if key in self.data:
                            removed += 1
                            self.data.pop(key, None)
                    return removed

                async def scan_iter(self, match: str | None = None):
                    prefix = (match or "").rstrip("*")
                    for key in list(self.data.keys()):
                        if not prefix or key.startswith(prefix):
                            yield key

            redis = _RedisStub()

            app.dependency_overrides[get_db] = override_get_db
            app.dependency_overrides[redis_dep] = lambda: redis
            app.dependency_overrides[get_current_user] = lambda: user
            app.dependency_overrides[get_current_user_optional] = lambda: user

            with TestClient(app) as client:
                start_response = client.post(f"/topics/{topic.id}/start")
                self.assertEqual(start_response.status_code, 200, start_response.text)
                start_payload = start_response.json()
                self.assertEqual(start_payload["message_count"], 1)
                self.assertTrue(start_payload["session_key"])

                topic_response = client.get(f"/topics/{topic.id}")
                self.assertEqual(topic_response.status_code, 200, topic_response.text)
                topic_payload = topic_response.json()

            progress = topic_payload["progress"]
            self.assertIsNotNone(progress)
            self.assertEqual(progress["mastery_score"], 50)
            self.assertEqual(len(progress["goals_state"]), 1)
            self.assertEqual(progress["goals_state"][0]["current_level"], 30)
            self.assertEqual(progress["goals_state"][0]["progress_percent"], 50)
            self.assertFalse(progress["completed"])

    def _make_user(self, db: Session, *, email: str) -> User:
        user = User(
            email=email,
            hashed_password="x",
            role="user",
            subscription_plan="free",
            subscription_status="active",
            is_active=True,
        )
        db.add(user)
        db.flush()
        return user

    def _make_skill(self, db: Session, skill_id: str) -> Skill:
        skill = Skill(skill_id=skill_id, name=skill_id, description=None, default_level=0)
        db.add(skill)
        db.flush()
        return skill

    def _make_topic(self, db: Session, *, learning_objectives: list[dict[str, object]]) -> Topic:
        topic = Topic(
            title="Логика",
            description="Проверка mastery",
            initial_prompt="Начнем с тезиса.",
            difficulty=2,
            tags=["logic"],
            learning_objectives=learning_objectives,
            is_premium=False,
            created_by=self._make_user(db, email=f"author-{datetime.now(timezone.utc).timestamp()}@example.com").id,
            is_active=True,
        )
        db.add(topic)
        db.flush()
        return topic


if __name__ == "__main__":
    unittest.main()
