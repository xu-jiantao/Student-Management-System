from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import Role, User
from ..utils import generate_token, verify_token

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.before_app_request
def enforce_first_login_password_change():
    if not current_user.is_authenticated:
        return
    allowed = {
        "auth.logout",
        "auth.first_login",
        "auth.first_login_update",
        "static",
    }
    if current_user.first_login and request.endpoint not in allowed:
        return redirect(url_for("auth.first_login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("用户名或密码错误", "danger")
            return render_template("auth/login.html")
        if not user.is_active:
            flash("账号已被禁用", "danger")
            return render_template("auth/login.html")

        login_user(user, remember="remember" in request.form)
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        next_url = request.args.get("next") or url_for("dashboard.index")
        return redirect(next_url)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("您已安全退出系统", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        role_name = request.form.get("role", "学生")

        if not username or not email or not password:
            flash("请完整填写注册信息", "danger")
            return render_template("auth/register.html")
        if password != confirm:
            flash("两次输入的密码不一致", "danger")
            return render_template("auth/register.html")
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("用户名或邮箱已被占用", "danger")
            return render_template("auth/register.html")

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash("所选角色不存在，请联系管理员", "danger")
            return render_template("auth/register.html")

        user = User(username=username, email=email, first_login=True)
        user.set_password(password)
        user.roles.append(role)
        db.session.add(user)
        db.session.commit()
        flash("注册成功，请登录", "success")
        return redirect(url_for("auth.login"))

    roles = Role.query.order_by(Role.name.asc()).all()
    return render_template("auth/register.html", roles=roles)


@auth_bp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("未找到对应邮箱的用户", "danger")
            return render_template("auth/forgot_password.html")

        token = generate_token(user.id, purpose="password-reset")
        user.reset_token = token
        db.session.commit()
        flash("重置链接已生成，请复制以下令牌并访问重置页面", "info")
        return render_template("auth/forgot_password.html", token=token)

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token") or request.form.get("token")
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if password != confirm:
            flash("两次输入的密码不一致", "danger")
            return render_template("auth/reset_password.html", token=token)
        user_id = verify_token(token, max_age=3600, purpose="password-reset") if token else None
        user = User.query.get(user_id) if user_id else None
        if not user or user.reset_token != token:
            flash("重置链接无效或已过期", "danger")
            return render_template("auth/reset_password.html")
        user.set_password(password)
        user.reset_token = None
        user.first_login = False
        db.session.commit()
        flash("密码重置成功，请使用新密码登录", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/first-login", methods=["GET", "POST"])
@login_required
def first_login():
    if not current_user.first_login:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if password != confirm:
            flash("两次输入的密码不一致", "danger")
            return render_template("auth/first_login.html")
        current_user.set_password(password)
        current_user.first_login = False
        db.session.commit()
        flash("密码修改成功", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/first_login.html")
