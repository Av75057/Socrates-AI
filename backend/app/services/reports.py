from __future__ import annotations

import io
import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Assignment, ClassStudent, Classroom, Conversation, Message, User
from app.services.learning_service import get_user_pedagogy_public, get_user_skills_summary


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_weekly_report_json(db: Session, classroom: Classroom) -> dict[str, Any]:
    now = _utc_now()
    week_ago = now - timedelta(days=7)
    student_ids = [row.student_id for row in classroom.students]
    assignments = (
        db.execute(
            select(Assignment)
            .where(Assignment.class_id == classroom.id)
            .order_by(Assignment.created_at.desc())
        )
        .scalars()
        .all()
    )
    started_conv_ids = (
        db.execute(
            select(Conversation.id)
            .join(ClassStudent, ClassStudent.student_id == Conversation.user_id)
            .where(
                ClassStudent.class_id == classroom.id,
                Conversation.last_updated_at >= week_ago,
            )
        )
        .scalars()
        .all()
    )
    active_students = (
        db.execute(
            select(func.count(func.distinct(Conversation.user_id)))
            .join(ClassStudent, ClassStudent.student_id == Conversation.user_id)
            .where(
                ClassStudent.class_id == classroom.id,
                Conversation.last_updated_at >= week_ago,
            )
        ).scalar()
        or 0
    )
    submissions_by_assignment: dict[int, int] = {}
    if assignments:
        rows = (
            db.execute(
                select(Conversation.assignment_id, func.count(func.distinct(Conversation.user_id)))
                .where(
                    Conversation.assignment_id.in_([a.id for a in assignments]),
                    Conversation.last_updated_at >= week_ago,
                )
                .group_by(Conversation.assignment_id)
            )
            .all()
        )
        submissions_by_assignment = {int(aid): int(cnt) for aid, cnt in rows if aid is not None}

    student_rows = (
        db.execute(
            select(User)
            .join(ClassStudent, ClassStudent.student_id == User.id)
            .where(ClassStudent.class_id == classroom.id)
            .order_by(User.full_name.asc(), User.email.asc())
        )
        .scalars()
        .all()
    )
    student_cards: list[dict[str, Any]] = []
    for student in student_rows:
        pedagogy = get_user_pedagogy_public(db, student.id)
        skills = get_user_skills_summary(db, student.id)
        top_skills = sorted(skills, key=lambda item: int(item.get("level") or 0), reverse=True)[:3]
        weak_skills = sorted(skills, key=lambda item: int(item.get("level") or 0))[:3]
        dialogs = (
            db.execute(
                select(func.count())
                .select_from(Conversation)
                .where(Conversation.user_id == student.id, Conversation.last_updated_at >= week_ago)
            ).scalar()
            or 0
        )
        student_cards.append(
            {
                "student_id": student.id,
                "student_name": student.full_name or student.email,
                "dialogs_last_week": int(dialogs),
                "current_difficulty": pedagogy.get("current_difficulty", 1),
                "top_skills": top_skills,
                "weak_skills": weak_skills,
            }
        )

    return {
        "class": {
            "id": classroom.id,
            "name": classroom.name,
            "description": classroom.description,
        },
        "period": {
            "from": week_ago.isoformat(),
            "to": now.isoformat(),
        },
        "summary": {
            "students_total": len(student_ids),
            "active_students_last_week": int(active_students),
            "conversations_last_week": len(started_conv_ids),
            "assignments_total": len(assignments),
        },
        "assignments": [
            {
                "id": a.id,
                "title": a.title,
                "due_date": a.due_date.isoformat() if a.due_date else None,
                "submissions_last_week": submissions_by_assignment.get(a.id, 0),
            }
            for a in assignments
        ],
        "students": student_cards,
    }


def build_weekly_report_pdf(report: dict[str, Any]) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except ModuleNotFoundError as exc:
        raise RuntimeError("PDF reports require reportlab to be installed") from exc

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 20 * mm

    def line(text: str, *, size: int = 11, color=colors.black, leading: int = 7) -> None:
        nonlocal y
        pdf.setFillColor(color)
        pdf.setFont("Helvetica", size)
        pdf.drawString(15 * mm, y, text[:110])
        y -= leading * mm
        if y < 20 * mm:
            pdf.showPage()
            y = height - 20 * mm

    class_name = report["class"]["name"]
    line(f"Socrates AI Weekly Report: {class_name}", size=15, leading=8)
    line(f"Period: {report['period']['from'][:10]} - {report['period']['to'][:10]}", size=10, color=colors.grey)
    y -= 2 * mm
    summary = report["summary"]
    line(f"Students total: {summary['students_total']}")
    line(f"Active students last week: {summary['active_students_last_week']}")
    line(f"Conversations last week: {summary['conversations_last_week']}")
    line(f"Assignments total: {summary['assignments_total']}")

    y -= 3 * mm
    line("Assignments", size=13, color=colors.darkblue)
    for item in report["assignments"][:12]:
        line(
            f"- {item['title']} | due: {(item['due_date'] or 'n/a')[:10]} | submissions: {item['submissions_last_week']}",
            size=10,
            leading=6,
        )

    y -= 3 * mm
    line("Students", size=13, color=colors.darkblue)
    for student in report["students"][:20]:
        line(
            f"- {student['student_name']} | dialogs: {student['dialogs_last_week']} | difficulty: {student['current_difficulty']}",
            size=10,
            leading=6,
        )
        weak = ", ".join(s["name"] for s in student["weak_skills"][:2]) or "n/a"
        top = ", ".join(s["name"] for s in student["top_skills"][:2]) or "n/a"
        line(f"  top: {top}", size=9, color=colors.darkgreen, leading=5)
        line(f"  weak: {weak}", size=9, color=colors.darkred, leading=5)

    pdf.save()
    return buf.getvalue()


def send_report_email(to_email: str, subject: str, body: str, pdf_bytes: bytes, filename: str) -> None:
    host = (os.getenv("SMTP_HOST") or "").strip()
    port = int((os.getenv("SMTP_PORT") or "587").strip() or "587")
    username = (os.getenv("SMTP_USER") or "").strip()
    password = (os.getenv("SMTP_PASSWORD") or "").strip()
    from_email = (os.getenv("SMTP_FROM") or username).strip()
    use_tls = (os.getenv("SMTP_USE_TLS") or "true").strip().lower() not in ("0", "false", "no")
    if not host or not from_email:
        raise RuntimeError("SMTP is not configured")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        if use_tls:
            smtp.starttls()
        if username:
            smtp.login(username, password)
        smtp.send_message(msg)
