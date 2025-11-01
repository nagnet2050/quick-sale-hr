from app import create_app
import subprocess
import sys
import os

def auto_upgrade_database():
    """تحديث قاعدة البيانات تلقائياً عند التشغيل"""
    try:
        print("\n" + "="*60)
        print("🔄 جاري التحقق من تحديثات قاعدة البيانات...")
        print("="*60)
        
        # تشغيل flask db upgrade
        result = subprocess.run(
            ['flask', 'db', 'upgrade'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print("✅ قاعدة البيانات محدثة بنجاح!")
            if result.stdout:
                # عرض فقط السطور المهمة من الخرج
                for line in result.stdout.split('\n'):
                    if 'Running upgrade' in line or 'Context impl' in line:
                        print(f"   {line.strip()}")
        else:
            print("⚠️ تحذير: حدثت مشكلة في تحديث قاعدة البيانات")
            if result.stderr:
                print(result.stderr)
        
        print("="*60 + "\n")
        
    except FileNotFoundError:
        print("⚠️ تحذير: لم يتم العثور على flask في المسار")
        print("   يرجى التأكد من تفعيل البيئة الافتراضية")
    except Exception as e:
        print(f"⚠️ خطأ في تحديث قاعدة البيانات: {str(e)}")

app = create_app()

if __name__ == '__main__':
    # تحديث قاعدة البيانات تلقائياً قبل التشغيل
    # auto_upgrade_database()  # معطل مؤقتاً بسبب مشكلة في ملفات الترحيل
    
    # تشغيل التطبيق
    app.run(debug=True)
