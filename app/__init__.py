from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
from .config import Config
import sqlite3
import os

# Initialize extensions
csrf = CSRFProtect()
db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()

# --- Migration logic ---
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
    for col, coltype in columns.items():
        if col not in existing:
            try:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
            except Exception as e:
                print(f"Error adding column {col} to {table}: {e}")
    conn.commit()
    conn.close()

def auto_db_migrate():
    db_path = os.environ.get('DB_PATH', 'hrcloud.db')
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found.")
        return
    for table, columns in TABLES.items():
        add_missing_columns(db_path, table, columns)
    print("Auto DB migration done.")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)

    # Import and register blueprints/routes
    from app.routes.auth import auth_bp
    from app.routes.employees import employees_bp
    from app.routes.attendance import attendance_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.settings import settings_bp
    from app.routes.performance import performance_bp
    from app.routes.payroll import payroll_bp
    from app.routes.audit import audit_bp
    from app.routes.reports import reports_bp
    from app.routes.leave import leave_bp
    from app.routes.landing import landing_bp
    from app.routes.employee_login import employee_login_bp
    from app.routes.support_ticket import support_ticket_bp
    app.register_blueprint(employees_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(landing_bp)
    app.register_blueprint(employee_login_bp)
    app.register_blueprint(support_ticket_bp)

        # Run DB migration automatically once per app startup
        @app.before_request
        def run_auto_migrate():
            if not hasattr(app, '_db_migrated'):
                auto_db_migrate()
                app._db_migrated = True

    return app
