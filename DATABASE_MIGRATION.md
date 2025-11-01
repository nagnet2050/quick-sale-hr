# نظام التحديث التلقائي لقاعدة البيانات

## نظرة عامة

تم إنشاء نظام تحديث تلقائي لقاعدة البيانات يعمل عند بدء تشغيل التطبيق. هذا النظام يقوم بـ:

1. **إنشاء الجداول المفقودة** - يتحقق من وجود جميع الجداول المطلوبة وينشئها إذا لم تكن موجودة
2. **إضافة الأعمدة الناقصة** - يضيف أي أعمدة جديدة تم تعريفها في Models ولم تكن موجودة في قاعدة البيانات
3. **تحديث البنية التلقائي** - يحدث بنية الجداول حسب احتياجات الصفحات والـ Models

## الملفات الرئيسية

### `app/db_manager.py`
يحتوي على جميع دوال إدارة قاعدة البيانات:

- `get_table_columns(table_name)` - الحصول على أسماء الأعمدة الموجودة
- `add_column_if_not_exists(table_name, column_name, column_type)` - إضافة عمود إذا لم يكن موجوداً
- `update_database_schema()` - تحديث بنية جميع الجداول
- `create_missing_tables()` - إنشاء الجداول المفقودة
- `auto_migrate_database()` - الدالة الرئيسية التي تستدعى عند بدء التطبيق

### `app/__init__.py`
يستدعي نظام التحديث التلقائي عند إنشاء التطبيق:

```python
with app.app_context():
    from app.db_manager import auto_migrate_database
    auto_migrate_database()
```

## كيفية إضافة جدول أو عمود جديد

### 1. إضافة جدول جديد

**الخطوة 1:** أنشئ Model جديد في `app/models/`

```python
from app import db

class NewTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**الخطوة 2:** أضف الاستيراد في `app/db_manager.py` في دالة `create_missing_tables()`:

```python
from app.models.new_table import NewTable
```

**الخطوة 3:** (اختياري) إذا كنت تريد إضافة أعمدة إضافية عبر SQL، أضف في قاموس `schema_updates`:

```python
'new_table': [
    ('column1', 'VARCHAR(64)'),
    ('column2', 'INTEGER DEFAULT 0')
]
```

**الخطوة 4:** أعد تشغيل التطبيق - سيتم إنشاء الجدول تلقائياً!

### 2. إضافة عمود جديد لجدول موجود

**الخطوة 1:** أضف العمود في Model:

```python
class Employee(db.Model):
    # ... الأعمدة الموجودة
    new_column = db.Column(db.String(64))  # عمود جديد
```

**الخطوة 2:** أضف العمود في قاموس `schema_updates` في `app/db_manager.py`:

```python
'employee': [
    # ... الأعمدة الموجودة
    ('new_column', 'VARCHAR(64)')
]
```

**الخطوة 3:** أعد تشغيل التطبيق - سيتم إضافة العمود تلقائياً!

## مثال على الإخراج عند بدء التطبيق

```
============================================================
🔄 Starting Database Auto-Migration...
============================================================
✓ All tables created/verified

📝 Schema Updates Applied:
  ✓ Added username to employee
  ✓ Added password_hash to employee
  ✓ Added payment_date to payroll
  ✓ Added payment_method to payroll

============================================================
✅ Database Migration Completed Successfully
============================================================
```

## الجداول المدعومة حالياً

- **employee** - بيانات الموظفين
- **user** - حسابات المستخدمين
- **payroll** - الرواتب
- **leave** - الإجازات
- **performance** - تقييم الأداء
- **attendance** - الحضور والانصراف
- **whatsapp_messages** - رسائل واتساب
- **customer_complaint** - شكاوى العملاء
- **employee_presence** - حالة تواجد الموظفين
- **settings** - إعدادات النظام

## ملاحظات مهمة

1. **النسخ الاحتياطي**: يُنصح بعمل نسخة احتياطية من قاعدة البيانات قبل إضافة تغييرات كبيرة
2. **SQLite Limitations**: SQLite لا يدعم تعديل أو حذف الأعمدة، فقط الإضافة
3. **Production**: في بيئة الإنتاج، يُفضل استخدام Alembic migrations للتحكم الأفضل

## استكشاف الأخطاء

### الخطأ: "table already exists"
- هذا طبيعي إذا كان الجدول موجود مسبقاً
- النظام يتجاهل هذا الخطأ تلقائياً

### الخطأ: "duplicate column name"
- العمود موجود بالفعل
- النظام يتحقق قبل الإضافة لتجنب هذا

### الخطأ: "cannot import name..."
- تأكد من أن اسم الكلاس في Model يطابق الاسم في الاستيراد
- تأكد من وجود الملف في المسار الصحيح

## المميزات

✅ **تلقائي بالكامل** - لا حاجة لتشغيل سكريبتات يدوياً
✅ **آمن** - يتحقق قبل إضافة أي شيء
✅ **سريع** - يعمل فقط عند بدء التطبيق
✅ **واضح** - يعرض log مفصل لكل عملية
✅ **مرن** - سهل الإضافة والتعديل

## الترقيات المستقبلية

- [ ] دعم تعديل نوع العمود
- [ ] دعم حذف الأعمدة (مع تحذيرات)
- [ ] Migration history tracking
- [ ] Rollback functionality
- [ ] دعم قواعد بيانات أخرى (PostgreSQL, MySQL)
