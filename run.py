from __future__ import annotations

import os

from flask import Flask
from app.extensions import init_extensions
from app.config import Config
from app.blueprints.auth.routes import auth_bp
from app.blueprints.admin.routes import admin_bp
from app.blueprints.main.routes import main_bp
from app.blueprints.modules.routes import modules_bp


def create_app() -> Flask:
    # Use absolute paths so Flask reliably finds templates/static regardless of CWD
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

    # Repo layout: /cyber/app.py, /cyber/app/templates/*, /cyber/static/*
    TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "app", "templates")
    STATIC_DIR = os.path.join(PROJECT_ROOT, "static")

    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

    app.config.from_object(Config)


    init_extensions(app)

    # Ensure DB tables exist (development convenience)
    with app.app_context():
        from app.extensions import db  # local import to avoid circular deps
        db.create_all()

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(modules_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app



app = create_app()


if __name__ == "__main__":
    # Note: debug=True for development.
    app.run(host="0.0.0.0", port=5000, debug=True)

