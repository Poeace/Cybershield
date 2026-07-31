"""Database migration: drop old tables, create new ones."""
# Import directly from app.py (not from app/ package)
import importlib.util
import sys
import os

# Load app.py as a module
path = os.path.join(os.path.dirname(__file__), "app.py")
spec = importlib.util.spec_from_file_location("app_module", path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
create_app = app_module.create_app

from app.extensions import db
import sqlalchemy as sa

app = create_app()
with app.app_context():
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print("Current tables:", tables)

    # Drop old cookie_security_logs table if it exists
    if "cookie_security_logs" in tables:
        db.session.execute(sa.text("DROP TABLE IF EXISTS cookie_security_logs"))
        db.session.commit()
        print("Dropped old 'cookie_security_logs' table")
    
    # Create all new tables
    db.create_all()
    
    # Verify
    tables = inspector.get_table_names()
    print("Tables after migration:", tables)
    
    if "breach_check_logs" in tables:
        print("OK: 'breach_check_logs' table created successfully!")
    else:
        print("ERROR: 'breach_check_logs' table NOT found!")

