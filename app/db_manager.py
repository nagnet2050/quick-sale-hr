"""
نظام إدارة قاعدة البيانات التلقائي
يقوم بإنشاء وتحديث الجداول تلقائياً بناءً على Models
"""

from sqlalchemy import inspect, text
from app import db


def get_table_columns(table_name):
    """الحصول على أسماء الأعمدة الموجودة في جدول"""
    inspector = inspect(db.engine)
    if table_name in inspector.get_table_names():
        return {col['name'] for col in inspector.get_columns(table_name)}
    return set()


def add_column_if_not_exists(table_name, column_name, column_type):
    """إضافة عمود إلى جدول إذا لم يكن موجوداً"""
    existing_columns = get_table_columns(table_name)
    
    if column_name not in existing_columns:
        try:
            with db.engine.connect() as connection:
                query = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                connection.execute(query)
                connection.commit()
                return True, f"[+] Added {column_name} to {table_name}"
        except Exception as e:
            return False, f"[-] Error adding {column_name} to {table_name}: {e}"
    
    return False, f"Column {column_name} already exists in {table_name}"


def update_database_schema():
    """
    تحديث بنية قاعدة البيانات تلقائياً
    يضيف الأعمدة المفقودة ويحدث الجداول حسب الحاجة
    """
    updates_log = []
    
    # قائمة التحديثات المطلوبة
    schema_updates = {
        'employee': [
            ('username', 'VARCHAR(64)'),
            ('password_hash', 'VARCHAR(128)'),
            ('salary', 'FLOAT DEFAULT 0.0'),
            ('code', 'VARCHAR(16)'),
            ('name', 'VARCHAR(128)'),
            ('address', 'VARCHAR(256)'),
            ('job_title', 'VARCHAR(64)'),
            ('department', 'VARCHAR(64)'),
            ('phone', 'VARCHAR(32)'),
            ('email', 'VARCHAR(128)'),
            ('active', 'BOOLEAN DEFAULT 1')
        ],
        'payroll': [
            ('basic', 'FLOAT DEFAULT 0.0'),
            ('allowances', 'FLOAT DEFAULT 0.0'),
            ('bonus', 'FLOAT DEFAULT 0.0'),
            ('overtime', 'FLOAT DEFAULT 0.0'),
            ('deductions', 'FLOAT DEFAULT 0.0'),
            ('tax', 'FLOAT DEFAULT 0.0'),
            ('insurance', 'FLOAT DEFAULT 0.0'),
            ('net', 'FLOAT DEFAULT 0.0'),
            ('period_start', 'DATE'),
            ('period_end', 'DATE'),
            ('generated_by', 'INTEGER'),
            ('generated_at', 'DATETIME'),
            ('status', "VARCHAR(32) DEFAULT 'unpaid'"),
            ('payment_date', 'DATE'),
            ('payment_method', 'VARCHAR(32)'),
            ('employee_id', 'INTEGER'),
            ('unpaid_leave_days', 'INTEGER DEFAULT 0'),
            ('unpaid_leave_deduction', 'FLOAT DEFAULT 0.0'),
            # حقول تتبع إعادة الحساب
            ('last_recalc_net_diff', 'FLOAT DEFAULT 0.0'),
            ('last_recalc_at', 'DATETIME')
        ],
        'user': [
            ('username', 'VARCHAR(64) UNIQUE'),
            ('password_hash', 'VARCHAR(128)'),
            ('role', 'VARCHAR(32)'),
            ('active', 'BOOLEAN DEFAULT 1')
        ],
        'leave': [
            ('employee_id', 'INTEGER'),
            ('leave_type', 'VARCHAR(32)'),
            ('start_date', 'DATE'),
            ('end_date', 'DATE'),
            ('reason', 'TEXT'),
            ('status', 'VARCHAR(32)'),
            ('paid', 'BOOLEAN DEFAULT 1'),
            ('paid_days', 'INTEGER'),
            ('requested_at', 'DATETIME'),
            ('approved_by', 'INTEGER'),
            ('approved_at', 'DATETIME')
        ],
        'leave_balance': [
            ('employee_id', 'INTEGER UNIQUE'),
            ('annual_total', 'INTEGER DEFAULT 21'),
            ('annual_used', 'INTEGER DEFAULT 0'),
            ('casual_total', 'INTEGER DEFAULT 6'),
            ('casual_used', 'INTEGER DEFAULT 0'),
            ('sick_paid_cap', 'INTEGER DEFAULT 0'),
            ('sick_used_paid', 'INTEGER DEFAULT 0'),
            ('updated_at', 'DATETIME')
        ],
        'performance': [
            ('employee_id', 'INTEGER'),
            ('review_date', 'DATE'),
            ('score', 'INTEGER'),
            ('comments', 'TEXT'),
            ('created_by', 'INTEGER'),
            ('created_at', 'DATETIME'),
            ('updated_at', 'DATETIME')
        ],
        'attendance': [
            ('employee_id', 'INTEGER'),
            ('date', 'DATE'),
            ('time_in', 'TIME'),
            ('time_out', 'TIME'),
            ('status', 'VARCHAR(32)'),
            ('timestamp', 'DATETIME'),
            ('location', 'VARCHAR(128)')
        ],
        'whatsapp_messages': [
            ('complaint_id', 'INTEGER'),
            ('customer_phone', 'VARCHAR(20)'),
            ('message_type', "VARCHAR(32) DEFAULT 'text'"),
            ('message_content', 'TEXT'),
            ('direction', "VARCHAR(32) DEFAULT 'incoming'"),
            ('message_date', 'DATETIME'),
            ('sent_by', 'INTEGER'),
            ('status', "VARCHAR(32) DEFAULT 'sent'")
        ],
        'customer_complaint': [
            ('customer_name', 'VARCHAR(128)'),
            ('customer_phone', 'VARCHAR(20)'),
            ('complaint_type', 'VARCHAR(64)'),
            ('description', 'TEXT'),
            ('status', 'VARCHAR(32)'),
            ('priority', 'VARCHAR(32)'),
            ('assigned_to', 'INTEGER'),
            ('created_at', 'DATETIME'),
            ('updated_at', 'DATETIME')
        ],
        'customer_complaints': [
            ('customer_name', 'VARCHAR(100)'),
            ('customer_phone', 'VARCHAR(20)'),
            ('issue_description', 'TEXT'),
            ('status', 'VARCHAR(50) DEFAULT "new"'),
            ('priority', 'VARCHAR(20) DEFAULT "medium"'),
            ('category', 'VARCHAR(100)'),
            ('assigned_to', 'INTEGER'),
            ('referred_to_manager', 'INTEGER'),
            ('referred_to_department', 'VARCHAR(100)'),
            ('manager_solution', 'TEXT'),
            ('manager_response_date', 'DATETIME'),
            ('manager_instructions', 'TEXT'),
            ('employee_action', 'TEXT'),
            ('customer_contact_method', 'VARCHAR(50)'),
            ('customer_response', 'TEXT'),
            ('resolution_details', 'TEXT'),
            ('resolved_at', 'DATETIME'),
            ('management_response', 'TEXT'),
            ('response_date', 'DATETIME'),
            ('resolution_notes', 'TEXT'),
            ('created_by', 'INTEGER'),
            ('created_at', 'DATETIME'),
            ('updated_at', 'DATETIME')
        ],
        'employee_presence': [
            ('employee_id', 'INTEGER'),
            ('is_online', 'BOOLEAN'),
            ('last_activity', 'DATETIME')
        ],
        'settings': [
            ('key', 'VARCHAR(64) UNIQUE'),
            ('value', 'TEXT'),
            ('description', 'VARCHAR(256)'),
            # Email provider fields (gradual rollout)
            ('sendgrid_api_key', 'VARCHAR(256)'),
            ('email_provider', 'VARCHAR(32)'),
            ('sendgrid_password_changed_template_id', 'VARCHAR(128)')
        ],
        'whatsapp_conversations': [
            ('customer_phone', 'VARCHAR(20)'),
            ('customer_name', 'VARCHAR(100)'),
            ('last_message', 'TEXT'),
            ('last_message_type', 'VARCHAR(20)'),
            ('last_message_direction', 'VARCHAR(10)'),
            ('unread_count', 'INTEGER DEFAULT 0'),
            ('status', "VARCHAR(20) DEFAULT 'active'"),
            ('assigned_to', 'INTEGER'),
            ('created_at', 'DATETIME'),
            ('updated_at', 'DATETIME')
        ],
        'whatsapp_templates': [
            ('name', 'VARCHAR(100)'),
            ('content', 'TEXT'),
            ('template_type', "VARCHAR(20) DEFAULT 'text'"),
            ('category', 'VARCHAR(50)'),
            ('created_by', 'INTEGER'),
            ('created_at', 'DATETIME')
        ]
    }
    
    # تطبيق التحديثات
    for table_name, columns in schema_updates.items():
        for column_name, column_type in columns:
            success, message = add_column_if_not_exists(table_name, column_name, column_type)
            if success:
                updates_log.append(message)
    
    return updates_log


