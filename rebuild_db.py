"""
سكريبت إعادة بناء قاعدة البيانات من الصفر
يحذف قاعدة البيانات الحالية وينشئ واحدة جديدة

تحذير: هذا سيحذف جميع البيانات!
"""

import os
import sys
from datetime import datetime

# إضافة المسار الحالي لـ PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User


def backup_database():
    """عمل نسخة احتياطية من قاعدة البيانات"""
    db_path = 'instance/hrcloud.db'
    if os.path.exists(db_path):
        backup_path = f'instance/hrcloud_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✓ Backup created: {backup_path}")
        return backup_path
    return None


def rebuild_database():
    """إعادة بناء قاعدة البيانات من الصفر"""
    
    print("\n" + "="*60)
    print("⚠️  DATABASE REBUILD SCRIPT")
    print("="*60)
    print("This will DELETE all existing data and create a fresh database!")
    print()
    
    # تأكيد من المستخدم
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("\n❌ Operation cancelled.")
        return
    
    # نسخ احتياطي
    print("\n📦 Creating backup...")
    backup_path = backup_database()
    
    # حذف قاعدة البيانات الحالية
    db_path = 'instance/hrcloud.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✓ Old database removed")
    
    # إنشاء التطبيق
    app = create_app()
    
    with app.app_context():
        # إنشاء جميع الجداول
        print("\n🔨 Creating all tables...")
        db.create_all()
        print("✓ All tables created")
        
        # إنشاء مستخدم admin افتراضي
        print("\n👤 Creating default admin user...")
        admin = User(username='admin', role='admin', active=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin user created (username: admin, password: admin)")
        
    print("\n" + "="*60)
    print("✅ Database rebuild completed successfully!")
    print("="*60)
    print(f"\nBackup saved to: {backup_path if backup_path else 'No backup (database did not exist)'}")
    print("\nDefault credentials:")
    print("  Username: admin")
    print("  Password: admin")
    print("\n⚠️  Please change the default password after first login!")
    print("="*60 + "\n")


if __name__ == '__main__':
    rebuild_database()
