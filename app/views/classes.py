from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Classroom, Student, Teacher
from ..utils import log_operation, permission_required

classes_bp = Blueprint("classes", __name__, url_prefix="/classes")


@classes_bp.route("/")
@login_required
@permission_required("classes.manage")
def list_classes():
    classrooms = Classroom.query.order_by(Classroom.name.asc()).all()
    return render_template("classes/list.html", classrooms=classrooms)


@classes_bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("classes.manage")
def create_class():
    teachers = Teacher.query.order_by(Teacher.name.asc()).all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        grade_level = request.form.get("grade_level", "").strip() or None
        description = request.form.get("description", "").strip() or None
        head_teacher_id = request.form.get("head_teacher_id", type=int)

        if not name:
            flash("班级名称不能为空", "danger")
            return render_template("classes/form.html", teachers=teachers)
        if Classroom.query.filter_by(name=name).first():
            flash("班级名称已存在", "danger")
            return render_template("classes/form.html", teachers=teachers)

        classroom = Classroom(
            name=name,
            grade_level=grade_level,
            description=description,
            head_teacher_id=head_teacher_id,
        )
        db.session.add(classroom)
        db.session.commit()
        log_operation(current_user.id, "create", "class", f"创建班级 {classroom.name}")
        flash("班级创建成功", "success")
        return redirect(url_for("classes.list_classes"))

    return render_template("classes/form.html", teachers=teachers)


@classes_bp.route("/<int:class_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("classes.manage")
def edit_class(class_id: int):
    classroom = Classroom.query.get_or_404(class_id)
    teachers = Teacher.query.order_by(Teacher.name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        grade_level = request.form.get("grade_level", "").strip() or None
        description = request.form.get("description", "").strip() or None
        head_teacher_id = request.form.get("head_teacher_id", type=int)

        if not name:
            flash("班级名称不能为空", "danger")
            return render_template("classes/form.html", classroom=classroom, teachers=teachers)
        if name != classroom.name and Classroom.query.filter_by(name=name).first():
            flash("班级名称已存在", "danger")
            return render_template("classes/form.html", classroom=classroom, teachers=teachers)

        classroom.name = name
        classroom.grade_level = grade_level
        classroom.description = description
        classroom.head_teacher_id = head_teacher_id
        db.session.commit()
        log_operation(current_user.id, "update", "class", f"更新班级 {classroom.name}")
        flash("班级信息更新成功", "success")
        return redirect(url_for("classes.list_classes"))

    return render_template("classes/form.html", classroom=classroom, teachers=teachers)


@classes_bp.route("/<int:class_id>")
@login_required
@permission_required("classes.manage")
def class_detail(class_id: int):
    classroom = Classroom.query.get_or_404(class_id)
    students = Student.query.filter_by(class_id=class_id).order_by(Student.name.asc()).all()
    return render_template("classes/detail.html", classroom=classroom, students=students)


@classes_bp.route("/<int:class_id>/assign", methods=["GET", "POST"])
@login_required
@permission_required("classes.manage")
def assign_students(class_id: int):
    classroom = Classroom.query.get_or_404(class_id)
    all_students = Student.query.order_by(Student.name.asc()).all()
    if request.method == "POST":
        selected_ids = request.form.getlist("student_ids")
        classroom.students.clear()
        for student_id in selected_ids:
            student = Student.query.get(int(student_id))
            if student:
                student.class_id = classroom.id
        db.session.commit()
        log_operation(current_user.id, "update", "class", f"调整班级 {classroom.name} 学生名单")
        flash("班级学生分配已更新", "success")
        return redirect(url_for("classes.class_detail", class_id=classroom.id))

    return render_template("classes/assign.html", classroom=classroom, students=all_students)
