import sqlite3
import os
from app.models.employee import Employee
from app.models.payroll import Payroll
from app.models.leave import Leave
from app.models.performance import Performance
from app.models.attendance import Attendance
from app.models.user import User
from app import db, create_app

DB_PATH = os.environ.get('DB_PATH', 'hrcloud.db')

# Columns to ensure for each table
TABLES = {
    'employee': {
        'salary': 'FLOAT DEFAULT 0.0',
        'code': 'VARCHAR(32)',
        'name': 'VARCHAR(128)',
        'job_title': 'VARCHAR(128)',
        'department': 'VARCHAR(128)',
        'phone': 'VARCHAR(32)',
        'email': 'VARCHAR(128)',
        'active': 'BOOLEAN DEFAULT 1'
    },
    'payroll': {
        'basic': 'FLOAT DEFAULT 0.0',
        'allowances': 'FLOAT DEFAULT 0.0',
        'bonus': 'FLOAT DEFAULT 0.0',
        'overtime': 'FLOAT DEFAULT 0.0',
        'deductions': 'FLOAT DEFAULT 0.0',
        'tax': 'FLOAT DEFAULT 0.0',
        'insurance': 'FLOAT DEFAULT 0.0',
        'net': 'FLOAT DEFAULT 0.0',
        'period_start': 'DATE',
        'period_end': 'DATE',
        'generated_by': 'INTEGER',
        'generated_at': 'DATETIME',
        'status': "VARCHAR(32) DEFAULT 'unpaid'",
        'employee_id': 'INTEGER'
    },
    'leave': {
        'requested_at': 'DATETIME',
        'approved_by': 'INTEGER',
        'approved_at': 'DATETIME'
    },
    'performance': {
        'created_by': 'INTEGER',
        'created_at': 'DATETIME',
        'updated_at': 'DATETIME'
    },
    'attendance': {
        'timestamp': 'DATETIME',
        'location': 'VARCHAR(128)'
    },
    'user': {
        'username': 'VARCHAR(64)',
        'password_hash': 'VARCHAR(128)',
        'role': 'VARCHAR(32) DEFAULT "user"'
    }
}

def add_missing_columns(db_path, table, columns):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cur.fetchall()}
    added = []
    for col, coltype in columns.items():
        if col not in existing:
            try:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
                added.append(col)
            except Exception as e:
                print(f"Error adding column {col} to {table}: {e}")
    conn.commit()
    conn.close()
    return added

def main():
    app = create_app()
    with app.app_context():
        db.create_all()
    print("Checked/created all tables via SQLAlchemy.")
    db_path = DB_PATH
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found.")
        return
    for table, columns in TABLES.items():
        added = add_missing_columns(db_path, table, columns)
        if added:
            print(f"Added columns to {table}: {', '.join(added)}")
        else:
            print(f"No columns added to {table} (all present)")
    print("Migration complete.")

if __name__ == "__main__":
    main()
