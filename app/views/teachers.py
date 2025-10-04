from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Classroom, Teacher
from ..utils import log_operation, permission_required

teachers_bp = Blueprint("teachers", __name__, url_prefix="/teachers")


@teachers_bp.route("/")
@login_required
@permission_required("teachers.manage")
def list_teachers():
    teachers = Teacher.query.order_by(Teacher.name.asc()).all()
    return render_template("teachers/list.html", teachers=teachers)


@teachers_bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("teachers.manage")
def create_teacher():
    if request.method == "POST":
        employee_number = request.form.get("employee_number", "").strip()
        name = request.form.get("name", "").strip()
        gender = request.form.get("gender", "").strip() or None
        email = request.form.get("email", "").strip() or None
        phone = request.form.get("phone", "").strip() or None
        title = request.form.get("professional_title", "").strip() or None
        hire_date_raw = request.form.get("hire_date", "").strip()

        if not employee_number:
            flash("工号不能为空", "danger")
            return render_template("teachers/form.html")
        if Teacher.query.filter_by(employee_number=employee_number).first():
            flash("工号已存在", "danger")
            return render_template("teachers/form.html")
        if not name:
            flash("姓名不能为空", "danger")
            return render_template("teachers/form.html")

        hire_date = None
        if hire_date_raw:
            try:
                hire_date = datetime.strptime(hire_date_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("入职日期格式不正确", "danger")
                return render_template("teachers/form.html")

        teacher = Teacher(
            employee_number=employee_number,
            name=name,
            gender=gender,
            email=email,
            phone=phone,
            professional_title=title,
            hire_date=hire_date,
        )
        db.session.add(teacher)
        db.session.commit()
        log_operation(current_user.id, "create", "teacher", f"创建教师 {teacher.name}")
        flash("教师创建成功", "success")
        return redirect(url_for("teachers.list_teachers"))

    return render_template("teachers/form.html")


@teachers_bp.route("/<int:teacher_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("teachers.manage")
def edit_teacher(teacher_id: int):
    teacher = Teacher.query.get_or_404(teacher_id)

    if request.method == "POST":
        employee_number = request.form.get("employee_number", "").strip()
        name = request.form.get("name", "").strip()
        gender = request.form.get("gender", "").strip() or None
        email = request.form.get("email", "").strip() or None
        phone = request.form.get("phone", "").strip() or None
        title = request.form.get("professional_title", "").strip() or None
        hire_date_raw = request.form.get("hire_date", "").strip()

        if not employee_number:
            flash("工号不能为空", "danger")
            return render_template("teachers/form.html", teacher=teacher)
        if (
            employee_number != teacher.employee_number
            and Teacher.query.filter_by(employee_number=employee_number).first()
        ):
            flash("工号已存在", "danger")
            return render_template("teachers/form.html", teacher=teacher)
        if not name:
            flash("姓名不能为空", "danger")
            return render_template("teachers/form.html", teacher=teacher)

        hire_date = None
        if hire_date_raw:
            try:
                hire_date = datetime.strptime(hire_date_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("入职日期格式不正确", "danger")
                return render_template("teachers/form.html", teacher=teacher)

        teacher.employee_number = employee_number
        teacher.name = name
        teacher.gender = gender
        teacher.email = email
        teacher.phone = phone
        teacher.professional_title = title
        teacher.hire_date = hire_date

        db.session.commit()
        log_operation(current_user.id, "update", "teacher", f"更新教师 {teacher.name}")
        flash("教师信息更新成功", "success")
        return redirect(url_for("teachers.list_teachers"))

    return render_template("teachers/form.html", teacher=teacher)


@teachers_bp.route("/<int:teacher_id>")
@login_required
@permission_required("teachers.manage")
def teacher_detail(teacher_id: int):
    teacher = Teacher.query.get_or_404(teacher_id)
    classes = Classroom.query.filter_by(head_teacher_id=teacher.id).all()
    return render_template("teachers/detail.html", teacher=teacher, classes=classes)
