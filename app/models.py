from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
)


role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)


course_students = db.Table(
    "course_students",
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), primary_key=True),
    db.Column("student_id", db.Integer, db.ForeignKey("students.id"), primary_key=True),
)


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    permissions = db.relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
    )

    def has_permission(self, code: str) -> bool:
        return any(permission.code == code for permission in self.permissions)


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="menu")

    roles = db.relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
    )


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_path = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    first_login = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime)
    reset_token = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship("Role", secondary=user_roles, backref=db.backref("users", lazy="dynamic"))

    student_profile = db.relationship("Student", back_populates="user", uselist=False)
    teacher_profile = db.relationship("Teacher", back_populates="user", uselist=False)

    todos = db.relationship("TodoItem", back_populates="user", cascade="all, delete-orphan")
    messages = db.relationship("SystemMessage", back_populates="user", cascade="all, delete-orphan")
    logs = db.relationship("OperationLog", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name: str) -> bool:
        return any(role.name == role_name for role in self.roles)

    def has_permission(self, code: str) -> bool:
        return any(role.has_permission(code) for role in self.roles)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    if user_id and user_id.isdigit():
        return User.query.get(int(user_id))
    return None


class Classroom(db.Model):
    __tablename__ = "classrooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    grade_level = db.Column(db.String(20))
    description = db.Column(db.String(255))
    head_teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))

    head_teacher = db.relationship("Teacher", back_populates="managed_classes")
    students = db.relationship("Student", back_populates="classroom", cascade="all, delete-orphan")
    courses = db.relationship("Course", back_populates="classroom")


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classrooms.id"))
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255))
    guardian_name = db.Column(db.String(100))
    guardian_phone = db.Column(db.String(20))
    avatar_path = db.Column(db.String(255))
    enrollment_date = db.Column(db.Date, default=date.today)

    user = db.relationship("User", back_populates="student_profile")
    classroom = db.relationship("Classroom", back_populates="students")
    courses = db.relationship("Course", secondary=course_students, back_populates="students")
    grades = db.relationship("GradeRecord", back_populates="student", cascade="all, delete-orphan")
    attendance_records = db.relationship(
        "AttendanceRecord", back_populates="student", cascade="all, delete-orphan"
    )
    leave_requests = db.relationship(
        "LeaveRequest", back_populates="student", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "student_number": self.student_number,
            "name": self.name,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth.isoformat(),
            "class_id": self.class_id,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
        }


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    employee_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    professional_title = db.Column(db.String(100))
    hire_date = db.Column(db.Date)

    user = db.relationship("User", back_populates="teacher_profile")
    courses = db.relationship("Course", back_populates="teacher")
    managed_classes = db.relationship("Classroom", back_populates="head_teacher")


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    credit = db.Column(db.Float, default=0)
    description = db.Column(db.Text)
    classroom_id = db.Column(db.Integer, db.ForeignKey("classrooms.id"))
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))

    classroom = db.relationship("Classroom", back_populates="courses")
    teacher = db.relationship("Teacher", back_populates="courses")
    students = db.relationship("Student", secondary=course_students, back_populates="courses")
    schedules = db.relationship("CourseSchedule", back_populates="course", cascade="all, delete-orphan")
    grades = db.relationship("GradeRecord", back_populates="course", cascade="all, delete-orphan")
    attendance_records = db.relationship(
        "AttendanceRecord", back_populates="course", cascade="all, delete-orphan"
    )


class CourseSchedule(db.Model):
    __tablename__ = "course_schedules"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 0=Monday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(100))

    course = db.relationship("Course", back_populates="schedules")


class GradeRecord(db.Model):
    __tablename__ = "grade_records"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    term = db.Column(db.String(20), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    remark = db.Column(db.String(255))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="grades")
    course = db.relationship("Course", back_populates="grades")


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    record_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False)  # Present/Absent/Leave
    remarks = db.Column(db.String(255))

    student = db.relationship("Student", back_populates="attendance_records")
    course = db.relationship("Course", back_populates="attendance_records")


class LeaveRequest(db.Model):
    __tablename__ = "leave_requests"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")
    approver_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

    student = db.relationship("Student", back_populates="leave_requests")
    approver = db.relationship("User", foreign_keys=[approver_id])


class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    target_roles = db.Column(db.String(255), default="all")
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship("User")


class TodoItem(db.Model):
    __tablename__ = "todo_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    due_date = db.Column(db.Date)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="todos")


class SystemMessage(db.Model):
    __tablename__ = "system_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="messages")


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))


class DataBackup(db.Model):
    __tablename__ = "data_backups"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User")


class OperationLog(db.Model):
    __tablename__ = "operation_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100))
    description = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="logs")


class UploadedFile(db.Model):
    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    file_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship("User")


def default_permissions() -> list[Permission]:
    permissions: list[Permission] = []
    permission_definitions = [
        ("dashboard.view", "查看仪表盘", "menu"),
        ("students.manage", "学生管理", "menu"),
        ("classes.manage", "班级管理", "menu"),
        ("teachers.manage", "教师管理", "menu"),
        ("courses.manage", "课程管理", "menu"),
        ("grades.manage", "成绩管理", "menu"),
        ("attendance.manage", "考勤管理", "menu"),
        ("announcements.manage", "公告管理", "menu"),
        ("profile.view", "个人中心", "menu"),
        ("settings.manage", "系统设置", "menu"),
        ("students.export", "学生导出", "action"),
        ("students.import", "学生导入", "action"),
        ("grades.export", "成绩导出", "action"),
    ]
    for code, name, category in permission_definitions:
        permission = Permission(code=code, name=name, category=category)
        permissions.append(permission)
    return permissions


def create_default_roles() -> None:
    if Role.query.count() > 0:
        return

    admin_role = Role(name="管理员", description="系统管理员")
    teacher_role = Role(name="教师", description="教师用户")
    student_role = Role(name="学生", description="学生用户")

    perms = default_permissions()
    for perm in perms:
        db.session.add(perm)

    admin_role.permissions.extend(perms)
    teacher_role.permissions.extend(
        [
            perm
            for perm in perms
            if perm.code
            in {
                "dashboard.view",
                "students.manage",
                "classes.manage",
                "courses.manage",
                "grades.manage",
                "attendance.manage",
                "announcements.manage",
                "profile.view",
                "students.import",
                "students.export",
                "grades.export",
            }
        ]
    )
    student_role.permissions.extend(
        [
            perm
            for perm in perms
            if perm.code in {"dashboard.view", "profile.view", "announcements.manage"}
        ]
    )

    db.session.add_all([admin_role, teacher_role, student_role])
    db.session.commit()


def ensure_admin_user() -> None:
    if User.query.filter_by(username="admin").first():
        return

    admin_role = Role.query.filter_by(name="管理员").first()
    if not admin_role:
        create_default_roles()
        admin_role = Role.query.filter_by(name="管理员").first()

    if not admin_role:
        return

    user = User(username="admin", email="admin@example.com", is_active=True, first_login=True)
    user.set_password("Admin@123")
    user.roles.append(admin_role)
    db.session.add(user)
    db.session.commit()
