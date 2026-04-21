from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_educator
from app.db.models import (
    Assignment,
    ClassStudent,
    Classroom,
    Conversation,
    GamificationProgress,
    Message,
    User,
)
from app.db.session import get_db
from app.services.conversation_db import display_title_for_conversation, fallacy_summary_for_user
from app.services.learning_service import get_user_pedagogy_public, get_user_skills_summary
from app.services.reports import build_weekly_report_json, build_weekly_report_pdf, send_report_email

router = APIRouter(prefix="/educator", tags=["educator"])


class ClassCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=512)


class ClassOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: str
    students_count: int
    assignments_count: int


class AddStudentBody(BaseModel):
    email: EmailStr | None = None
    user_id: int | None = Field(None, ge=1)


class StudentSummaryOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    joined_at: str
    wisdom_points: int
    current_difficulty: int
    active_assignments: int
    last_activity_at: str | None


class AssignmentCreateBody(BaseModel):
    class_id: int
    title: str = Field(..., min_length=1, max_length=255)
    prompt: str = Field(..., min_length=1, max_length=4000)
    due_date: datetime | None = None


class AssignmentOut(BaseModel):
    id: int
    class_id: int
    class_name: str
    title: str
    prompt: str
    due_date: str | None
    created_at: str


class SubmissionOut(BaseModel):
    student_id: int
    student_name: str
    conversation_id: int
    title: str
    started_at: str
    last_updated_at: str


class StudentProgressOut(BaseModel):
    student: dict[str, Any]
    skills: list[dict[str, Any]]
    pedagogy: dict[str, Any]
    gamification: dict[str, Any]
    frequent_fallacies: list[dict[str, Any]]
    conversations_total: int
    recent_conversations: list[dict[str, Any]]
    activity_by_day: list[dict[str, Any]]
    active_assignments: list[dict[str, Any]]


class WeeklyReportEmailBody(BaseModel):
    class_id: int
    email: EmailStr


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _class_out(db: Session, classroom: Classroom) -> ClassOut:
    students_count = db.scalar(
        select(func.count()).select_from(ClassStudent).where(ClassStudent.class_id == classroom.id)
    ) or 0
    assignments_count = db.scalar(
        select(func.count()).select_from(Assignment).where(Assignment.class_id == classroom.id)
    ) or 0
    return ClassOut(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        created_at=classroom.created_at.isoformat(),
        students_count=int(students_count),
        assignments_count=int(assignments_count),
    )


