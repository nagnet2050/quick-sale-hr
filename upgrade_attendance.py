"""
تحديث جدول الحضور والانصراف لإضافة ميزات التحقق
"""
import sqlite3
from datetime import datetime

def upgrade_attendance():
    conn = sqlite3.connect('instance/hrcloud.db')
    cursor = conn.cursor()
    
    print("جاري تحديث جدول attendance...")
    
    # إضافة الأعمدة الجديدة لجدول attendance
    columns_to_add = [
        ('mac_address', 'VARCHAR(17)'),
        ('device_info', 'VARCHAR(256)'),
        ('location_verified', 'BOOLEAN DEFAULT 0'),
        ('time_verified', 'BOOLEAN DEFAULT 0'),
        ('device_verified', 'BOOLEAN DEFAULT 0'),
        ('verification_notes', 'TEXT'),
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE attendance ADD COLUMN {column_name} {column_type}')
            print(f"✓ تم إضافة عمود: {column_name}")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f"- العمود {column_name} موجود بالفعل")
            else:
                print(f"✗ خطأ في إضافة {column_name}: {e}")
    
    # إنشاء جدول attendance_settings
    print("\nجاري إنشاء جدول attendance_settings...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_lat REAL DEFAULT 30.0444,
                company_lng REAL DEFAULT 31.2357,
                max_distance_meters INTEGER DEFAULT 100,
                check_in_start TIME DEFAULT '07:00:00',
                check_in_end TIME DEFAULT '10:00:00',
                check_out_start TIME DEFAULT '14:00:00',
                check_out_end TIME DEFAULT '18:00:00',
                require_location_verification BOOLEAN DEFAULT 1,
                require_time_verification BOOLEAN DEFAULT 1,
                require_device_verification BOOLEAN DEFAULT 0,
                allow_outside_hours BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ تم إنشاء جدول attendance_settings")
        
        # إضافة السجل الافتراضي
        cursor.execute('SELECT COUNT(*) FROM attendance_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO attendance_settings 
                (company_lat, company_lng, max_distance_meters) 
                VALUES (30.0444, 31.2357, 100)
            ''')
            print("✓ تم إضافة الإعدادات الافتراضية")
    except sqlite3.OperationalError as e:
        print(f"- جدول attendance_settings موجود بالفعل: {e}")
    
    # إنشاء جدول registered_device
    print("\nجاري إنشاء جدول registered_device...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registered_device (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                mac_address VARCHAR(17) NOT NULL UNIQUE,
                device_name VARCHAR(128),
                device_info VARCHAR(256),
                is_active BOOLEAN DEFAULT 1,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employee (id)
            )
        ''')
        print("✓ تم إنشاء جدول registered_device")
        
        # إنشاء index
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registered_device_employee 
            ON registered_device(employee_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registered_device_mac 
            ON registered_device(mac_address)
        ''')
        print("✓ تم إنشاء الفهارس")
    except sqlite3.OperationalError as e:
        print(f"- جدول registered_device موجود بالفعل: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ تم تحديث قاعدة البيانات بنجاح!")

if __name__ == '__main__':
    upgrade_attendance()
