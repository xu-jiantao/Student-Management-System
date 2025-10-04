from flask import Flask
from flask_login import current_user

from .extensions import db, login_manager


def create_app() -> Flask:
    """Application factory for the student信息管理系统 with modular blueprints."""
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize shared extensions
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from . import models  # noqa: F401 (ensure models are registered)

        # Register blueprints lazily to avoid circular imports
        from .views.auth import auth_bp
        from .views.dashboard import dashboard_bp
        from .views.students import students_bp
        from .views.classes import classes_bp
        from .views.teachers import teachers_bp
        from .views.courses import courses_bp
        from .views.grades import grades_bp
        from .views.attendance import attendance_bp
        from .views.announcements import announcements_bp
        from .views.profile import profile_bp
        from .views.settings import settings_bp
        from .api import api_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(students_bp)
        app.register_blueprint(classes_bp)
        app.register_blueprint(teachers_bp)
        app.register_blueprint(courses_bp)
        app.register_blueprint(grades_bp)
        app.register_blueprint(attendance_bp)
        app.register_blueprint(announcements_bp)
        app.register_blueprint(profile_bp)
        app.register_blueprint(settings_bp)
        app.register_blueprint(api_bp, url_prefix="/api")

        @app.context_processor
        def inject_navigation():
            menu_definition = [
                {
                    "label": "仪表盘",
                    "endpoint": "dashboard.index",
                    "icon": "ri-dashboard-line",
                    "permission": "dashboard.view",
                },
                {
                    "label": "学生管理",
                    "endpoint": "students.list_students",
                    "icon": "ri-user-3-line",
                    "permission": "students.manage",
                },
                {
                    "label": "班级管理",
                    "endpoint": "classes.list_classes",
                    "icon": "ri-team-line",
                    "permission": "classes.manage",
                },
                {
                    "label": "教师管理",
                    "endpoint": "teachers.list_teachers",
                    "icon": "ri-user-star-line",
                    "permission": "teachers.manage",
                },
                {
                    "label": "课程中心",
                    "icon": "ri-booklet-line",
                    "permission": "courses.manage",
                    "children": [
                        {
                            "label": "课程列表",
                            "endpoint": "courses.list_courses",
                            "permission": "courses.manage",
                        },
                        {
                            "label": "新增课程",
                            "endpoint": "courses.create_course",
                            "permission": "courses.manage",
                        },
                    ],
                },
                {
                    "label": "成绩管理",
                    "icon": "ri-bar-chart-2-line",
                    "permission": "grades.manage",
                    "children": [
                        {
                            "label": "成绩录入",
                            "endpoint": "grades.entry",
                            "permission": "grades.manage",
                        },
                        {
                            "label": "成绩查询",
                            "endpoint": "grades.search",
                            "permission": "grades.manage",
                        },
                        {
                            "label": "成绩统计",
                            "endpoint": "grades.statistics",
                            "permission": "grades.manage",
                        },
                    ],
                },
                {
                    "label": "考勤管理",
                    "icon": "ri-time-line",
                    "permission": "attendance.manage",
                    "children": [
                        {
                            "label": "考勤签到",
                            "endpoint": "attendance.check_attendance",
                            "permission": "attendance.manage",
                        },
                        {
                            "label": "考勤统计",
                            "endpoint": "attendance.statistics",
                            "permission": "attendance.manage",
                        },
                        {
                            "label": "请假管理",
                            "endpoint": "attendance.leave_requests",
                            "permission": "attendance.manage",
                        },
                    ],
                },
                {
                    "label": "通知公告",
                    "endpoint": "announcements.list_announcements",
                    "icon": "ri-notification-3-line",
                    "permission": None,
                },
                {
                    "label": "个人中心",
                    "icon": "ri-user-settings-line",
                    "permission": None,
                    "children": [
                        {
                            "label": "账号信息",
                            "endpoint": "profile.info",
                            "permission": None,
                        },
                        {
                            "label": "修改密码",
                            "endpoint": "profile.change_password",
                            "permission": None,
                        },
                        {
                            "label": "消息通知",
                            "endpoint": "profile.messages",
                            "permission": None,
                        },
                    ],
                },
                {
                    "label": "系统设置",
                    "icon": "ri-settings-3-line",
                    "permission": "settings.manage",
                    "children": [
                        {
                            "label": "用户权限",
                            "endpoint": "settings.manage_users",
                            "permission": "settings.manage",
                        },
                        {
                            "label": "系统参数",
                            "endpoint": "settings.parameters",
                            "permission": "settings.manage",
                        },
                        {
                            "label": "数据备份",
                            "endpoint": "settings.backups",
                            "permission": "settings.manage",
                        },
                        {
                            "label": "操作日志",
                            "endpoint": "settings.logs",
                            "permission": "settings.manage",
                        },
                    ],
                },
            ]

            def filter_items(items):
                filtered = []
                for item in items:
                    perm = item.get("permission")
                    if perm and (not current_user.is_authenticated or not current_user.has_permission(perm)):
                        continue
                    children = item.get("children")
                    new_item = dict(item)
                    if children:
                        allowed_children = filter_items(children)
                        if not allowed_children:
                            continue
                        new_item["children"] = allowed_children
                    filtered.append(new_item)
                return filtered

            return {"nav_menu": filter_items(menu_definition)}

        db.create_all()

        from .models import create_default_roles, ensure_admin_user

        create_default_roles()
        ensure_admin_user()

    return app
