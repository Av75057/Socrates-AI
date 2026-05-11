from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Skill, Topic, User, UserSkill
from app.services.adaptive_difficulty import (
    get_session_skill_id,
    get_skill_mastery,
    get_target_difficulty,
    update_skill_mastery,
)


class TestAdaptiveDifficulty(unittest.TestCase):
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

    def test_get_target_difficulty_uses_fixed_thresholds(self) -> None:
        self.assertEqual(get_target_difficulty(0.0), 1)
        self.assertEqual(get_target_difficulty(0.33), 1)
        self.assertEqual(get_target_difficulty(0.34), 2)
        self.assertEqual(get_target_difficulty(0.66), 2)
        self.assertEqual(get_target_difficulty(0.67), 3)
        self.assertEqual(get_target_difficulty(1.0), 3)

    def test_update_skill_mastery_smooths_toward_answer_score(self) -> None:
        with self.SessionLocal() as db:
            user = self._make_user(db)
            self._make_skill(db, "structure_argument")
            db.add(UserSkill(user_id=user.id, skill_id="structure_argument", level=30))
            db.commit()

            mastery = update_skill_mastery(db, user.id, "structure_argument", 1.0)

            self.assertAlmostEqual(mastery, 0.51, places=2)
            self.assertEqual(get_skill_mastery(db, user.id, "structure_argument"), 0.51)

    def test_update_skill_mastery_clamps_to_valid_range(self) -> None:
        with self.SessionLocal() as db:
            user = self._make_user(db)
            self._make_skill(db, "logical_consistency")
            db.add(UserSkill(user_id=user.id, skill_id="logical_consistency", level=100))
            db.commit()

            mastery = update_skill_mastery(db, user.id, "logical_consistency", -5.0)

            self.assertGreaterEqual(mastery, 0.0)
            self.assertLessEqual(mastery, 1.0)

    def test_get_session_skill_id_returns_first_learning_objective_skill(self) -> None:
        with self.SessionLocal() as db:
            topic = Topic(
                title="Тема",
                description="desc",
                initial_prompt="prompt",
                difficulty=2,
                tags=[],
                learning_objectives=[
                    {"title": "A", "skill_id": "ask_clarifying", "target_level": 50},
                    {"title": "B", "skill_id": "structure_argument", "target_level": 60},
                ],
                is_premium=False,
                created_by=self._make_user(db, email="author@example.com").id,
                is_active=True,
            )
            db.add(topic)
            db.flush()

            self.assertEqual(get_session_skill_id(topic), "ask_clarifying")

    def _make_user(self, db, email: str = "student@example.com") -> User:
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

    def _make_skill(self, db, skill_id: str) -> Skill:
        skill = Skill(skill_id=skill_id, name=skill_id, description=None, default_level=0)
        db.add(skill)
        db.flush()
        return skill


if __name__ == "__main__":
    unittest.main()
