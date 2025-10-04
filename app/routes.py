from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from . import db
from .models import Student

web_bp = Blueprint("web", __name__)


def _get_student_or_404(student_id: int) -> Student:
    student = Student.query.get(student_id)
    if student is None:
        abort(404, description="Student not found")
    return student


@web_bp.route("/")
def index() -> str:
    return redirect(url_for("web.list_students"))


@web_bp.route("/students")
def list_students() -> str:
    query = Student.query.order_by(Student.student_number.asc())
    search_term = request.args.get("q", type=str, default="").strip()
    if search_term:
        like_term = f"%{search_term}%"
        query = query.filter(
            (Student.student_number.ilike(like_term))
            | (Student.name.ilike(like_term))
            | (Student.class_name.ilike(like_term))
        )
    students = query.all()
    return render_template("student_list.html", students=students, search_term=search_term)


@web_bp.route("/students/new", methods=["GET", "POST"])
def create_student() -> str:
    if request.method == "POST":
        form = request.form
        student_number = form.get("student_number", "").strip()
        name = form.get("name", "").strip()
        gender = form.get("gender", "").strip()
        class_name = form.get("class_name", "").strip()
        email = form.get("email", "").strip()
        phone = form.get("phone", "").strip()
        address = form.get("address", "").strip() or None
        dob_raw = form.get("date_of_birth", "").strip()

        errors = []
        if not student_number:
            errors.append("学号不能为空")
        elif Student.query.filter_by(student_number=student_number).first():
            errors.append("学号已存在")

        if not name:
            errors.append("姓名不能为空")
        if not gender:
            errors.append("性别不能为空")
        if not class_name:
            errors.append("班级不能为空")
        if not email:
            errors.append("邮箱不能为空")
        if not phone:
            errors.append("联系电话不能为空")

        try:
            date_of_birth = datetime.strptime(dob_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("出生日期格式不正确，应为 YYYY-MM-DD")
            date_of_birth = None

        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template(
                "student_form.html",
                mode="create",
                student=form,
                student_id=None,
            )

        student = Student(
            student_number=student_number,
            name=name,
            gender=gender,
            date_of_birth=date_of_birth,
            class_name=class_name,
            email=email,
            phone=phone,
            address=address,
        )
        db.session.add(student)
        db.session.commit()
        flash("学生信息创建成功", "success")
        return redirect(url_for("web.list_students"))

    return render_template(
        "student_form.html",
        mode="create",
        student={},
        student_id=None,
    )


@web_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id: int) -> str:
    student = _get_student_or_404(student_id)

    if request.method == "POST":
        form = request.form
        student_number = form.get("student_number", "").strip()
        name = form.get("name", "").strip()
        gender = form.get("gender", "").strip()
        class_name = form.get("class_name", "").strip()
        email = form.get("email", "").strip()
        phone = form.get("phone", "").strip()
        address = form.get("address", "").strip() or None
        dob_raw = form.get("date_of_birth", "").strip()

        errors = []

        if not student_number:
            errors.append("学号不能为空")
        elif (
            student_number != student.student_number
            and Student.query.filter_by(student_number=student_number).first()
        ):
            errors.append("学号已存在")

        if not name:
            errors.append("姓名不能为空")
        if not gender:
            errors.append("性别不能为空")
        if not class_name:
            errors.append("班级不能为空")
        if not email:
            errors.append("邮箱不能为空")
        if not phone:
            errors.append("联系电话不能为空")

        try:
            date_of_birth = datetime.strptime(dob_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("出生日期格式不正确，应为 YYYY-MM-DD")
            date_of_birth = None

        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template(
                "student_form.html",
                mode="edit",
                student=form,
                student_id=student.id,
            )

        student.student_number = student_number
        student.name = name
        student.gender = gender
        student.date_of_birth = date_of_birth
        student.class_name = class_name
        student.email = email
        student.phone = phone
        student.address = address

        db.session.commit()
        flash("学生信息更新成功", "success")
        return redirect(url_for("web.list_students"))

    return render_template(
        "student_form.html",
        mode="edit",
        student=student,
        student_id=student.id,
    )


@web_bp.route("/students/<int:student_id>")
def student_detail(student_id: int) -> str:
    student = _get_student_or_404(student_id)
    return render_template("student_detail.html", student=student)


@web_bp.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id: int):  # type: ignore[override]
    student = _get_student_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash("学生信息删除成功", "success")
    return redirect(url_for("web.list_students"))