def create_missing_tables():
    """إنشاء الجداول المفقودة"""
    try:
        # استيراد جميع النماذج
        from app.models.employee import Employee
        from app.models.user import User
        from app.models.payroll import Payroll
        from app.models.attendance import Attendance
        from app.models.leave import Leave
        from app.models.performance import Performance
        from app.models.audit import Audit
        from app.models.support import SupportTicket
        from app.models.presence import EmployeePresence
        from app.models.settings import Settings
        from app.models.whatsapp_models import WhatsAppMessage
        from app.models.client_support import ClientSupport, ClientTransferHistory
        from app.models.password_reset import PasswordResetCode
        # نماذج نظام الصلاحيات المتقدم
        from app.models.permission import Role, Permission, RolePermission, UserRole, PermissionLog
        
        # إنشاء جميع الجداول
        db.create_all()
        return True, "[+] All tables created/verified"
    except Exception as e:
        return False, f"[-] Error creating tables: {e}"


def create_default_admin_user():
    """إنشاء مستخدم admin افتراضي بدون كلمة مرور ضعيفة.
    - اسم المستخدم الافتراضي '1' (ليطابق غالباً رقم الموظف المدير)
    - كلمة المرور: تُؤخذ من متغير بيئي ADMIN_PASSWORD إن وُجد، وإلا تُولَّد كلمة قوية عشوائياً.
    ملاحظة: تسجيل الدخول للمدير يتم بكلمة مرور الموظف المرتبط (انظر auth.login) وليس بهذه الكلمة.
    """
    try:
        from app.models.user import User
        import os, secrets

        admin = User.query.filter_by(username='1').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            provided = os.environ.get('ADMIN_PASSWORD')
            pw = provided if provided else secrets.token_urlsafe(16)
            admin = User(
                username='1',
                role='admin',
                password_hash=generate_password_hash(pw),
                active=True
            )
            db.session.add(admin)
            db.session.commit()
            if provided:
                return True, "[+] Created default admin user: 1 (env password set)"
            else:
                return True, "[+] Created default admin user: 1 (random password generated)"
        else:
            return False, "[+] Admin user already exists"
    except Exception as e:
        return False, f"[!] Could not create admin user: {e}"


def auto_migrate_database():
    """
    دالة رئيسية للتحديث التلقائي لقاعدة البيانات
    تستدعى عند بدء تشغيل التطبيق
    """
    print("\n" + "="*60)
    print("[*] Starting Database Auto-Migration...")
    print("="*60)
    
    # إنشاء الجداول المفقودة
    success, message = create_missing_tables()
    print(message)
    
    # تحديث البنية
    updates = update_database_schema()
    
    if updates:
        print("\n[+] Schema Updates Applied:")
        for update in updates:
            print(f"  {update}")
    else:
        print("\n[+] No schema updates needed - database is up to date")
    
    # إنشاء مستخدم افتراضي
    success, message = create_default_admin_user()
    print(message)
    
    print("="*60)
    print("[+] Database Migration Completed Successfully")
    print("="*60 + "\n")

    # Seed/initialize default permissions and roles (idempotent)
    try:
        from app.models.permission import (
            initialize_default_permissions,
            initialize_default_roles,
            assign_admin_permissions,
        )
        initialize_default_permissions()
        initialize_default_roles()
        assign_admin_permissions()
        print("[+] Permissions and roles initialized (idempotent)")
    except Exception as e:
        print(f"[!] Permission initialization skipped due to error: {e}")
