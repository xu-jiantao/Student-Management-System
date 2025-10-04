from __future__ import annotations

from datetime import datetime

from flask import Blueprint, Response, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Classroom, Student
from ..utils import (
    export_students_to_excel,
    import_students_from_excel,
    log_operation,
    paginate_query,
    permission_required,
    save_uploaded_file,
)

students_bp = Blueprint("students", __name__, url_prefix="/students")


@students_bp.route("/")
@login_required
@permission_required("students.manage")
def list_students():
    page = request.args.get("page", default=1, type=int)
    per_page = 15
    keyword = request.args.get("q", "").strip()
    class_id = request.args.get("class_id", type=int)
    gender = request.args.get("gender", "")

    query = Student.query.order_by(Student.student_number.asc())
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            (Student.name.ilike(like_pattern))
            | (Student.student_number.ilike(like_pattern))
            | (Student.email.ilike(like_pattern))
        )
    if class_id:
        query = query.filter_by(class_id=class_id)
    if gender:
        query = query.filter_by(gender=gender)

    students, total = paginate_query(query, page, per_page)
    classes = Classroom.query.order_by(Classroom.name.asc()).all()
    return render_template(
        "students/list.html",
        students=students,
        total=total,
        page=page,
        per_page=per_page,
        keyword=keyword,
        class_id=class_id,
        gender=gender,
        classes=classes,
    )


@students_bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("students.manage")
def create_student():
    classes = Classroom.query.order_by(Classroom.name.asc()).all()
    if request.method == "POST":
        form = request.form
        student_number = form.get("student_number", "").strip()
        name = form.get("name", "").strip()
        gender = form.get("gender", "").strip()
        class_id = form.get("class_id", type=int)
        email = form.get("email", "").strip()
        phone = form.get("phone", "").strip()
        address = form.get("address", "").strip() or None
        guardian_name = form.get("guardian_name", "").strip() or None
        guardian_phone = form.get("guardian_phone", "").strip() or None
        avatar = request.files.get("avatar")
        dob_raw = form.get("date_of_birth", "").strip()

        errors: list[str] = []
        if not student_number:
            errors.append("学号不能为空")
        elif Student.query.filter_by(student_number=student_number).first():
            errors.append("学号已存在")
        if not name:
            errors.append("姓名不能为空")
        if not gender:
            errors.append("性别不能为空")
        if not class_id:
            errors.append("请选择班级")
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
            return render_template("students/form.html", classes=classes)

        avatar_path = None
        if avatar and avatar.filename:
            avatar_path = save_uploaded_file(avatar, subdir="avatars")

        student = Student(
            student_number=student_number,
            name=name,
            gender=gender,
            date_of_birth=date_of_birth,
            class_id=class_id,
            email=email,
            phone=phone,
            address=address,
            guardian_name=guardian_name,
            guardian_phone=guardian_phone,
            avatar_path=avatar_path,
        )
        db.session.add(student)
        db.session.commit()
        log_operation(current_user.id, "create", "student", f"创建学生 {student.name}")
        flash("学生信息创建成功", "success")
        return redirect(url_for("students.list_students"))

    return render_template("students/form.html", classes=classes)


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("students.manage")
def edit_student(student_id: int):
    student = Student.query.get_or_404(student_id)
    classes = Classroom.query.order_by(Classroom.name.asc()).all()

    if request.method == "POST":
        form = request.form
        student_number = form.get("student_number", "").strip()
        name = form.get("name", "").strip()
        gender = form.get("gender", "").strip()
        class_id = form.get("class_id", type=int)
        email = form.get("email", "").strip()
        phone = form.get("phone", "").strip()
        address = form.get("address", "").strip() or None
        guardian_name = form.get("guardian_name", "").strip() or None
        guardian_phone = form.get("guardian_phone", "").strip() or None
        avatar = request.files.get("avatar")
        dob_raw = form.get("date_of_birth", "").strip()

        errors: list[str] = []
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
        if not class_id:
            errors.append("请选择班级")
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
            return render_template("students/form.html", student=student, classes=classes)

        if avatar and avatar.filename:
            student.avatar_path = save_uploaded_file(avatar, subdir="avatars")

        student.student_number = student_number
        student.name = name
        student.gender = gender
        student.class_id = class_id
        student.email = email
        student.phone = phone
        student.address = address
        student.guardian_name = guardian_name
        student.guardian_phone = guardian_phone
        student.date_of_birth = date_of_birth

        db.session.commit()
        log_operation(current_user.id, "update", "student", f"更新学生 {student.name}")
        flash("学生信息更新成功", "success")
        return redirect(url_for("students.list_students"))

    return render_template("students/form.html", student=student, classes=classes)


@students_bp.route("/<int:student_id>")
@login_required
@permission_required("students.manage")
def student_detail(student_id: int):
    student = Student.query.get_or_404(student_id)
    return render_template("students/detail.html", student=student)


@students_bp.route("/<int:student_id>/delete", methods=["POST"])
@login_required
@permission_required("students.manage")
def delete_student(student_id: int):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    log_operation(current_user.id, "delete", "student", f"删除学生 {student.name}")
    flash("学生信息删除成功", "success")
    return redirect(url_for("students.list_students"))


@students_bp.route("/export")
@login_required
@permission_required("students.export")
def export_students() -> Response:
    students = Student.query.all()
    rows = []
    for student in students:
        rows.append(
            {
                "student_number": student.student_number,
                "name": student.name,
                "gender": student.gender,
                "date_of_birth": student.date_of_birth.strftime("%Y-%m-%d"),
                "class_name": student.classroom.name if student.classroom else "",
                "email": student.email,
                "phone": student.phone,
                "address": student.address or "",
            }
        )
    stream = export_students_to_excel(rows)
    return send_file(
        stream,
        as_attachment=True,
        download_name="students.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@students_bp.route("/import", methods=["GET", "POST"])
@login_required
@permission_required("students.import")
def import_students():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("请选择要上传的 Excel 文件", "danger")
            return render_template("students/import.html")
        stored_path = save_uploaded_file(file, subdir="imports")
        try:
            imported_rows = import_students_from_excel(stored_path)
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("students/import.html")

        created = 0
        for row in imported_rows:
            if not row.get("student_number"):
                continue
            if Student.query.filter_by(student_number=row["student_number"]).first():
                continue
            classroom = Classroom.query.filter_by(name=row.get("class_name", "")).first()
            dob_value = row.get("date_of_birth")
            if isinstance(dob_value, datetime):
                date_of_birth = dob_value.date()
            else:
                try:
                    date_of_birth = datetime.strptime(str(dob_value), "%Y-%m-%d").date()
                except ValueError:
                    date_of_birth = datetime.utcnow().date()
            student = Student(
                student_number=str(row.get("student_number", "")).strip(),
                name=str(row.get("name", "")).strip(),
                gender=str(row.get("gender", "")).strip(),
                date_of_birth=date_of_birth,
                class_id=classroom.id if classroom else None,
                email=str(row.get("email", "")).strip(),
                phone=str(row.get("phone", "")).strip(),
                address=str(row.get("address", "")).strip() or None,
            )
            db.session.add(student)
            created += 1
        db.session.commit()
        log_operation(current_user.id, "import", "student", f"导入学生 {created} 条")
        flash(f"成功导入 {created} 条学生信息", "success")
        return redirect(url_for("students.list_students"))

    return render_template("students/import.html")