def _ensure_classroom(db: Session, educator: User, class_id: int) -> Classroom:
    classroom = db.get(Classroom, class_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Class not found")
    if educator.role != "admin" and classroom.educator_id != educator.id:
        raise HTTPException(status_code=403, detail="No access to this class")
    return classroom


def _educator_has_student(db: Session, educator: User, student_id: int) -> bool:
    if educator.role == "admin":
        return True
    row = db.execute(
        select(ClassStudent)
        .join(Classroom, Classroom.id == ClassStudent.class_id)
        .where(Classroom.educator_id == educator.id, ClassStudent.student_id == student_id)
        .limit(1)
    ).scalar_one_or_none()
    return row is not None


def _student_summary(db: Session, classroom: Classroom, link: ClassStudent) -> StudentSummaryOut:
    student = db.get(User, link.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    gam = db.get(GamificationProgress, student.id)
    pedagogy = get_user_pedagogy_public(db, student.id)
    active_assignments = db.scalar(
        select(func.count())
        .select_from(Assignment)
        .where(
            Assignment.class_id == classroom.id,
            (Assignment.due_date.is_(None)) | (Assignment.due_date >= _now_utc()),
        )
    ) or 0
    last_activity = (
        db.execute(
            select(Conversation.last_updated_at)
            .where(Conversation.user_id == student.id)
            .order_by(Conversation.last_updated_at.desc())
            .limit(1)
        ).scalar_one_or_none()
    )
    return StudentSummaryOut(
        id=student.id,
        email=student.email,
        full_name=student.full_name,
        joined_at=link.joined_at.isoformat(),
        wisdom_points=int(gam.wisdom_points if gam else 0),
        current_difficulty=int(pedagogy.get("current_difficulty") or 1),
        active_assignments=int(active_assignments),
        last_activity_at=last_activity.isoformat() if last_activity else None,
    )


@router.post("/classes", response_model=ClassOut)
def create_classroom(
    body: ClassCreateBody,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    classroom = Classroom(
        educator_id=educator.id,
        name=body.name.strip(),
        description=(body.description or "").strip() or None,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return _class_out(db, classroom)


@router.get("/classes", response_model=list[ClassOut])
def list_classrooms(
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    stmt = select(Classroom).order_by(Classroom.created_at.desc())
    if educator.role != "admin":
        stmt = stmt.where(Classroom.educator_id == educator.id)
    rows = db.execute(stmt).scalars().all()
    return [_class_out(db, classroom) for classroom in rows]


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classroom(
    class_id: int,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    classroom = _ensure_classroom(db, educator, class_id)
    db.delete(classroom)
    db.commit()
    return None


@router.post("/classes/{class_id}/students", response_model=StudentSummaryOut)
def add_student_to_classroom(
    class_id: int,
    body: AddStudentBody,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    classroom = _ensure_classroom(db, educator, class_id)
    student: User | None = None
    if body.user_id:
        student = db.get(User, body.user_id)
    elif body.email:
        student = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Only student accounts can be added")
    existing = db.get(ClassStudent, {"class_id": classroom.id, "student_id": student.id})
    if existing is None:
        existing = ClassStudent(class_id=classroom.id, student_id=student.id)
        db.add(existing)
        db.commit()
        db.refresh(existing)
    return _student_summary(db, classroom, existing)


@router.delete("/classes/{class_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student_from_classroom(
    class_id: int,
    student_id: int,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    classroom = _ensure_classroom(db, educator, class_id)
    link = db.get(ClassStudent, {"class_id": classroom.id, "student_id": student_id})
    if link is None:
        raise HTTPException(status_code=404, detail="Student is not in class")
    db.delete(link)
    db.commit()
    return None


@router.get("/classes/{class_id}/students", response_model=list[StudentSummaryOut])
def list_classroom_students(
    class_id: int,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    classroom = _ensure_classroom(db, educator, class_id)
    rows = (
        db.execute(
            select(ClassStudent)
            .where(ClassStudent.class_id == classroom.id)
            .order_by(ClassStudent.joined_at.asc())
        )
        .scalars()
        .all()
    )
    return [_student_summary(db, classroom, link) for link in rows]


@router.get("/students/{student_id}/progress", response_model=StudentProgressOut)
def get_student_progress(
    student_id: int,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    student = db.get(User, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if not _educator_has_student(db, educator, student_id):
        raise HTTPException(status_code=403, detail="No access to this student")

    skills = get_user_skills_summary(db, student_id)
    pedagogy = get_user_pedagogy_public(db, student_id)
    gam = db.get(GamificationProgress, student_id)
    frequent_fallacies = fallacy_summary_for_user(db, student_id, limit=8)
    total_conversations = db.scalar(
        select(func.count()).select_from(Conversation).where(Conversation.user_id == student_id)
    ) or 0
    recent = (
        db.execute(
            select(Conversation)
            .where(Conversation.user_id == student_id)
            .order_by(Conversation.last_updated_at.desc())
            .limit(8)
        )
        .scalars()
        .all()
    )

    since = _now_utc() - timedelta(days=6)
    activity_rows = (
        db.execute(
            select(func.date(Message.created_at), func.count())
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Conversation.user_id == student_id,
                Message.role == "user",
                Message.created_at >= since,
            )
            .group_by(func.date(Message.created_at))
            .order_by(func.date(Message.created_at).asc())
        )
        .all()
    )
    activity = [{"day": str(day), "messages": int(count)} for day, count in activity_rows]

    active_assignments = (
        db.execute(
            select(Assignment)
            .join(ClassStudent, ClassStudent.class_id == Assignment.class_id)
            .where(
                ClassStudent.student_id == student_id,
                (Assignment.due_date.is_(None)) | (Assignment.due_date >= _now_utc()),
            )
            .order_by(Assignment.created_at.desc())
        )
        .scalars()
        .all()
    )

    return StudentProgressOut(
        student={
            "id": student.id,
            "email": student.email,
            "full_name": student.full_name,
        },
        skills=skills,
        pedagogy=pedagogy,
        gamification={
            "wisdom_points": int(gam.wisdom_points if gam else 0),
            "level": int(gam.level if gam else 1),
            "streak_days": int(gam.streak_days if gam else 0),
        },
        frequent_fallacies=frequent_fallacies,
        conversations_total=int(total_conversations),
        recent_conversations=[
            {
                "id": conv.id,
                "title": display_title_for_conversation(db, conv),
                "last_updated_at": conv.last_updated_at.isoformat(),
                "assignment_id": conv.assignment_id,
            }
            for conv in recent
        ],
        activity_by_day=activity,
        active_assignments=[
            {
                "id": assignment.id,
                "title": assignment.title,
                "prompt": assignment.prompt,
                "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            }
            for assignment in active_assignments
        ],
    )


@router.post("/assignments", response_model=AssignmentOut)
def create_assignment(
    body: AssignmentCreateBody,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    classroom = _ensure_classroom(db, educator, body.class_id)
    assignment = Assignment(
        class_id=classroom.id,
        title=body.title.strip(),
        prompt=body.prompt.strip(),
        due_date=body.due_date,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return AssignmentOut(
        id=assignment.id,
        class_id=assignment.class_id,
        class_name=classroom.name,
        title=assignment.title,
        prompt=assignment.prompt,
        due_date=assignment.due_date.isoformat() if assignment.due_date else None,
        created_at=assignment.created_at.isoformat(),
    )


@router.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(
    class_id: int | None = Query(None),
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    stmt = select(Assignment, Classroom).join(Classroom, Classroom.id == Assignment.class_id).order_by(Assignment.created_at.desc())
    if educator.role != "admin":
        stmt = stmt.where(Classroom.educator_id == educator.id)
    if class_id is not None:
        stmt = stmt.where(Assignment.class_id == class_id)
    rows = db.execute(stmt).all()
    return [
        AssignmentOut(
            id=assignment.id,
            class_id=classroom.id,
            class_name=classroom.name,
            title=assignment.title,
            prompt=assignment.prompt,
            due_date=assignment.due_date.isoformat() if assignment.due_date else None,
            created_at=assignment.created_at.isoformat(),
        )
        for assignment, classroom in rows
    ]


@router.get("/assignments/{assignment_id}/submissions", response_model=list[SubmissionOut])
def get_assignment_submissions(
    assignment_id: int,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    classroom = _ensure_classroom(db, educator, assignment.class_id)
    rows = (
        db.execute(
            select(Conversation, User)
            .join(User, User.id == Conversation.user_id)
            .where(Conversation.assignment_id == assignment.id)
            .order_by(Conversation.last_updated_at.desc())
        )
        .all()
    )
    return [
        SubmissionOut(
            student_id=user.id,
            student_name=user.full_name or user.email,
            conversation_id=conversation.id,
            title=display_title_for_conversation(db, conversation),
            started_at=conversation.started_at.isoformat(),
            last_updated_at=conversation.last_updated_at.isoformat(),
        )
        for conversation, user in rows
    ]


@router.get("/conversations/{conversation_id}")
def educator_get_conversation(
    conversation_id: int,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not _educator_has_student(db, educator, conversation.user_id):
        raise HTTPException(status_code=403, detail="No access to this conversation")
    messages = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
        )
        .scalars()
        .all()
    )
    return {
        "id": conversation.id,
        "title": display_title_for_conversation(db, conversation),
        "started_at": conversation.started_at.isoformat(),
        "last_updated_at": conversation.last_updated_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


@router.get("/reports/weekly")
def get_weekly_report(
    class_id: int,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    classroom = _ensure_classroom(db, educator, class_id)
    return build_weekly_report_json(db, classroom)


@router.get("/reports/weekly.pdf")
def get_weekly_report_pdf(
    class_id: int,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    classroom = _ensure_classroom(db, educator, class_id)
    report = build_weekly_report_json(db, classroom)
    pdf = build_weekly_report_pdf(report)
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in classroom.name) or "class"
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="weekly_report_{safe_name}.pdf"'},
    )


@router.post("/reports/send-email", status_code=status.HTTP_202_ACCEPTED)
def send_weekly_report_email(
    body: WeeklyReportEmailBody,
    background_tasks: BackgroundTasks,
    educator: User = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    classroom = _ensure_classroom(db, educator, body.class_id)
    report = build_weekly_report_json(db, classroom)
    pdf = build_weekly_report_pdf(report)
    subject = f"Socrates AI report: {classroom.name}"
    text = (
        f"Weekly report for class {classroom.name}.\n"
        f"Students: {report['summary']['students_total']}\n"
        f"Active last week: {report['summary']['active_students_last_week']}\n"
    )
    background_tasks.add_task(
        send_report_email,
        body.email,
        subject,
        text,
        pdf,
        f"weekly_report_{classroom.id}.pdf",
    )
    return {"queued": True}
