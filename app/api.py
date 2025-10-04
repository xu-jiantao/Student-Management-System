from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import (
    Announcement,
    AttendanceRecord,
    Classroom,
    Course,
    GradeRecord,
    Student,
    TodoItem,
)

api_bp = Blueprint("api", __name__)


def _parse_date(value: str) -> datetime.date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _require_text(data: dict, field: str) -> str:
    value = data.get(field)
    if value is None:
        raise ValueError(f"缺少字段: {field}")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} 不能为空")
    return text


@api_bp.errorhandler(ValueError)
def handle_value_error(error: ValueError):
    return jsonify({"error": str(error)}), 400


@api_bp.get("/students")
def api_list_students():
    query = Student.query.order_by(Student.student_number.asc())
    search_term = request.args.get("q", type=str, default="").strip()
    if search_term:
        like_term = f"%{search_term}%"
        query = query.filter(
            (Student.student_number.ilike(like_term))
            | (Student.name.ilike(like_term))
            | (Student.class_name.ilike(like_term))
        )
    return jsonify([student.to_dict() for student in query.all()])


@api_bp.post("/students")
def api_create_student():
    payload = request.get_json(force=True, silent=False)
    if not payload:
        raise ValueError("请求体不能为空")

    student = Student(
        student_number=_require_text(payload, "student_number"),
        name=_require_text(payload, "name"),
        gender=_require_text(payload, "gender"),
        date_of_birth=_parse_date(_require_text(payload, "date_of_birth")),
        class_name=_require_text(payload, "class_name"),
        email=_require_text(payload, "email"),
        phone=_require_text(payload, "phone"),
        address=str(payload.get("address", "")).strip() or None,
    )

    db.session.add(student)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ValueError("学号已存在") from exc

    return jsonify(student.to_dict()), 201


@api_bp.get("/students/<int:student_id>")
def api_get_student(student_id: int):
    student = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict())


@api_bp.put("/students/<int:student_id>")
def api_update_student(student_id: int):
    student = Student.query.get_or_404(student_id)
    payload = request.get_json(force=True, silent=False)
    if not payload:
        raise ValueError("请求体不能为空")

    student.student_number = _require_text(payload, "student_number")
    student.name = _require_text(payload, "name")
    student.gender = _require_text(payload, "gender")
    student.date_of_birth = _parse_date(_require_text(payload, "date_of_birth"))
    student.class_name = _require_text(payload, "class_name")
    student.email = _require_text(payload, "email")
    student.phone = _require_text(payload, "phone")
    student.address = str(payload.get("address", "")).strip() or None

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ValueError("学号已存在") from exc

    return jsonify(student.to_dict())


@api_bp.delete("/students/<int:student_id>")
def api_delete_student(student_id: int):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({"status": "deleted", "id": student_id})


@api_bp.get("/dashboard/summary")
@login_required
def api_dashboard_summary():
    return jsonify(
        {
            "students": Student.query.count(),
            "classes": Classroom.query.count(),
            "teachers": Course.query.distinct(Course.teacher_id).count(),
            "courses": Course.query.count(),
        }
    )


@api_bp.get("/classes")
@login_required
def api_list_classes():
    classrooms = Classroom.query.order_by(Classroom.name.asc()).all()
    return jsonify(
        [
            {
                "id": classroom.id,
                "name": classroom.name,
                "grade_level": classroom.grade_level,
                "head_teacher_id": classroom.head_teacher_id,
                "student_count": len(classroom.students),
            }
            for classroom in classrooms
        ]
    )


@api_bp.get("/courses")
@login_required
def api_list_courses():
    courses = Course.query.order_by(Course.name.asc()).all()
    return jsonify(
        [
            {
                "id": course.id,
                "code": course.code,
                "name": course.name,
                "credit": course.credit,
                "teacher_id": course.teacher_id,
                "classroom_id": course.classroom_id,
            }
            for course in courses
        ]
    )


@api_bp.get("/grades")
@login_required
def api_list_grades():
    records = (
        db.session.query(
            GradeRecord.id,
            Student.student_number,
            Student.name,
            Course.name,
            GradeRecord.term,
            GradeRecord.assessment_type,
            GradeRecord.score,
        )
        .join(Student, Student.id == GradeRecord.student_id)
        .join(Course, Course.id == GradeRecord.course_id)
        .all()
    )
    return jsonify(
        [
            {
                "id": record_id,
                "student_number": student_number,
                "student_name": student_name,
                "course": course_name,
                "term": term,
                "assessment_type": assessment_type,
                "score": score,
            }
            for record_id, student_number, student_name, course_name, term, assessment_type, score in records
        ]
    )


@api_bp.get("/attendance")
@login_required
def api_attendance_records():
    records = AttendanceRecord.query.order_by(AttendanceRecord.record_date.desc()).limit(200).all()
    return jsonify(
        [
            {
                "id": record.id,
                "student_id": record.student_id,
                "course_id": record.course_id,
                "record_date": record.record_date.isoformat(),
                "status": record.status,
                "remarks": record.remarks,
            }
            for record in records
        ]
    )


@api_bp.get("/announcements")
@login_required
def api_list_announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return jsonify(
        [
            {
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "created_at": announcement.created_at.isoformat(),
                "is_pinned": announcement.is_pinned,
            }
            for announcement in announcements
        ]
    )


@api_bp.post("/todos")
@login_required
def api_create_todo():
    payload = request.get_json(force=True)
    if not payload or "content" not in payload:
        raise ValueError("缺少字段: content")
    todo = TodoItem(user_id=current_user.id, content=str(payload["content"]).strip())
    db.session.add(todo)
    db.session.commit()
    return jsonify({"id": todo.id, "content": todo.content}), 201
