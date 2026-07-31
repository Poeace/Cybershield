"""Verify the new cyber_reports table was created."""
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables in DB:", tables)
    if "cyber_reports" in tables:
        print("OK: cyber_reports table created successfully")
    else:
        print("ERROR: cyber_reports table NOT found!")
