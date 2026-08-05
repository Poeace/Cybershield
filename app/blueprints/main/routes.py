from flask import render_template, jsonify

from app.blueprints.main import main_bp
from app.extensions import db
from app.models import User, LoginLog, ModuleUsage, UPIScanHistory, CyberReport


@main_bp.route("/")
def home():
    return render_template("home.html")


@main_bp.route("/about")
def about_us():
    return render_template("about.html")


@main_bp.route("/contact")
def contact_us():
    return render_template("contact.html")


@main_bp.route("/security")
def security():
    """Security & Privacy informational page."""
    return render_template("security.html")


@main_bp.route("/api/home/stats")
def api_home_stats():
    """JSON endpoint returning live homepage statistics from the database."""
    registered_users = User.query.count()
    threats_detected = (
        UPIScanHistory.query.count()
        + CyberReport.query.count()
        + LoginLog.query.filter_by(status="failed").count()
    )
    protected_sessions = ModuleUsage.query.count()

    return jsonify({
        "registered_users": registered_users,
        "threats_detected": threats_detected,
        "protected_sessions": protected_sessions,
    })

