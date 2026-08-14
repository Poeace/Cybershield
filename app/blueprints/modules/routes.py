"""
CyberShield Ransomware Encryption/Decryption Module Routes.

Provides upload → encrypt → show key → decrypt with key → download workflow.
"""

import json
import os
import uuid

from flask import render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from flask_mail import Message

from app.blueprints.modules import modules_bp
from app.extensions import db, mail
from app.models import (
    ModuleUsage, ReportedUPI, UPIScanHistory, CyberReport, UPIFraudReport,
    BackupHistory, BreachCheckLog,
)
from app.qr_reader import decode_qr_upi_handle
from app.risk_engine import compute_risk_score
from app.upi_validator import validate_upi_handle, KNOWN_PROVIDERS

# Breach Checker import
from app.utils.breach_checker import check_personal_info_breaches

# Ransomware module imports
from app.utils.ransomware_simulator import (
    encrypt_user_file,
    decrypt_with_key,
    list_encrypted_files,
    delete_encrypted_file,
    get_stats as get_ransomware_stats,
)


@modules_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@modules_bp.route("/module/cookies", methods=["GET", "POST"])
@login_required
def cookie_module():
    risk = None
    recommendations = []
    breach_results = None

    # Run breach check on GET (auto-scan on page load)
    if request.method == "GET":
        try:
            breach_results = check_personal_info_breaches(
                email=current_user.email,
                phone_number=current_user.phone_number
            )
            # Log the breach check
            log_entry = BreachCheckLog(
                user_id=current_user.user_id,
                email_checked=current_user.email,
                phone_checked=current_user.phone_number,
                breaches_found=json.dumps(breach_results.get("breaches", [])),
                breach_count=breach_results.get("breach_count", 0),
                risk_level=breach_results.get("risk_level", "Safe"),
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent", "")[:200],
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            current_app.logger.warning(f"Breach check failed: {str(e)}")
            breach_results = {
                "error": str(e),
                "breach_count": 0,
                "risk_level": "Error",
                "email_checked": current_user.email,
            }

    if request.method == "POST":
        # Check if this is a breach check refresh
        if request.form.get("check_breach") == "1":
            try:
                breach_results = check_personal_info_breaches(
                    email=current_user.email,
                    phone_number=current_user.phone_number
                )
                log_entry = BreachCheckLog(
                    user_id=current_user.user_id,
                    email_checked=current_user.email,
                    phone_checked=current_user.phone_number,
                    breaches_found=json.dumps(breach_results.get("breaches", [])),
                    breach_count=breach_results.get("breach_count", 0),
                    risk_level=breach_results.get("risk_level", "Safe"),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get("User-Agent", "")[:200],
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                current_app.logger.warning(f"Breach check failed: {str(e)}")

        # Run the cookie risk assessment
        has_tracking = request.form.get("tracking_cookies") == "on"
        wants_cross_site = request.form.get("cross_site") == "on"

        score = 0
        if has_tracking:
            score += 45
        if wants_cross_site:
            score += 35

        if score >= 75:
            risk = "High Risk"
            recommendations = [
                "Enable browser 'Do Not Track'.",
                "Use privacy-focused settings and extensions.",
                "Review and limit third-party cookie access.",
            ]
        elif score >= 35:
            risk = "Warning"
            recommendations = [
                "Clear cookies regularly.",
                "Review site cookie permissions.",
                "Consider browser privacy mode.",
            ]
        else:
            risk = "Safe"
            recommendations = [
                "Your cookie settings look reasonably safe.",
                "Keep tracking permissions minimal.",
            ]

    _log_module_access(current_user.user_id, "cookie_protection")
    return render_template(
        "modules/cookies.html",
        risk=risk,
        recommendations=recommendations,
        breach_results=breach_results,
    )


@modules_bp.route("/module/upifraud", methods=["GET", "POST"])
@login_required
def upi_module():
    scan = None
    handle_error = None
    cyber_report_success = None

    if request.method == "POST":
        do_report = request.form.get("report") == "1"
        do_cyber_report = request.form.get("cyber_report") == "1"

        # Prefer QR if present
        upi_handle = (request.form.get("upi_id") or "").strip().lower()

        file = request.files.get("qr_image")
        if file and file.filename:
            try:
                image_bytes = file.read()
                decoded = decode_qr_upi_handle(image_bytes)
                if decoded.upi_handle:
                    upi_handle = decoded.upi_handle.strip().lower()
            except Exception as e:
                handle_error = str(e)

        if not upi_handle:
            handle_error = "Provide a UPI ID or upload a QR code containing a UPI handle (pa=)."

        # Report flow (local report)
        if do_report and upi_handle:
            existing = db.session.execute(
                db.select(ReportedUPI).where(ReportedUPI.upi_handle == upi_handle)
            ).scalar_one_or_none()

            if existing:
                existing.report_count = (existing.report_count or 0) + 1
            else:
                existing = ReportedUPI(upi_handle=upi_handle, report_count=1)
                db.session.add(existing)

            db.session.commit()

        # Cyber team report flow (store + send email alert)
        if do_cyber_report and upi_handle:
            try:
                # Fetch report count
                reported = db.session.execute(
                    db.select(ReportedUPI).where(ReportedUPI.upi_handle == upi_handle)
                ).scalar_one_or_none()
                report_count = reported.report_count if reported else 0

                # Compute risk for the report
                risk = compute_risk_score(
                    upi_handle=upi_handle,
                    report_count=report_count,
                    known_providers=KNOWN_PROVIDERS,
                )

                validation = validate_upi_handle(upi_handle, known_providers=KNOWN_PROVIDERS)
                merged_reasons = list(risk.reasons)
                for r in list(validation.reasons):
                    if r not in merged_reasons:
                        merged_reasons.append(r)

                # Create CyberReport record
                cyber_report = CyberReport(
                    user_id=current_user.user_id,
                    upi_handle=upi_handle,
                    risk_score=risk.risk_score,
                    status=risk.status,
                    reasons="\n".join(merged_reasons),
                    report_notes=f"Reported by user {current_user.username} ({current_user.email})",
                )
                db.session.add(cyber_report)
                db.session.commit()

                # Generate unique report ID
                report_id = f"UFR-{uuid.uuid4().hex[:12].upper()}"
                
                # Create UPIFraudReport entry for user tracking
                upi_fraud_report = UPIFraudReport(
                    report_id=report_id,
                    user_id=current_user.user_id,
                    user_email=current_user.email,
                    upi_handle=upi_handle,
                    threat_level=risk.status,
                    risk_score=risk.risk_score,
                    detection_result="\n".join(merged_reasons),
                    cyber_team_notified=False,
                    user_confirmation_sent=False,
                    status="pending"
                )
                db.session.add(upi_fraud_report)
                db.session.commit()

                # Send email alert to admin/cyber team
                cyber_team_email = current_app.config.get("MAIL_DEFAULT_SENDER")
                try:
                    msg = Message(
                        subject=f"[CyberShield Alert] UPI Fraud Report - {upi_handle}",
                        recipients=[cyber_team_email],
                        body=f"""
CyberShield - UPI Fraud Report

Reported by: {current_user.full_name} ({current_user.username})
Email: {current_user.email}
UPI Handle: {upi_handle}
Risk Score: {risk.risk_score}/100
Threat Level: {risk.status}

Detection Results:
{chr(10).join(f'- {r}' for r in merged_reasons)}

Report ID: {cyber_report.id}
Fraud Report ID: {report_id}
Reported at: {cyber_report.created_at.strftime('%Y-%m-%d %H:%M:%S')}

---
This is a fraud report submission. The user has flagged this UPI ID as suspicious.
Please review and take appropriate action.
                        """.strip(),
                    )
                    mail.send(msg)
                    upi_fraud_report.cyber_team_notified = True
                    db.session.commit()
                except Exception as mail_err:
                    current_app.logger.warning(f"Failed to send cyber report email to team: {mail_err}")

                # Send confirmation email to user
                try:
                    user_msg = Message(
                        subject="CyberShield Fraud Report Confirmation",
                        recipients=[current_user.email],
                        body=f"""
Dear {current_user.full_name},

Thank you for reporting suspicious activity to CyberShield.

Your report has been successfully submitted to our Cyber Security team for investigation.

--- REPORT DETAILS ---
Report ID: {report_id}
Suspicious UPI ID: {upi_handle}
Threat Status: {risk.status}
Risk Score: {risk.risk_score}/100
Submission Date & Time: {upi_fraud_report.submission_date.strftime('%Y-%m-%d %H:%M:%S')}

--- DETECTION RESULTS ---
{chr(10).join(f'• {r}' for r in merged_reasons)}

--- NEXT STEPS ---
Our cyber team has received your report and will review it within 24 hours.
You will be notified via email once the investigation is complete.

IMPORTANT: Please avoid making any transactions using the reported UPI ID 
until the investigation is complete.

--- TRACK YOUR REPORT ---
You can view this and other reports at any time by visiting your 
"My Reports" section in your CyberShield dashboard.

If you have any questions or additional information to provide, 
please don't hesitate to contact us.

Best regards,
CyberShield Cyber Security Team
support@cybershield.local
                        """.strip(),
                    )
                    mail.send(user_msg)
                    upi_fraud_report.user_confirmation_sent = True
                    db.session.commit()
                except Exception as mail_err:
                    current_app.logger.warning(f"Failed to send confirmation email to user: {mail_err}")

                cyber_report_success = f"Report #{report_id} for {upi_handle} has been successfully submitted! A confirmation email has been sent to {current_user.email}. Our Cyber Security team will review it shortly."
            except Exception as e:
                handle_error = f"Failed to submit cyber report: {str(e)}"

        # Scan flow
        if upi_handle and not handle_error:
            reported = db.session.execute(
                db.select(ReportedUPI).where(ReportedUPI.upi_handle == upi_handle)
            ).scalar_one_or_none()
            report_count = reported.report_count if reported else 0

            risk = compute_risk_score(
                upi_handle=upi_handle,
                report_count=report_count,
                known_providers=KNOWN_PROVIDERS,
            )

            validation = validate_upi_handle(upi_handle, known_providers=KNOWN_PROVIDERS)
            extra_reasons = list(validation.reasons)

            merged_reasons = []
            for r in list(risk.reasons) + extra_reasons:
                if r not in merged_reasons:
                    merged_reasons.append(r)

            status = risk.status

            scan = {
                "upi_handle": upi_handle,
                "risk_score": risk.risk_score,
                "status": status,
                "provider": validation.provider,
                "reasons": merged_reasons,
                "recommendations": list(risk.recommendations),
                "payment_recommendation": risk.payment_recommendation,
                "report_count": report_count,
                "timestamp": "now",
            }

            history = UPIScanHistory(
                upi_handle=upi_handle,
                risk_score=risk.risk_score,
                status=status,
                reasons="\n".join(merged_reasons),
            )
            db.session.add(history)
            db.session.commit()

            scan["timestamp"] = history.created_at.strftime("%Y-%m-%d %H:%M:%S")

        if do_cyber_report and not upi_handle:
            pass

    if not scan:
        scan = None

    _log_module_access(current_user.user_id, "upi_fraud_detection")
    return render_template(
        "modules/upifraud.html",
        scan=scan,
        handle_error=handle_error,
        cyber_report_success=cyber_report_success,
    )


# =============================================================================
# VIEW UPI FRAUD REPORTS
# =============================================================================

@modules_bp.route("/upi/my-reports", methods=["GET"])
@login_required
def view_upi_reports():
    """View all UPI fraud reports submitted by the current user."""
    # Fetch all reports for the current user, ordered by newest first
    reports = db.session.execute(
        db.select(UPIFraudReport).where(UPIFraudReport.user_id == current_user.user_id).order_by(UPIFraudReport.submission_date.desc())
    ).scalars().all()
    
    # Format reports for display
    formatted_reports = []
    for report in reports:
        formatted_reports.append({
            "report_id": report.report_id,
            "upi_handle": report.upi_handle,
            "threat_level": report.threat_level,
            "risk_score": report.risk_score,
            "submission_date": report.submission_date.strftime('%Y-%m-%d %H:%M:%S'),
            "submission_date_obj": report.submission_date,
            "status": report.status,
            "cyber_team_notified": report.cyber_team_notified,
            "user_confirmation_sent": report.user_confirmation_sent,
            "detection_result": report.detection_result,
        })
    
    _log_module_access(current_user.user_id, "upi_fraud_reports_view")
    return render_template(
        "modules/upi_reports.html",
        reports=formatted_reports,
        total_reports=len(formatted_reports),
    )


# =============================================================================
# CYBERSHIELD RANSOMWARE ENCRYPTION/DECRYPTION MODULE
# =============================================================================


@modules_bp.route("/module/ransomware", methods=["GET"])
@login_required
def ransomware_module():
    """Ransomware Encryption/Decryption Module main page."""
    root = current_app.root_path
    backup_dir = os.path.join(root, "backups")
    restore_dir = os.path.join(root, "restored")
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(restore_dir, exist_ok=True)

    _log_module_access(current_user.user_id, "ransomware_recovery")
    return render_template("modules/ransomware.html")


# ---------------------------------------------------------------------------
# API: Upload & Encrypt File (Step 1)
# ---------------------------------------------------------------------------
@modules_bp.route("/api/ransomware/upload-and-encrypt", methods=["POST"])
@login_required
def api_upload_and_encrypt():
    """
    Upload a file, backup to user's personal storage, encrypt it with Fernet,
    and return the encryption key to the user.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file selected."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file selected."}), 400

    root = current_app.root_path
    backup_dir = os.path.join(root, "backups")
    uploads_dir = os.path.join(root, "uploads")
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)

    try:
        result = encrypt_user_file(
            file_storage=file,
            user_id=current_user.user_id,
            backup_dir=backup_dir,
            uploads_dir=uploads_dir,
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Encryption failed: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# API: Decrypt with User-Provided Key (Step 2)
# ---------------------------------------------------------------------------
@modules_bp.route("/api/ransomware/decrypt-with-key", methods=["POST"])
@login_required
def api_decrypt_with_key():
    """
    Decrypt a .locked file using the encryption key provided by the user.
    """
    data = request.get_json(silent=True) or {}
    backup_id = data.get("backup_id")
    encryption_key = data.get("encryption_key", "").strip()

    if not backup_id:
        return jsonify({"success": False, "error": "No backup ID specified."}), 400

    if not encryption_key:
        return jsonify({"success": False, "error": "No encryption key provided. Please enter the key that was shown during encryption."}), 400

    root = current_app.root_path
    restore_dir = os.path.join(root, "restored")
    os.makedirs(restore_dir, exist_ok=True)

    try:
        result = decrypt_with_key(
            backup_id=backup_id,
            user_provided_key=encryption_key,
            user_id=current_user.user_id,
            restore_dir=restore_dir,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": f"Decryption failed: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# API: Download Decrypted File (Step 3)
# ---------------------------------------------------------------------------
@modules_bp.route("/api/ransomware/download/<int:backup_id>")
@login_required
def api_download_decrypted(backup_id):
    """
    Download a previously decrypted file.
    The file must have status 'restored' and belong to the current user.
    """
    backup = BackupHistory.query.get_or_404(backup_id)
    if backup.user_id != current_user.user_id:
        return jsonify({"error": "Unauthorized access."}), 403

    if backup.status != "restored":
        return jsonify({"error": "File has not been decrypted yet. Use the decrypt step first."}), 400

    # Find the latest restored file for this backup from restore directory
    root = current_app.root_path
    restore_dir = os.path.join(root, "restored")

    # Get original filename (remove .locked)
    original_name = backup.file_name
    if original_name.endswith(".locked"):
        original_name = original_name[:-7]
    if backup.original_path and not backup.original_path.endswith(".locked"):
        original_name = backup.original_path

    # Look for the decrypted file in restore directory
    decrypted_path = None
    if os.path.exists(restore_dir):
        for fname in os.listdir(restore_dir):
            if original_name in fname or str(backup.id) in fname:
                candidate = os.path.join(restore_dir, fname)
                if os.path.isfile(candidate):
                    decrypted_path = candidate
                    break

    if not decrypted_path or not os.path.exists(decrypted_path):
        return jsonify({"error": "Decrypted file not found on disk. Please decrypt the file again."}), 404

    return send_file(
        decrypted_path,
        as_attachment=True,
        download_name=original_name,
    )


# ---------------------------------------------------------------------------
# API: List Encrypted Files
# ---------------------------------------------------------------------------
@modules_bp.route("/api/ransomware/list-encrypted")
@login_required
def api_list_encrypted():
    """List all encrypted files for the current user."""
    try:
        files = list_encrypted_files(current_user.user_id)
        return jsonify({"success": True, "files": files, "count": len(files)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# API: Delete Encrypted File
# ---------------------------------------------------------------------------
@modules_bp.route("/api/ransomware/delete-encrypted/<int:backup_id>", methods=["POST"])
@login_required
def api_delete_encrypted(backup_id):
    """Delete an encrypted file and its record."""
    try:
        result = delete_encrypted_file(backup_id, current_user.user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# API: Dashboard Stats
# ---------------------------------------------------------------------------
@modules_bp.route("/api/ransomware/stats")
@login_required
def api_ransomware_stats():
    """JSON endpoint for ransomware module statistics."""
    try:
        stats = get_ransomware_stats(current_user.user_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _log_module_access(user_id: int, module_name: str) -> None:
    db.session.add(ModuleUsage(user_id=user_id, module_name=module_name))
    db.session.commit()
