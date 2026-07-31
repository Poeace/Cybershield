from __future__ import annotations

from datetime import datetime

from flask import render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user

from app.utils.captcha import generate_captcha_text


from app.blueprints.admin import admin_bp
from app.config import Config
from app.extensions import db
from app.models import User, ContactMessage, LoginLog, ModuleUsage


# Simple admin auth (admin account stored in config, not DB)
# For production, store admin users in DB and use hashing.


# NOTE: Admin access is protected via a Flask session flag set in admin_login.
# No user-based is_admin attribute is currently stored in the DB.



@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        captcha = (request.form.get("captcha") or "").strip().upper()
        expected = (session.get("captcha", "") or "").strip().upper()
        if not captcha or not expected or captcha != expected:
            flash("Invalid captcha.", "danger")
            return redirect(url_for("admin.admin_login"))

        username = (request.form.get("username") or "").strip()

        password = request.form.get("password") or ""

        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            # Emulate an admin session using a special flag on current_user.
            # Since we reuse Flask-Login for users, we'll store admin auth in session via cookie flag.
           

            session["cybershield_admin"] = True
            return redirect(url_for("admin.admin_dashboard"))

        flash("Invalid admin credentials.", "danger")
    session["captcha"] = generate_captcha_text(6)
    return render_template("admin/admin_login.html", captcha_text=session["captcha"])



@admin_bp.route("/dashboard")
def admin_dashboard():
    from flask import session

    if not session.get("cybershield_admin"):
        flash("Admin login required.", "warning")
        return redirect(url_for("admin.admin_login"))

    total_users = User.query.count()
    total_logins = LoginLog.query.count()
    total_messages = ContactMessage.query.count()

    module_usage = (
        db.session.query(ModuleUsage.module_name, db.func.count(ModuleUsage.id))
        .group_by(ModuleUsage.module_name)
        .all()
    )

    last_login_logs = LoginLog.query.order_by(LoginLog.login_time.desc()).limit(10).all()
    users = User.query.order_by(User.registration_date.desc()).limit(50).all()
    messages = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).limit(50).all()

    return render_template(
        "admin/admin_dashboard.html",
        total_users=total_users,
        total_logins=total_logins,
        total_messages=total_messages,
        module_usage=module_usage,
        users=users,
        messages=messages,
        last_login_logs=last_login_logs,
    )


@admin_bp.route("/logout")
def admin_logout():
    from flask import session

    session.pop("cybershield_admin", None)
    return redirect(url_for("main.home"))

