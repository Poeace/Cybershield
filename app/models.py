from __future__ import annotations

import json
from datetime import datetime

from flask_login import UserMixin

from app.extensions import db, login_manager


class BackupHistory(db.Model):
    """Stores records of files backed up by CyberShield Backup & Recovery."""
    __tablename__ = "backup_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    original_path = db.Column(db.String(512), nullable=False)
    backup_path = db.Column(db.String(512), nullable=False)
    sha256_hash = db.Column(db.String(64), nullable=False, index=True)
    file_size = db.Column(db.Integer, nullable=True)
    backup_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(30), nullable=False, default="active")  # active / encrypted / restored / missing / corrupted
    recovery_point = db.Column(db.String(100), nullable=True)  # Recovery point identifier
    encryption_key = db.Column(db.Text, nullable=True)  # Fernet encryption key for .locked files


class RecoveryHistory(db.Model):
    """Stores records of file recoveries performed by CyberShield."""
    __tablename__ = "recovery_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    backup_id = db.Column(db.Integer, db.ForeignKey("backup_history.id"), nullable=True)
    incident_id = db.Column(db.String(64), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    original_path = db.Column(db.String(512), nullable=False)
    backup_path = db.Column(db.String(512), nullable=False)
    restore_path = db.Column(db.String(512), nullable=True)
    sha256_hash = db.Column(db.String(64), nullable=False)
    recovery_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(30), nullable=False, default="restored")  # restored / failed / integrity_failed
    integrity_verified = db.Column(db.Boolean, default=False)
    recovery_duration_ms = db.Column(db.Integer, nullable=True)


class IncidentReport(db.Model):
    """Stores incident report data for ransomware attacks."""
    __tablename__ = "incident_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    incident_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    report_data = db.Column(db.Text, nullable=False)  # JSON blob storing full report
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(30), nullable=False, default="generated")  # generated / downloaded / archived





class User(db.Model, UserMixin):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(30), nullable=False)
    registration_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


    def get_id(self):
        return str(self.user_id)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class PasswordOTP(db.Model):
    __tablename__ = "password_otps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)


class LoginLog(db.Model):
    __tablename__ = "login_logs"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), nullable=True)
    login_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(30), nullable=False)  # success/failed


class ModuleUsage(db.Model):
    __tablename__ = "module_usage"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    module_name = db.Column(db.String(80), nullable=False)
    accessed_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class BreachCheckLog(db.Model):
    """Stores personal data breach check logs for the Cookie Protection module."""
    __tablename__ = "breach_check_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    email_checked = db.Column(db.String(120), nullable=False)
    phone_checked = db.Column(db.String(30), nullable=True)
    breaches_found = db.Column(db.Text, nullable=True)  # JSON blob of breach details
    breach_count = db.Column(db.Integer, nullable=False, default=0)
    risk_level = db.Column(db.String(20), nullable=True)  # Safe / Warning / Critical
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ReportedUPI(db.Model):
    __tablename__ = "reported_upi"

    id = db.Column(db.Integer, primary_key=True)
    upi_handle = db.Column(db.String(120), nullable=False, unique=True)
    report_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class UPIScanHistory(db.Model):
    __tablename__ = "upi_scan_history"

    id = db.Column(db.Integer, primary_key=True)
    upi_handle = db.Column(db.String(120), nullable=False, index=True)
    risk_score = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False)
    reasons = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class CyberReport(db.Model):
    __tablename__ = "cyber_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    upi_handle = db.Column(db.String(120), nullable=False)
    risk_score = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False)
    reasons = db.Column(db.Text, nullable=True)
    report_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, nullable=False, default=False)


class UPIFraudReport(db.Model):
    """Stores UPI fraud reports submitted by users with unique report IDs for tracking."""
    __tablename__ = "upi_fraud_reports"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(32), nullable=False, unique=True, index=True)  # Unique report ID
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    upi_handle = db.Column(db.String(120), nullable=False)
    threat_level = db.Column(db.String(30), nullable=False)  # High Risk / Medium Risk / Safe
    risk_score = db.Column(db.Integer, nullable=False)
    detection_result = db.Column(db.Text, nullable=True)  # JSON or formatted reasons
    submission_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    cyber_team_notified = db.Column(db.Boolean, nullable=False, default=False)
    user_confirmation_sent = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(30), nullable=False, default="pending")  # pending / under_review / resolved / closed


@login_manager.user_loader
def load_user(user_id: str):
    # SQLAlchemy 3: prefer session.get(Model, primary_key)
    return db.session.get(User, int(user_id))


