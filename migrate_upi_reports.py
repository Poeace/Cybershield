#!/usr/bin/env python3
"""
Database Migration Script for UPI Fraud Report Enhancement
This script creates the upi_fraud_reports table needed for the new feature.

Usage:
    python migrate_upi_reports.py
"""

import sys
from app import create_app
from app.extensions import db
from app.models import UPIFraudReport

def migrate():
    """Create the UPIFraudReport table in the database."""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            
            # Verify table was created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'upi_fraud_reports' in tables:
                print("✅ SUCCESS: UPI Fraud Reports table created successfully!")
                print("\nTable Details:")
                print(f"  Table Name: upi_fraud_reports")
                print(f"  Columns: {', '.join([c['name'] for c in inspector.get_columns('upi_fraud_reports')])}")
                return 0
            else:
                print("❌ ERROR: Table creation failed!")
                return 1
                
        except Exception as e:
            print(f"❌ ERROR: Migration failed with error: {str(e)}")
            return 1

if __name__ == '__main__':
    sys.exit(migrate())
