"""Дерево навыков: шаблон + прогресс пользователя (связь с памятью тем)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.models.user_memory import UserMemory

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def track_key_for_topic(topic: str) -> str:
    """Выбор трека по теме: математика vs физика (и др.)."""
    t = (topic or "").strip().lower()
    math_markers = (
        "математ",
        "алгебр",
        "геометр",
        "уравнен",
        "логарифм",
        "производн",
        "интеграл",
        "тригонометр",
        "процент",
        "дроб",
        "функц",
        "график",
        "многочлен",
        "арифметик",
    )
    if any(m in t for m in math_markers):
        return "math"
    return "physics"


@lru_cache(maxsize=4)
def _load_track(track_key: str) -> dict:
    files = {
        "physics": _DATA_DIR / "skill_tree.json",
        "math": _DATA_DIR / "skill_tree_math.json",
    }
    path = files.get(track_key, files["physics"])
    if not path.is_file():
        return {"track_id": track_key, "track_title": "Навыки", "nodes": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_skill_tree_data(topic: str) -> dict:
    """Шаблон дерева для текущей темы диалога."""
    return _load_track(track_key_for_topic(topic))


def topic_matches_user_topic(user_topic: str, node: dict) -> bool:
    t = (user_topic or "").strip().lower()
    if not t:
        return False
    title = (node.get("title") or "").strip().lower()
    if title and title in t:
        return True
    for kw in node.get("keywords") or []:
        if str(kw).lower() in t:
            return True
    return False


def _completed_ids(skill_status: dict[str, str]) -> set[str]:
    return {nid for nid, s in skill_status.items() if s == "completed"}


def merge_node_statuses(nodes: list[dict], skill_status: dict[str, str]) -> list[dict]:
    """Возвращает ноды с полем status: locked | available | in_progress | completed."""
    completed = _completed_ids(skill_status)
    out: list[dict] = []
    for node in nodes:
        nid = node["id"]
        deps = list(node.get("depends_on") or [])
        deps_ok = all(d in completed for d in deps)
        explicit = skill_status.get(nid)

        if explicit == "completed":
            status = "completed"
        elif explicit == "in_progress":
            status = "in_progress"
        elif deps_ok:
            status = "available"
        else:
            status = "locked"
        row = {**node, "status": status}
        out.append(row)
    return out


def apply_skill_tree_updates(memory: UserMemory, topic: str, reply_mode: str) -> None:
    """Обновляет memory.skill_status по текущей теме и режиму ответа."""
    data = load_skill_tree_data(topic)
    nodes = list(data.get("nodes") or [])
    if not nodes or not (topic or "").strip():
        return

    topic = topic.strip()
    prog = memory.progress.get(topic) or ""
    completed = _completed_ids(memory.skill_status)

    for node in nodes:
        if not topic_matches_user_topic(topic, node):
            continue
        nid = node["id"]
        deps = list(node.get("depends_on") or [])
        deps_ok = all(d in completed for d in deps)

        if reply_mode == "explain" and prog == "completed":
            memory.skill_status[nid] = "completed"
        elif prog == "in_progress" and (deps_ok or not deps):
            prev = memory.skill_status.get(nid)
            if prev != "completed":
                memory.skill_status[nid] = "in_progress"

    if len(memory.skill_status) > 64:
        # оставляем завершённые и последние in_progress
        keep = {k: v for k, v in memory.skill_status.items() if v == "completed"}
        ip = {k: v for k, v in memory.skill_status.items() if v == "in_progress"}
        for k, v in list(ip.items())[-20:]:
            keep[k] = v
        memory.skill_status = keep


def build_skill_tree_payload(
    skill_status_before: dict[str, str],
    skill_status_after: dict[str, str],
    topic: str = "",
) -> dict:
    """Снимок для API + события unlock/complete."""
    data = load_skill_tree_data(topic)
    nodes_raw = list(data.get("nodes") or [])
    track_title = str(data.get("track_title") or "Навыки")

    before_m = merge_node_statuses(nodes_raw, skill_status_before)
    after_m = merge_node_statuses(nodes_raw, skill_status_after)

    before_by = {n["id"]: n["status"] for n in before_m}
    unlocked: list[dict[str, str]] = []
    completed_ev: list[dict[str, str]] = []

    for n in after_m:
        oid = before_by.get(n["id"])
        if n["status"] == "completed" and oid != "completed":
            completed_ev.append({"id": n["id"], "title": n["title"]})
        if n["status"] == "available" and oid == "locked":
            unlocked.append({"id": n["id"], "title": n["title"]})

    total = len(after_m)
    done = sum(1 for n in after_m if n["status"] == "completed")

    nodes_public = [
        {
            "id": n["id"],
            "title": n["title"],
            "depends_on": list(n.get("depends_on") or []),
            "status": n["status"],
        }
        for n in after_m
    ]

    return {
        "track_id": data.get("track_id", "default"),
        "track_title": track_title,
        "completed": done,
        "total": total,
        "nodes": nodes_public,
        "events": {"unlocked": unlocked, "completed": completed_ev},
    }
