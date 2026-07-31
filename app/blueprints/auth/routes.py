from __future__ import annotations
import random
from flask_mail import Message
from app.extensions import mail




from datetime import datetime

from flask import flash, redirect, render_template, request, url_for, session

from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from email_validator import EmailNotValidError, validate_email

import random


from app.blueprints.auth import auth_bp
from app.extensions import db
from app.models import ContactMessage, LoginLog, PasswordOTP, User
from app.utils.captcha import generate_captcha_text










def _log_login(username: str | None, status: str) -> None:

    db.session.add(
        LoginLog(username=username, status=status, login_time=datetime.utcnow())
    )
    db.session.commit()



@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Captcha
        captcha = (request.form.get("captcha") or "").strip().upper()

        expected = (session.get("captcha", "") or "").strip().upper()
        if not captcha or not expected or captcha != expected:
            flash("Invalid captcha.", "danger")
            return redirect(url_for("auth.register"))

        full_name = (request.form.get("full_name") or "").strip()

        email = (request.form.get("email") or "").strip().lower()
        username = (request.form.get("username") or "").strip()
        phone_number = (request.form.get("phone_number") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""


        if (
            not full_name
            or not email
            or not username
            or not phone_number
            or not password
            or not confirm_password
        ):
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))


        try:
            validate_email(email)
        except EmailNotValidError:
            flash("Invalid email address.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "warning")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("auth.register"))

        password_hash = generate_password_hash(password)
        user = User(
            full_name=full_name,
            email=email,
            username=username,
            phone_number=phone_number,
            password_hash=password_hash,
            registration_date=datetime.utcnow(),
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration Successful", "success")
        return redirect(url_for("auth.login"))

    session["captcha"] = generate_captcha_text(6)
    return render_template("auth/register.html", captcha_text=session["captcha"])



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        captcha = (request.form.get("captcha") or "").strip().upper()
        expected = (session.get("captcha", "") or "").strip().upper()
        if not captcha or not expected or captcha != expected:
            flash("Invalid captcha.", "danger")
            return redirect(url_for("auth.login"))

        user_or_email = (request.form.get("username_email") or "").strip()

        password = request.form.get("password") or ""

        user = User.query.filter(
            (User.username == user_or_email) | (User.email == user_or_email.lower())
        ).first()

        if not user or not check_password_hash(user.password_hash, password):
            _log_login(user_or_email, "failed")
            flash("Invalid credentials.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        _log_login(user.username, "success")
        return redirect(url_for("modules.dashboard"))

    session["captcha"] = generate_captcha_text(6)
    return render_template("auth/login.html", captcha_text=session["captcha"])



@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        user_or_email = (request.form.get("username_email") or "").strip()
        user = User.query.filter(
            (User.username == user_or_email)
            | (User.email == user_or_email.lower())
        ).first()

        if not user:
            flash("If the account exists, an OTP will be sent.", "info")
            return redirect(url_for("auth.forgot_password"))

        # Demo OTP: generate and (in real app) email it to user's registered email.
        otp_code = f"{random.randint(0, 999999):06d}" 

        otp_lifetime_minutes = 10
        expires_at = datetime.utcnow()
        from datetime import timedelta

        expires_at = expires_at + timedelta(minutes=otp_lifetime_minutes)

        db.session.query(PasswordOTP).filter(
            PasswordOTP.user_id == user.user_id
        ).delete()

        otp = PasswordOTP(
            user_id=user.user_id,
            otp_code=otp_code,
            expires_at=expires_at,
        )
        db.session.add(otp)
        db.session.commit()

        msg = Message(
            subject="CyberShield Password Reset OTP",
            recipients=[user.email]
        )
        msg.body = f"""
        Hello {user.full_name},

        Your OTP for resetting your CyberShield account password is:

        {otp_code}

        This OTP is valid for 10 minutes.

        If you did not request this, please ignore this email.

        Regards,
        CyberShield Team
        """

        mail.send(msg)

        # Demo: show OTP in server console instead of sending email.
        # print(f"[CyberShield] Password reset OTP for {user.email} (user_id={user.user_id}): {otp_code}")

        # flash(
        #     "OTP generated. (Demo) Check server console for the OTP.",
        #     "success",
        # )

        flash(
            "OTP has been sent to your registered email.",
            "success",
        )
        
        return redirect(url_for("auth.reset_password", user_id=user.user_id))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "GET":
        return render_template("auth/reset_password.html", user_id=request.args.get("user_id"))

    user_id = request.form.get("user_id")

    otp_code = (request.form.get("otp") or "").strip()
    new_password = request.form.get("new_password") or ""
    confirm_new_password = request.form.get("confirm_new_password") or ""

    if not user_id or not otp_code or not new_password or not confirm_new_password:
        flash("All fields are required.", "danger")
        return redirect(url_for("auth.forgot_password"))


    if new_password != confirm_new_password:

        flash("Passwords do not match.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        flash("Invalid request.", "danger")
        return redirect(url_for("auth.forgot_password"))

    otp = PasswordOTP.query.filter_by(user_id=user.user_id, otp_code=otp_code).first()

    from datetime import datetime as dt

    if not otp or otp.expires_at < dt.utcnow():
        flash("Invalid or expired OTP.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user.password_hash = generate_password_hash(new_password)
    db.session.add(user)
    db.session.delete(otp)
    db.session.commit()

    flash("Password updated successfully.", "success")
    return redirect(url_for("auth.login"))




@auth_bp.route("/contact", methods=["POST"])
def contact_submit():
    # Contact messages handled here because it is part of auth blueprint requirement.
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    subject = (request.form.get("subject") or "").strip()
    message = (request.form.get("message") or "").strip()

    if not name or not email or not subject or not message:
        flash("All contact fields are required.", "danger")
        return redirect(url_for("main.contact_us"))

    try:
        validate_email(email)
    except EmailNotValidError:
        flash("Invalid email address.", "danger")
        return redirect(url_for("main.contact_us"))

    db.session.add(
        ContactMessage(name=name, email=email, subject=subject, message=message)
    )
    db.session.commit()

    # Send email notification to admin
    try:
        msg = Message(
            subject=f"New Contact Message: {subject}",
            recipients=["poeace140503@gmail.com"],
            reply_to=email,
        )
        msg.body = f"""
You have received a new contact message from a visitor.

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
This email was sent automatically by CyberShield.
        """
        msg.html = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
    <div style="text-align: center; margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, #0d6efd, #6610f2); border-radius: 8px;">
        <h2 style="color: #fff; margin: 0;">🔒 CyberShield</h2>
    </div>
    <h3 style="color: #333;">New Contact Message</h3>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; width: 100px;">Name</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{name}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Email</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{email}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Subject</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{subject}</td>
        </tr>
    </table>
    <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
        <h4 style="color: #555; margin-top: 0;">Message:</h4>
        <p style="color: #333; line-height: 1.6; white-space: pre-wrap;">{message}</p>
    </div>
    <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">
    <p style="color: #888; font-size: 12px; text-align: center;">This email was sent automatically by CyberShield Contact System.</p>
</div>
        """
        mail.send(msg)
    except Exception as e:
        # Log the error but don't block the user's success message
        print(f"[CyberShield] Failed to send email notification: {e}")

    flash("Message submitted successfully.", "success")
    return redirect(url_for("main.contact_us"))

