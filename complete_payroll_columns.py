"""
إضافة جميع الأعمدة المفقودة في جدول payroll
"""

from app import create_app, db
from sqlalchemy import text

def add_all_payroll_columns():
    """إضافة جميع الأعمدة المفقودة"""
    app = create_app()
    with app.app_context():
        try:
            # الحصول على الأعمدة الموجودة
            result = db.session.execute(text("PRAGMA table_info(payroll)"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            # جميع الأعمدة المطلوبة حسب النموذج
            required_columns = [
                ('housing_allowance', 'FLOAT', 0.0),
                ('transport_allowance', 'FLOAT', 0.0),
                ('food_allowance', 'FLOAT', 0.0),
                ('phone_allowance', 'FLOAT', 0.0),
                ('other_allowances', 'FLOAT', 0.0),
                ('commission', 'FLOAT', 0.0),
                ('overtime_hours', 'FLOAT', 0.0),
                ('overtime_amount', 'FLOAT', 0.0),
                ('incentives', 'FLOAT', 0.0),
                ('absence_days', 'INTEGER', 0),
                ('absence_deduction', 'FLOAT', 0.0),
                ('late_minutes', 'INTEGER', 0),
                ('late_deduction', 'FLOAT', 0.0),
                ('loan_deduction', 'FLOAT', 0.0),
                ('other_deductions', 'FLOAT', 0.0),
                ('health_insurance', 'FLOAT', 0.0),
                ('gross_salary', 'FLOAT', 0.0),
                ('total_deductions', 'FLOAT', 0.0),
                ('bank_name', 'VARCHAR(100)', None),
                ('account_number', 'VARCHAR(50)', None),
                ('reference_number', 'VARCHAR(100)', None),
                ('approved_by', 'INTEGER', None),
                ('approved_at', 'DATETIME', None),
                ('paid_by', 'INTEGER', None),
                ('paid_at', 'DATETIME', None),
                ('notes', 'TEXT', None),
                ('is_final', 'BOOLEAN', 0),
            ]
            
            print("="*60)
            print("إضافة الأعمدة المفقودة إلى جدول payroll")
            print("="*60)
            
            added_count = 0
            skipped_count = 0
            
            for column_name, column_type, default_value in required_columns:
                if column_name not in existing_columns:
                    try:
                        if default_value is not None:
                            query = f"ALTER TABLE payroll ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                        else:
                            query = f"ALTER TABLE payroll ADD COLUMN {column_name} {column_type}"
                        
                        db.session.execute(text(query))
                        print(f"✓ تم إضافة: {column_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"✗ خطأ في {column_name}: {str(e)}")
                else:
                    skipped_count += 1
            
            if added_count > 0:
                db.session.commit()
                print(f"\n✓ تم إضافة {added_count} عمود بنجاح!")
            else:
                print("\n✓ جميع الأعمدة موجودة بالفعل!")
            
            print(f"⚠ تم تخطي {skipped_count} عمود موجود مسبقاً")
            
            # عرض العدد النهائي للأعمدة
            result = db.session.execute(text("PRAGMA table_info(payroll)"))
            total_columns = len(result.fetchall())
            print(f"\n✓ إجمالي الأعمدة في جدول payroll: {total_columns}")
            
        except Exception as e:
            print(f"\n✗ حدث خطأ: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    add_all_payroll_columns()
