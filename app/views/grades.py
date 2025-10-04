from __future__ import annotations

from collections import defaultdict

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Classroom, Course, GradeRecord, Student
from ..utils import export_grades_to_excel, log_operation, permission_required


grades_bp = Blueprint("grades", __name__, url_prefix="/grades")


@grades_bp.route("/entry", methods=["GET", "POST"])
@login_required
@permission_required("grades.manage")
def entry():
    classes = Classroom.query.order_by(Classroom.name.asc()).all()
    courses = Course.query.order_by(Course.name.asc()).all()

    selected_class_id = request.values.get("class_id", type=int)
    selected_course_id = request.values.get("course_id", type=int)
    term = request.values.get("term", "2023-2024")
    assessment_type = request.values.get("assessment_type", "期末")

    students = []
    if selected_class_id:
        students = Student.query.filter_by(class_id=selected_class_id).order_by(Student.student_number.asc()).all()

    if request.method == "POST" and request.form.get("action") == "save":
        for student in students:
            field_name = f"score_{student.id}"
            score_value = request.form.get(field_name)
            if score_value is None:
                continue
            try:
                score = float(score_value)
            except ValueError:
                flash(f"学生 {student.name} 的成绩格式不正确", "danger")
                continue

            record = GradeRecord.query.filter_by(
                student_id=student.id,
                course_id=selected_course_id,
                term=term,
                assessment_type=assessment_type,
            ).first()
            if record:
                record.score = score
            else:
                record = GradeRecord(
                    student_id=student.id,
                    course_id=selected_course_id,
                    term=term,
                    assessment_type=assessment_type,
                    score=score,
                )
                db.session.add(record)
        db.session.commit()
        log_operation(current_user.id, "update", "grade", f"录入成绩 课程 {selected_course_id}")
        flash("成绩已保存", "success")
        return redirect(url_for("grades.entry", class_id=selected_class_id, course_id=selected_course_id, term=term, assessment_type=assessment_type))

    return render_template(
        "grades/entry.html",
        classes=classes,
        courses=courses,
        students=students,
        selected_class_id=selected_class_id,
        selected_course_id=selected_course_id,
        term=term,
        assessment_type=assessment_type,
    )


@grades_bp.route("/search")
@login_required
@permission_required("grades.manage")
def search():
    classes = Classroom.query.order_by(Classroom.name.asc()).all()
    courses = Course.query.order_by(Course.name.asc()).all()

    selected_class_id = request.args.get("class_id", type=int)
    selected_course_id = request.args.get("course_id", type=int)
    term = request.args.get("term", "")
    keyword = request.args.get("q", "").strip()

    query = GradeRecord.query.join(Student).join(Course)
    if selected_class_id:
        query = query.join(Classroom, Student.class_id == Classroom.id).filter(Classroom.id == selected_class_id)
    if selected_course_id:
        query = query.filter(GradeRecord.course_id == selected_course_id)
    if term:
        query = query.filter(GradeRecord.term == term)
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            (Student.name.ilike(like_pattern))
            | (Student.student_number.ilike(like_pattern))
            | (Course.name.ilike(like_pattern))
        )

    results = query.order_by(GradeRecord.recorded_at.desc()).all()

    return render_template(
        "grades/search.html",
        results=results,
        classes=classes,
        courses=courses,
        selected_class_id=selected_class_id,
        selected_course_id=selected_course_id,
        term=term,
        keyword=keyword,
    )


@grades_bp.route("/statistics")
@login_required
@permission_required("grades.manage")
def statistics():
    course_stats_raw = (
        db.session.query(Course.name, db.func.avg(GradeRecord.score), db.func.max(GradeRecord.score))
        .join(GradeRecord, GradeRecord.course_id == Course.id)
        .group_by(Course.name)
        .order_by(Course.name.asc())
        .all()
    )
    course_stats = [
        (name, float(avg or 0), float(max_score or 0)) for name, avg, max_score in course_stats_raw
    ]

    class_stats = defaultdict(list)
    records = (
        db.session.query(Classroom.name, GradeRecord.score)
        .join(Student, Student.id == GradeRecord.student_id)
        .join(Classroom, Classroom.id == Student.class_id)
        .all()
    )
    for class_name, score in records:
        class_stats[class_name].append(score)

    class_averages = [
        (class_name, float(sum(scores) / len(scores)) if scores else 0.0)
        for class_name, scores in class_stats.items()
    ]
    class_averages.sort(key=lambda item: item[0])

    return render_template(
        "grades/statistics.html",
        course_stats=course_stats,
        class_averages=class_averages,
    )


@grades_bp.route("/export")
@login_required
@permission_required("grades.export")
def export():
    records = (
        db.session.query(
            Student.student_number,
            Student.name,
            Course.name,
            GradeRecord.term,
            GradeRecord.assessment_type,
            GradeRecord.score,
            GradeRecord.recorded_at,
        )
        .join(Student, Student.id == GradeRecord.student_id)
        .join(Course, Course.id == GradeRecord.course_id)
        .all()
    )
    rows = []
    for student_number, student_name, course_name, term, assessment_type, score, recorded_at in records:
        rows.append(
            {
                "student_number": student_number,
                "student_name": student_name,
                "course": course_name,
                "term": term,
                "assessment_type": assessment_type,
                "score": score,
                "recorded_at": recorded_at.strftime("%Y-%m-%d %H:%M"),
            }
        )
    stream = export_grades_to_excel(rows)
    return send_file(
        stream,
        as_attachment=True,
        download_name="grades.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
