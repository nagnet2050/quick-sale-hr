"""
إصلاح جدول payroll - إضافة أعمدة year و month
"""

from app import create_app, db
from sqlalchemy import text

def fix_payroll_table():
    """إضافة الأعمدة المفقودة إلى جدول payroll"""
    app = create_app()
    with app.app_context():
        try:
            # فحص الأعمدة الموجودة
            result = db.session.execute(text("PRAGMA table_info(payroll)"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            print("الأعمدة الموجودة حالياً في جدول payroll:")
            for col in existing_columns:
                print(f"  - {col}")
            
            # الأعمدة المطلوب إضافتها
            columns_to_add = []
            
            if 'year' not in existing_columns:
                columns_to_add.append(('year', 'INTEGER'))
            
            if 'month' not in existing_columns:
                columns_to_add.append(('month', 'INTEGER'))
            
            if 'period_start' not in existing_columns:
                columns_to_add.append(('period_start', 'DATE'))
            
            if 'period_end' not in existing_columns:
                columns_to_add.append(('period_end', 'DATE'))
            
            # إضافة الأعمدة المفقودة
            if columns_to_add:
                print("\n" + "="*60)
                print("إضافة الأعمدة المفقودة...")
                print("="*60)
                
                for column_name, column_type in columns_to_add:
                    try:
                        query = f"ALTER TABLE payroll ADD COLUMN {column_name} {column_type}"
                        db.session.execute(text(query))
                        print(f"✓ تم إضافة العمود: {column_name}")
                    except Exception as e:
                        if "duplicate column name" in str(e).lower():
                            print(f"⚠ العمود {column_name} موجود بالفعل")
                        else:
                            print(f"✗ خطأ في إضافة العمود {column_name}: {str(e)}")
                
                db.session.commit()
                print("\n✓ تم حفظ التغييرات بنجاح!")
            else:
                print("\n✓ جميع الأعمدة موجودة بالفعل!")
            
            # عرض البنية النهائية
            print("\n" + "="*60)
            print("بنية جدول payroll النهائية:")
            print("="*60)
            result = db.session.execute(text("PRAGMA table_info(payroll)"))
            for row in result.fetchall():
                print(f"  {row[1]:25s} {row[2]:15s} {'NOT NULL' if row[3] else ''}")
            
        except Exception as e:
            print(f"\n✗ حدث خطأ: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    fix_payroll_table()
