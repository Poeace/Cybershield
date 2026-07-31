import os


class Config:
    SECRET_KEY = os.environ.get("CYBERSHIELD_SECRET_KEY", "dev-secret-change-me")

    # SQLite database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(os.path.dirname(__file__), "cybershield.sqlite3")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Auth
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set True only in production with HTTPS
    SESSION_COOKIE_SAMESITE = "Lax"

    # Cookie Integrity Scanner settings
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes (in seconds)

    # Admin defaults
    # In production, set via environment variables.
    ADMIN_USERNAME = os.environ.get("CYBERSHIELD_ADMIN_USERNAME", "Poeace")
    ADMIN_PASSWORD = os.environ.get("CYBERSHIELD_ADMIN_PASSWORD", "Dhurandhar")

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "poeace140503@gmail.com"
    MAIL_PASSWORD = "afzn xbot nues hnic"
    MAIL_DEFAULT_SENDER = "poeace140503@gmail.com"