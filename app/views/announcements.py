from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Announcement, Role
from ..utils import log_operation, permission_required


announcements_bp = Blueprint("announcements", __name__, url_prefix="/announcements")


@announcements_bp.route("/")
@login_required
def list_announcements():
    announcements = Announcement.query.order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()
    return render_template("announcements/list.html", announcements=announcements)


@announcements_bp.route("/<int:announcement_id>")
@login_required
def announcement_detail(announcement_id: int):
    announcement = Announcement.query.get_or_404(announcement_id)
    return render_template("announcements/detail.html", announcement=announcement)


@announcements_bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("announcements.manage")
def create_announcement():
    roles = Role.query.order_by(Role.name.asc()).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        target_roles = request.form.getlist("target_roles")
        is_pinned = bool(request.form.get("is_pinned"))

        if not title or not content:
            flash("标题和内容不能为空", "danger")
            return render_template("announcements/form.html", roles=roles)

        announcement = Announcement(
            title=title,
            content=content,
            author_id=current_user.id,
            target_roles=",".join(target_roles) if target_roles else "all",
            is_pinned=is_pinned,
        )
        db.session.add(announcement)
        db.session.commit()
        log_operation(current_user.id, "create", "announcement", f"发布公告 {announcement.title}")
        flash("公告发布成功", "success")
        return redirect(url_for("announcements.list_announcements"))

    return render_template("announcements/form.html", roles=roles)
