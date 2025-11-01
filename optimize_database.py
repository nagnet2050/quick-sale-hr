"""
تحسين أداء قاعدة البيانات بإضافة Indexes
"""

from app import create_app, db
from sqlalchemy import text

def optimize_database():
    """إضافة indexes للجداول الأساسية لتحسين الأداء"""
    app = create_app()
    with app.app_context():
        try:
            print("="*60)
            print("تحسين أداء قاعدة البيانات...")
            print("="*60)
            
            # Indexes for employee table
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_employee_active ON employee(active)",
                "CREATE INDEX IF NOT EXISTS idx_employee_code ON employee(code)",
                "CREATE INDEX IF NOT EXISTS idx_employee_department ON employee(department)",
                
                # Indexes for attendance table
                "CREATE INDEX IF NOT EXISTS idx_attendance_employee ON attendance(employee_id)",
                "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)",
                "CREATE INDEX IF NOT EXISTS idx_attendance_employee_date ON attendance(employee_id, date)",
                
                # Indexes for payroll table
                "CREATE INDEX IF NOT EXISTS idx_payroll_employee ON payroll(employee_id)",
                "CREATE INDEX IF NOT EXISTS idx_payroll_year_month ON payroll(year, month)",
                "CREATE INDEX IF NOT EXISTS idx_payroll_status ON payroll(status)",
                
                # Indexes for employee_presence table
                "CREATE INDEX IF NOT EXISTS idx_presence_employee ON employee_presence(employee_id)",
                "CREATE INDEX IF NOT EXISTS idx_presence_status ON employee_presence(status)",
                "CREATE INDEX IF NOT EXISTS idx_presence_last_activity ON employee_presence(last_activity)",
                
                # Indexes for user table
                "CREATE INDEX IF NOT EXISTS idx_user_username ON user(username)",
                "CREATE INDEX IF NOT EXISTS idx_user_active ON user(active)",
                
                # Indexes for leave table
                "CREATE INDEX IF NOT EXISTS idx_leave_employee ON leave(employee_id)",
                "CREATE INDEX IF NOT EXISTS idx_leave_status ON leave(status)",
                "CREATE INDEX IF NOT EXISTS idx_leave_start_date ON leave(start_date)",
                
                # Indexes for client_support table
                "CREATE INDEX IF NOT EXISTS idx_client_support_status ON client_support(status)",
                "CREATE INDEX IF NOT EXISTS idx_client_support_priority ON client_support(priority)",
                "CREATE INDEX IF NOT EXISTS idx_client_support_created ON client_support(created_at)",
            ]
            
            created_count = 0
            for index_sql in indexes:
                try:
                    db.session.execute(text(index_sql))
                    index_name = index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unknown'
                    print(f"✓ تم إنشاء index: idx_{index_name}")
                    created_count += 1
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"✗ خطأ: {str(e)}")
            
            db.session.commit()
            
            print(f"\n✓ تم إنشاء {created_count} index بنجاح!")
            
            # تحسين قاعدة البيانات (VACUUM و ANALYZE)
            print("\nتحسين قاعدة البيانات...")
            try:
                db.session.execute(text("VACUUM"))
                print("✓ تم تنفيذ VACUUM")
            except:
                pass
            
            try:
                db.session.execute(text("ANALYZE"))
                print("✓ تم تنفيذ ANALYZE")
            except:
                pass
            
            print("\n" + "="*60)
            print("✓ اكتمل تحسين قاعدة البيانات بنجاح!")
            print("="*60)
            
        except Exception as e:
            print(f"\n✗ حدث خطأ: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    optimize_database()
