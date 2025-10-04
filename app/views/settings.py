from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Blueprint, Response, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import DataBackup, OperationLog, Role, SystemSetting, User
from ..utils import log_operation, permission_required

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/users", methods=["GET", "POST"])
@login_required
@permission_required("settings.manage")
def manage_users():
    users = User.query.order_by(User.username.asc()).all()
    roles = Role.query.order_by(Role.name.asc()).all()
    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        raw_role_ids = request.form.getlist("role_ids")
        role_ids: list[int] = []
        for value in raw_role_ids:
            try:
                role_ids.append(int(value))
            except (TypeError, ValueError):
                continue
        user = User.query.get_or_404(user_id)
        user.roles = [Role.query.get(role_id) for role_id in role_ids if Role.query.get(role_id)]
        db.session.commit()
        log_operation(current_user.id, "update", "user_roles", f"更新用户 {user.username} 角色")
        flash("角色已更新", "success")
        return redirect(url_for("settings.manage_users"))
    return render_template("settings/users.html", users=users, roles=roles)


@settings_bp.route("/parameters", methods=["GET", "POST"])
@login_required
@permission_required("settings.manage")
def parameters():
    if request.method == "POST":
        key = request.form.get("key", "").strip()
        value = request.form.get("value", "")
        description = request.form.get("description", "").strip() or None
        if not key:
            flash("参数键不能为空", "danger")
        else:
            setting = SystemSetting.query.get(key)
            if setting:
                setting.value = value
                setting.description = description
            else:
                db.session.add(SystemSetting(key=key, value=value, description=description))
            db.session.commit()
            log_operation(current_user.id, "update", "system_setting", f"保存参数 {key}")
            flash("参数已保存", "success")
        return redirect(url_for("settings.parameters"))

    settings = SystemSetting.query.order_by(SystemSetting.key.asc()).all()
    return render_template("settings/parameters.html", settings=settings)


@settings_bp.route("/backups", methods=["GET", "POST"])
@login_required
@permission_required("settings.manage")
def backups():
    backups_dir = Path("backups")
    backups_dir.mkdir(exist_ok=True)
    if request.method == "POST":
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"backup_{timestamp}.sql"
        file_path = backups_dir / filename
        file_path.write_text("-- mock backup file --", encoding="utf-8")
        backup = DataBackup(
            filename=filename,
            file_path=str(file_path),
            created_by=request.form.get("user_id", type=int) or None,
        )
        db.session.add(backup)
        db.session.commit()
        log_operation(current_user.id, "create", "backup", filename)
        flash("备份已创建", "success")
        return redirect(url_for("settings.backups"))

    backups_list = DataBackup.query.order_by(DataBackup.created_at.desc()).all()
    return render_template("settings/backups.html", backups=backups_list)


@settings_bp.route("/backups/<int:backup_id>/download")
@login_required
@permission_required("settings.manage")
def download_backup(backup_id: int) -> Response:
    backup = DataBackup.query.get_or_404(backup_id)
    return send_file(backup.file_path, as_attachment=True, download_name=backup.filename)


@settings_bp.route("/logs")
@login_required
@permission_required("settings.manage")
def logs():
    logs_records = OperationLog.query.order_by(OperationLog.created_at.desc()).limit(200).all()
    return render_template("settings/logs.html", logs=logs_records)
