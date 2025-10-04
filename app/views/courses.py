from __future__ import annotations

from datetime import datetime, time

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Classroom, Course, CourseSchedule, Student, Teacher
from ..utils import log_operation, permission_required

courses_bp = Blueprint("courses", __name__, url_prefix="/courses")


@courses_bp.route("/")
@login_required
@permission_required("courses.manage")
def list_courses():
    courses = Course.query.order_by(Course.name.asc()).all()
    teachers = Teacher.query.order_by(Teacher.name.asc()).all()
    classes = Classroom.query.order_by(Classroom.name.asc()).all()
    teacher_id = request.args.get("teacher_id", type=int)
    class_id = request.args.get("class_id", type=int)

    query = Course.query
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    if class_id:
        query = query.filter_by(classroom_id=class_id)
    courses = query.order_by(Course.name.asc()).all()

    return render_template(
        "courses/list.html",
        courses=courses,
        teachers=teachers,
        classes=classes,
        teacher_id=teacher_id,
        class_id=class_id,
    )


@courses_bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("courses.manage")
def create_course():
    teachers = Teacher.query.order_by(Teacher.name.asc()).all()
    classes = Classroom.query.order_by(Classroom.name.asc()).all()
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        name = request.form.get("name", "").strip()
        credit = request.form.get("credit", type=float, default=0.0)
        description = request.form.get("description", "").strip() or None
        teacher_id = request.form.get("teacher_id", type=int)
        classroom_id = request.form.get("classroom_id", type=int)

        if not code or not name:
            flash("课程编号和名称不能为空", "danger")
            return render_template("courses/form.html", teachers=teachers, classes=classes)
        if Course.query.filter_by(code=code).first():
            flash("课程编号已存在", "danger")
            return render_template("courses/form.html", teachers=teachers, classes=classes)

        course = Course(
            code=code,
            name=name,
            credit=credit,
            description=description,
            teacher_id=teacher_id,
            classroom_id=classroom_id,
        )
        db.session.add(course)
        db.session.commit()
        log_operation(current_user.id, "create", "course", f"创建课程 {course.name}")
        flash("课程创建成功", "success")
        return redirect(url_for("courses.list_courses"))

    return render_template("courses/form.html", teachers=teachers, classes=classes)


@courses_bp.route("/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("courses.manage")
def edit_course(course_id: int):
    course = Course.query.get_or_404(course_id)
    teachers = Teacher.query.order_by(Teacher.name.asc()).all()
    classes = Classroom.query.order_by(Classroom.name.asc()).all()

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        name = request.form.get("name", "").strip()
        credit = request.form.get("credit", type=float, default=0.0)
        description = request.form.get("description", "").strip() or None
        teacher_id = request.form.get("teacher_id", type=int)
        classroom_id = request.form.get("classroom_id", type=int)

        if not code or not name:
            flash("课程编号和名称不能为空", "danger")
            return render_template("courses/form.html", course=course, teachers=teachers, classes=classes)
        if code != course.code and Course.query.filter_by(code=code).first():
            flash("课程编号已存在", "danger")
            return render_template("courses/form.html", course=course, teachers=teachers, classes=classes)

        course.code = code
        course.name = name
        course.credit = credit
        course.description = description
        course.teacher_id = teacher_id
        course.classroom_id = classroom_id
        db.session.commit()
        log_operation(current_user.id, "update", "course", f"更新课程 {course.name}")
        flash("课程信息更新成功", "success")
        return redirect(url_for("courses.list_courses"))

    return render_template("courses/form.html", course=course, teachers=teachers, classes=classes)


@courses_bp.route("/<int:course_id>")
@login_required
@permission_required("courses.manage")
def course_detail(course_id: int):
    course = Course.query.get_or_404(course_id)
    students = course.students
    schedules = course.schedules
    return render_template("courses/detail.html", course=course, students=students, schedules=schedules)


@courses_bp.route("/<int:course_id>/schedule", methods=["GET", "POST"])
@login_required
@permission_required("courses.manage")
def manage_schedule(course_id: int):
    course = Course.query.get_or_404(course_id)
    if request.method == "POST":
        weekday = request.form.get("weekday", type=int)
        start_time_raw = request.form.get("start_time")
        end_time_raw = request.form.get("end_time")
        location = request.form.get("location", "").strip() or None
        try:
            start_time_obj = datetime.strptime(start_time_raw, "%H:%M").time() if start_time_raw else None
            end_time_obj = datetime.strptime(end_time_raw, "%H:%M").time() if end_time_raw else None
        except ValueError:
            flash("时间格式错误，请使用 HH:MM", "danger")
            return render_template("courses/schedule.html", course=course)

        if weekday is None or start_time_obj is None or end_time_obj is None:
            flash("请完整填写课表信息", "danger")
            return render_template("courses/schedule.html", course=course)

        schedule = CourseSchedule(
            course_id=course.id,
            weekday=weekday,
            start_time=start_time_obj,
            end_time=end_time_obj,
            location=location,
        )
        db.session.add(schedule)
        db.session.commit()
        log_operation(current_user.id, "update", "course_schedule", f"更新课表 {course.name}")
        flash("课表信息已添加", "success")
        return redirect(url_for("courses.manage_schedule", course_id=course.id))

    schedules = course.schedules
    return render_template("courses/schedule.html", course=course, schedules=schedules)


@courses_bp.route("/<int:course_id>/assign", methods=["GET", "POST"])
@login_required
@permission_required("courses.manage")
def assign_students(course_id: int):
    course = Course.query.get_or_404(course_id)
    students = Student.query.order_by(Student.name.asc()).all()
    if request.method == "POST":
        selected_ids = set(map(int, request.form.getlist("student_ids")))
        course.students.clear()
        for student in students:
            if student.id in selected_ids:
                course.students.append(student)
        db.session.commit()
        log_operation(current_user.id, "update", "course", f"调整选课 {course.name}")
        flash("选课学生名单已更新", "success")
        return redirect(url_for("courses.course_detail", course_id=course.id))

    return render_template("courses/assign.html", course=course, students=students)
