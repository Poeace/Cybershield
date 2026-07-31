"""App extensions (database, authentication, etc.)."""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

mail = Mail()


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def init_extensions(app):
    """Initialize all Flask extensions for the given app."""
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)


