from __future__ import annotations

from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import (
    Announcement,
    AttendanceRecord,
    Course,
    GradeRecord,
    SystemMessage,
    TodoItem,
    Classroom,
    Student,
    Teacher,
)
from ..utils import log_operation
from sqlalchemy import case


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        due_date = request.form.get("due_date")
        if not content:
            flash("待办内容不能为空", "danger")
        else:
            item = TodoItem(user_id=current_user.id, content=content)
            if due_date:
                try:
                    item.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
                except ValueError:
                    flash("日期格式不正确", "danger")
                    return redirect(url_for("dashboard.index"))
            db.session.add(item)
            db.session.commit()
            log_operation(current_user.id, "create", "todo", content)
            flash("待办已添加", "success")
        return redirect(url_for("dashboard.index"))

    student_count = Student.query.count()
    class_count = Classroom.query.count()
    teacher_count = Teacher.query.count()
    course_count = Course.query.count()

    announcements = (
        Announcement.query.order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
        .limit(5)
        .all()
    )
    todos = (
        TodoItem.query.filter_by(user_id=current_user.id, is_completed=False)
        .order_by(
            case((TodoItem.due_date.is_(None), 1), else_=0),
            TodoItem.due_date.asc(),
        )
        .limit(5)
        .all()
    )
    messages = (
        SystemMessage.query.filter_by(user_id=current_user.id, is_read=False)
        .order_by(SystemMessage.created_at.desc())
        .limit(5)
        .all()
    )

    # 简单的成绩统计（按课程平均分）
    grade_stats_raw = (
        db.session.query(Course.name, db.func.avg(GradeRecord.score))
        .join(GradeRecord, GradeRecord.course_id == Course.id)
        .group_by(Course.id)
        .order_by(Course.name.asc())
        .limit(6)
        .all()
    )
    grade_stats = [(name, float(avg or 0)) for name, avg in grade_stats_raw]

    attendance_stats_raw = (
        db.session.query(AttendanceRecord.status, db.func.count(AttendanceRecord.id))
        .filter(AttendanceRecord.record_date >= date.today() - timedelta(days=30))
        .group_by(AttendanceRecord.status)
        .all()
    )
    attendance_stats = [(status, int(count)) for status, count in attendance_stats_raw]

    return render_template(
        "dashboard/index.html",
        student_count=student_count,
        class_count=class_count,
        teacher_count=teacher_count,
        course_count=course_count,
        announcements=announcements,
        todos=todos,
        messages=messages,
        grade_stats=grade_stats,
        attendance_stats=attendance_stats,
    )
