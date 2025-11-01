"""
تحديث قاعدة البيانات للميزات المتقدمة
"""
import sqlite3
from datetime import datetime

def upgrade_advanced_attendance():
    conn = sqlite3.connect('instance/hrcloud.db')
    cursor = conn.cursor()
    
    print("=" * 60)
    print("تحديث قاعدة البيانات - الميزات المتقدمة للحضور")
    print("=" * 60)
    
    # 1. جدول التقارير المجمّعة
    print("\n📊 إنشاء جدول attendance_report...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_report (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                period_type VARCHAR(20),
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                total_days INTEGER DEFAULT 0,
                present_days INTEGER DEFAULT 0,
                absent_days INTEGER DEFAULT 0,
                late_days INTEGER DEFAULT 0,
                total_work_minutes INTEGER DEFAULT 0,
                total_late_minutes INTEGER DEFAULT 0,
                total_overtime_minutes INTEGER DEFAULT 0,
                average_late_minutes REAL DEFAULT 0.0,
                location_violations INTEGER DEFAULT 0,
                time_violations INTEGER DEFAULT 0,
                device_violations INTEGER DEFAULT 0,
                linked_to_payroll BOOLEAN DEFAULT 0,
                payroll_id INTEGER,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                generated_by INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employee (id),
                FOREIGN KEY (payroll_id) REFERENCES payroll (id),
                FOREIGN KEY (generated_by) REFERENCES user (id)
            )
        ''')
        print("✓ تم إنشاء جدول attendance_report")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_att_report_employee 
            ON attendance_report(employee_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_att_report_period 
            ON attendance_report(period_start, period_end)
        ''')
        print("✓ تم إنشاء الفهارس")
    except sqlite3.OperationalError as e:
        print(f"- جدول attendance_report موجود: {e}")
    
    # 2. جدول قائمة المزامنة (Offline Support)
    print("\n🔄 إنشاء جدول attendance_sync...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_sync (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                action VARCHAR(20),
                timestamp TIMESTAMP NOT NULL,
                lat REAL,
                lng REAL,
                address VARCHAR(256),
                mac_address VARCHAR(17),
                device_info VARCHAR(256),
                sync_status VARCHAR(20) DEFAULT 'pending',
                sync_attempts INTEGER DEFAULT 0,
                last_sync_attempt TIMESTAMP,
                error_message TEXT,
                original_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_at TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employee (id)
            )
        ''')
        print("✓ تم إنشاء جدول attendance_sync")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_att_sync_status 
            ON attendance_sync(sync_status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_att_sync_employee 
            ON attendance_sync(employee_id)
        ''')
        print("✓ تم إنشاء الفهارس")
    except sqlite3.OperationalError as e:
        print(f"- جدول attendance_sync موجود: {e}")
    
    # 3. جدول RBAC للحضور
    print("\n🔐 إنشاء جدول attendance_rbac...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_rbac (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name VARCHAR(128) NOT NULL,
                description TEXT,
                rule_type VARCHAR(50),
                applies_to TEXT,
                can_check_in BOOLEAN DEFAULT 1,
                can_check_out BOOLEAN DEFAULT 1,
                can_check_for_others BOOLEAN DEFAULT 0,
                allowed_devices TEXT,
                allowed_locations TEXT,
                allowed_time_ranges TEXT,
                is_active BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES user (id)
            )
        ''')
        print("✓ تم إنشاء جدول attendance_rbac")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_att_rbac_active 
            ON attendance_rbac(is_active, priority)
        ''')
        print("✓ تم إنشاء الفهارس")
        
        # إضافة قواعد افتراضية
        cursor.execute("SELECT COUNT(*) FROM attendance_rbac")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO attendance_rbac 
                (rule_name, description, rule_type, can_check_in, can_check_out, can_check_for_others, priority)
                VALUES 
                ('Admin Full Access', 'المسؤولون لهم صلاحيات كاملة', 'role', 1, 1, 1, 100),
                ('Manager Access', 'المديرون يمكنهم تسجيل حضور فريقهم', 'role', 1, 1, 1, 50),
                ('Employee Self Only', 'الموظفون يسجلون حضورهم فقط', 'role', 1, 1, 0, 10)
            ''')
            print("✓ تم إضافة القواعد الافتراضية")
    except sqlite3.OperationalError as e:
        print(f"- جدول attendance_rbac موجود: {e}")
    
    # 4. جدول ربط الحضور بالرواتب
    print("\n💰 إنشاء جدول payroll_attendance_link...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payroll_attendance_link (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payroll_id INTEGER NOT NULL,
                report_id INTEGER NOT NULL,
                late_deduction_amount REAL DEFAULT 0.0,
                absence_deduction_amount REAL DEFAULT 0.0,
                overtime_bonus_amount REAL DEFAULT 0.0,
                late_deduction_rate REAL,
                absence_deduction_rate REAL,
                overtime_bonus_rate REAL,
                auto_calculated BOOLEAN DEFAULT 1,
                approved BOOLEAN DEFAULT 0,
                approved_by INTEGER,
                approved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (payroll_id) REFERENCES payroll (id),
                FOREIGN KEY (report_id) REFERENCES attendance_report (id),
                FOREIGN KEY (approved_by) REFERENCES user (id)
            )
        ''')
        print("✓ تم إنشاء جدول payroll_attendance_link")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_payroll_link_payroll 
            ON payroll_attendance_link(payroll_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_payroll_link_report 
            ON payroll_attendance_link(report_id)
        ''')
        print("✓ تم إنشاء الفهارس")
    except sqlite3.OperationalError as e:
        print(f"- جدول payroll_attendance_link موجود: {e}")
    
    # 5. إضافة إعدادات الربط التلقائي
    print("\n⚙️ تحديث جدول attendance_settings...")
    columns_to_add = [
        ('auto_link_payroll', 'BOOLEAN DEFAULT 1'),
        ('late_deduction_per_minute', 'REAL DEFAULT 1.0'),
        ('absence_deduction_per_day', 'REAL DEFAULT 100.0'),
        ('overtime_bonus_per_hour', 'REAL DEFAULT 50.0'),
        ('grace_period_minutes', 'INTEGER DEFAULT 15'),
        ('min_work_hours_per_day', 'INTEGER DEFAULT 8'),
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE attendance_settings ADD COLUMN {column_name} {column_type}')
            print(f"✓ تم إضافة عمود: {column_name}")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f"- العمود {column_name} موجود بالفعل")
            else:
                print(f"✗ خطأ: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ تم تحديث قاعدة البيانات بنجاح!")
    print("=" * 60)

if __name__ == '__main__':
    upgrade_advanced_attendance()
