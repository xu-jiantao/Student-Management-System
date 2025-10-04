from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_, case

from ..extensions import db
from ..models import Announcement, TodoItem
from ..utils import save_uploaded_file

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/info", methods=["GET", "POST"])
@login_required
def info():
    if request.method == "POST":
        current_user.email = request.form.get("email", "").strip()
        current_user.phone = request.form.get("phone", "").strip()
        avatar = request.files.get("avatar")
        if avatar and avatar.filename:
            path = save_uploaded_file(avatar, subdir="avatars")
            current_user.avatar_path = path
        db.session.commit()
        flash("个人信息已更新", "success")
        return redirect(url_for("profile.info"))

    recent_todos = (
        TodoItem.query.filter_by(user_id=current_user.id)
        .order_by(
            TodoItem.is_completed.asc(),
            case((TodoItem.due_date.is_(None), 1), else_=0),
            TodoItem.due_date.asc(),
        )
        .limit(5)
        .all()
    )
    total_todos = TodoItem.query.filter_by(user_id=current_user.id).count()
    completed_todos = TodoItem.query.filter_by(user_id=current_user.id, is_completed=True).count()

    role_names = [role.name for role in current_user.roles]
    announcement_query = Announcement.query
    if role_names:
        conditions = [Announcement.target_roles.ilike(f"%{name}%") for name in role_names]
        announcement_query = announcement_query.filter(
            or_(Announcement.target_roles == "all", *conditions)
        )
    else:
        announcement_query = announcement_query.filter(Announcement.target_roles == "all")

    recent_announcements = (
        announcement_query.order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "profile/info.html",
        recent_todos=recent_todos,
        total_todos=total_todos,
        completed_todos=completed_todos,
        recent_announcements=recent_announcements,
    )


@profile_bp.route("/password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not current_user.check_password(old_password):
            flash("原密码错误", "danger")
            return render_template("profile/password.html")
        if new_password != confirm_password:
            flash("两次输入的密码不一致", "danger")
            return render_template("profile/password.html")
        current_user.set_password(new_password)
        db.session.commit()
        flash("密码修改成功", "success")
        return redirect(url_for("profile.info"))

    return render_template("profile/password.html")


@profile_bp.route("/messages", methods=["GET", "POST"])
@login_required
def messages():
    if request.method == "POST":
        message_id = request.form.get("message_id", type=int)
        action = request.form.get("action")
        message = next((msg for msg in current_user.messages if msg.id == message_id), None)
        if message and action == "mark_read":
            message.is_read = True
            db.session.commit()
        return redirect(url_for("profile.messages"))

    unread = [message for message in current_user.messages if not message.is_read]
    read = [message for message in current_user.messages if message.is_read]
    return render_template("profile/messages.html", unread=unread, read=read)
