from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import AttendanceRecord, Classroom, Course, LeaveRequest, Student
from ..utils import log_operation, permission_required

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


@attendance_bp.route("/check", methods=["GET", "POST"])
@login_required
@permission_required("attendance.manage")
def check_attendance():
    classes = Classroom.query.order_by(Classroom.name.asc()).all()
    courses = Course.query.order_by(Course.name.asc()).all()
    class_id = request.values.get("class_id", type=int)
    course_id = request.values.get("course_id", type=int)
    record_date_raw = request.values.get("record_date", datetime.utcnow().strftime("%Y-%m-%d"))

    students = []
    record_map = {}
    if class_id:
        students = Student.query.filter_by(class_id=class_id).order_by(Student.name.asc()).all()

    try:
        record_date = datetime.strptime(record_date_raw, "%Y-%m-%d").date()
    except ValueError:
        record_date = datetime.utcnow().date()

    if students and course_id:
        records = AttendanceRecord.query.filter_by(course_id=course_id, record_date=record_date).all()
        record_map = {record.student_id: record for record in records}

    if request.method == "POST" and request.form.get("action") == "save":
        record_date = datetime.strptime(record_date_raw, "%Y-%m-%d").date()
        for student in students:
            status = request.form.get(f"status_{student.id}")
            remarks = request.form.get(f"remark_{student.id}")
            if not status:
                continue
            record = AttendanceRecord.query.filter_by(
                student_id=student.id,
                course_id=course_id,
                record_date=record_date,
            ).first()
            if record:
                record.status = status
                record.remarks = remarks
            else:
                record = AttendanceRecord(
                    student_id=student.id,
                    course_id=course_id,
                    record_date=record_date,
                    status=status,
                    remarks=remarks,
                )
                db.session.add(record)
        db.session.commit()
        log_operation(current_user.id, "update", "attendance", f"记录考勤 {record_date}")
        flash("考勤记录已保存", "success")
        return redirect(url_for("attendance.check_attendance", class_id=class_id, course_id=course_id, record_date=record_date_raw))

    return render_template(
        "attendance/check.html",
        classes=classes,
        courses=courses,
        students=students,
        class_id=class_id,
        course_id=course_id,
        record_date=record_date_raw,
        record_map=record_map,
    )


@attendance_bp.route("/statistics")
@login_required
@permission_required("attendance.manage")
def statistics():
    summary = (
        db.session.query(
            AttendanceRecord.status,
            db.func.count(AttendanceRecord.id),
        )
        .group_by(AttendanceRecord.status)
        .all()
    )

    class_summary = (
        db.session.query(
            Classroom.name,
            AttendanceRecord.status,
            db.func.count(AttendanceRecord.id),
        )
        .join(Student, Student.id == AttendanceRecord.student_id)
        .join(Classroom, Classroom.id == Student.class_id)
        .group_by(Classroom.name, AttendanceRecord.status)
        .all()
    )

    class_stat_map = {}
    for class_name, status, count in class_summary:
        class_stat_map.setdefault(class_name, {}).update({status: count})

    return render_template(
        "attendance/statistics.html",
        summary=summary,
        class_stat_map=class_stat_map,
    )


@attendance_bp.route("/leaves", methods=["GET", "POST"])
@login_required
def leave_requests():
    if request.method == "POST" and current_user.has_permission("attendance.manage"):
        request_id = request.form.get("request_id", type=int)
        action = request.form.get("action")
        leave_request = LeaveRequest.query.get_or_404(request_id)
        leave_request.status = "approved" if action == "approve" else "rejected"
        leave_request.approver_id = current_user.id
        leave_request.reviewed_at = datetime.utcnow()
        db.session.commit()
        log_operation(current_user.id, "update", "leave_request", f"{action} leave {leave_request.id}")
        flash("请假申请已处理", "success")
        return redirect(url_for("attendance.leave_requests"))

    leaves = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template("attendance/leaves.html", leaves=leaves)


@attendance_bp.route("/leaves/new", methods=["GET", "POST"])
@login_required
def create_leave_request():
    student = current_user.student_profile
    if not student:
        flash("仅学生可以提交请假申请", "danger")
        return redirect(url_for("attendance.leave_requests"))

    if request.method == "POST":
        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")
        reason = request.form.get("reason", "").strip()
        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("日期格式不正确", "danger")
            return render_template("attendance/leave_form.html")
        if start_date > end_date:
            flash("结束日期不能早于开始日期", "danger")
            return render_template("attendance/leave_form.html")
        leave_request = LeaveRequest(
            student_id=student.id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
        )
        db.session.add(leave_request)
        db.session.commit()
        log_operation(current_user.id, "create", "leave_request", f"student {student.id}")
        flash("请假申请已提交", "success")
        return redirect(url_for("attendance.leave_requests"))

    return render_template("attendance/leave_form.html")
