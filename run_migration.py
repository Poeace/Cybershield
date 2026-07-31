"""Run database migration directly on SQLite."""
import os
import sys

# Ensure we're in project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Use SQLite directly
import sqlite3

db_path = os.path.join(os.getcwd(), "app", "cybershield.sqlite3")
print(f"Database path: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Current tables:", tables)

# Drop old cookie_security_logs table if it exists
if "cookie_security_logs" in tables:
    cursor.execute("DROP TABLE IF EXISTS cookie_security_logs")
    conn.commit()
    print("Dropped old 'cookie_security_logs' table")
else:
    print("'cookie_security_logs' table not found - nothing to drop")

# Create breach_check_logs table
cursor.execute("""
CREATE TABLE IF NOT EXISTS breach_check_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    email_checked VARCHAR(120) NOT NULL,
    phone_checked VARCHAR(30),
    breaches_found TEXT,
    breach_count INTEGER NOT NULL DEFAULT 0,
    risk_level VARCHAR(20),
    ip_address VARCHAR(45),
    user_agent VARCHAR(200),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")
conn.commit()
print("Created 'breach_check_logs' table")

# Verify
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables after migration:", tables)

if "breach_check_logs" in tables:
    print("OK: 'breach_check_logs' table created successfully!")
else:
    print("ERROR: 'breach_check_logs' table NOT found!")

conn.close()

