from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
from .config import Config
import sqlite3
import os
from flask_migrate import Migrate

# Initialize extensions
csrf = CSRFProtect()
db = SQLAlchemy()  # تعريف الكائن db
login_manager = LoginManager()
babel = Babel()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    csrf.init_app(app)
    db.init_app(app)  # Properly initialize the db object
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # صفحة تسجيل الدخول الرئيسية
    babel.init_app(app)

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

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
    from app.routes.support import support_bp
    from app.routes.lang import lang_bp
    from app.routes.ess import ess_bp
    from app.routes.mss import mss_bp
    from app.routes.rewards import rewards_bp
    from app.routes.surveys import surveys_bp
    from app.routes.lms import lms_bp
    from app.routes.succession import succession_bp
    from app.routes.ats import ats_bp
    from app.routes.analytics import analytics_bp
    from app.routes.compensation import compensation_bp
    from app.routes.external_workforce import external_workforce_bp
    from app.routes.ehs import ehs_bp
    from app.routes.ai import ai_bp
    from app.routes.presence import presence_bp
    from app.routes.presence_status import presence_status_bp
    from app.routes.employee_profile import employee_profile_bp
    from app.routes.client_support import client_support_bp
    from app.routes.support_ticket import support_ticket_bp
    from app.routes.support_hub import support_hub_bp
    from app.routes.permissions import permissions_bp  # نظام الصلاحيات المتقدم
    from app.routes.attendance_reports import attendance_reports_bp  # تقارير الحضور المتقدمة
    # from app.routes.whatsapp import whatsapp_bp  # استُبدل بـ whatsapp_api
    from app.routes.whatsapp_api import whatsapp_bp as whatsapp_api_bp
    from app.routes.user import user_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(permissions_bp)  # نظام الصلاحيات
    app.register_blueprint(attendance_reports_bp)  # تقارير الحضور
    app.register_blueprint(whatsapp_api_bp)  # WhatsApp API الجديد
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
    app.register_blueprint(support_bp)
    app.register_blueprint(lang_bp)
    app.register_blueprint(ess_bp)
    app.register_blueprint(mss_bp)
    app.register_blueprint(rewards_bp)
    app.register_blueprint(surveys_bp)
    app.register_blueprint(lms_bp)
    app.register_blueprint(succession_bp)
    app.register_blueprint(ats_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(compensation_bp)
    app.register_blueprint(external_workforce_bp)
    app.register_blueprint(ehs_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(presence_bp)
    app.register_blueprint(presence_status_bp)
    app.register_blueprint(employee_profile_bp)
    app.register_blueprint(client_support_bp)
    app.register_blueprint(support_ticket_bp)
    app.register_blueprint(support_hub_bp)
    # whatsapp_bp القديم تم استبداله بـ whatsapp_api_bp (مُسجّل في السطر 72)

    # تشغيل التحديث التلقائي لقاعدة البيانات
    with app.app_context():
        from app.db_manager import auto_migrate_database
        auto_migrate_database()

    return app
