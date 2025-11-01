# نظام Quick-Sale HR المتكامل - وثائق شاملة

## 📋 نظرة عامة على النظام

هذا نظام إدارة موارد بشرية متكامل مبني بـ **Flask 3.1.2** و **SQLAlchemy** و **SQLite3**.

### الإصدار الحالي: v1.0
- **التاريخ**: نوفمبر 2025
- **اللغات المدعومة**: العربية والإنجليزية
- **قاعدة البيانات**: SQLite3 (auto-migration enabled)
- **المصادقة**: Flask-Login + Password Hashing

---

## 🎯 الميزات الحالية المتاحة

### ✅ 1. نظام المصادقة والتفويض
- **المستخدم الافتراضي**: `1` / `1` (مسؤول)
- **الأدوار المدعومة**:
  - `admin` - مسؤول كامل (جميع الصلاحيات)
  - `manager` - مدير (إدارة الموظفين والحضور والرواتب)
  - `employee` - موظف (عرض بيانات شخصية)

**نقطة فريدة**: المستخدم برقم `1` يملك جميع الصلاحيات تلقائياً ✨

### ✅ 2. إدارة الموظفين
- **المسار**: `/employees`
- **الصلاحيات**: admin, manager
- **الميزات**:
  - إضافة موظف جديد
  - تعديل بيانات الموظف
  - حذف الموظف
  - البحث والفلترة

### ✅ 3. نظام الحضور والغياب
- **المسار**: `/attendance`
- **الصلاحيات**: admin, manager, employee
- **الميزات**:
  - تسجيل الحضور والانصراف
  - عرض سجلات الحضور
  - مؤشر الحالة (online/offline/away)
  - متابعة التواجد الفوري

**النموذج**: `EmployeePresence`
```python
- id (int)
- employee_id (int) - معرف الموظف
- status (string) - online/away/offline
- last_activity (datetime) - آخر نشاط
- session_start (datetime) - بدء الجلسة
- ip_address (string) - عنوان IP
- is_online (bool) - حالة التواجد
```

### ✅ 4. نظام الرواتب
- **المسار**: `/payroll`
- **الصلاحيات**: admin, manager
- **الميزات**:
  - إدارة الرواتب الأساسية
  - البدلات والخصومات
  - الضرائب والتأمينات
  - إنشاء كشوف الراتب (payslips)
  - تصدير Excel/PDF

### ✅ 5. إدارة الإجازات
- **المسار**: `/leave`
- **الصلاحيات**: admin, manager, employee
- **الميزات**:
  - طلب إجازة
  - الموافقة/الرفض
  - متابعة الإجازات
  - نماذج الإجازات المختلفة

### ✅ 6. تقييم الأداء
- **المسار**: `/performance`
- **الصلاحيات**: admin, manager
- **الميزات**:
  - تقييم أداء الموظفين
  - متابعة النتائج
  - تحديث التقييمات
  - تقارير الأداء

### ✅ 7. نظام شكاوى العملاء
- **المسار**: `/client-support`
- **الصلاحيات**: admin, manager
- **الميزات**:
  - تسجيل شكوى جديدة
  - رقم الهاتف + الاسم + المشكلة
  - متابعة حالة الشكوى
  - الرد على الشكاوى
  - البحث والفلترة

**النموذج**: `ClientSupport`
```python
- id (int)
- client_phone (string) - رقم الهاتف
- client_name (string) - اسم العميل
- issue (text) - المشكلة
- resolved (bool) - تم الحل؟
- escalated (bool) - تم التصعيد؟
- created_at (datetime)
- response (text) - الرد
```

### ✅ 8. متابعة الحضور الفوري
- **API**: `/api/presence/update`
- **الميزات**:
  - تحديث الحالة تلقائياً
  - كشف النشاط
  - لوحة معلومات المدير
  - أيقونات الحالة (أخضر/أصفر/رمادي)

### ✅ 9. إدارة المستخدمين والأدوار
- **المسار**: `/add_user` و `/manage_roles`
- **الصلاحيات**: admin, manager
- **الميزات**:
  - إضافة مستخدم جديد
  - تغيير الدور
  - تحديث الصلاحيات
  - **قيد الحماية**: المديرون لا يمكنهم إعطاء أدوار أعلى

### ✅ 10. إعدادات الحساب الشخصي
- **المسار**: `/account/settings`
- **الصلاحيات**: جميع المستخدمين
- **الميزات**:
  - تغيير اسم المستخدم
  - تغيير كلمة المرور
  - عرض معلومات الحساب
  - التحقق من كلمة المرور الحالية

---

## 🗂️ هيكل الملفات الحالي

```
Quick-Sale-HR/
├── app/
│   ├── __init__.py                    # تهيئة التطبيق
│   ├── config.py                      # الإعدادات
│   ├── db_manager.py                  # إدارة قاعدة البيانات التلقائية
│   ├── permissions.py                 # نظام الصلاحيات ⭐ جديد
│   ├── init_db.py                     # تهيئة قاعدة البيانات
│   ├── models/
│   │   ├── user.py                    # نموذج المستخدم
│   │   ├── employee.py                # نموذج الموظف
│   │   ├── attendance.py              # نموذج الحضور
│   │   ├── payroll.py                 # نموذج الراتب
│   │   ├── performance.py             # نموذج الأداء
│   │   ├── leave.py                   # نموذج الإجازة
│   │   ├── client_support.py          # نموذج شكاوى العملاء
│   │   ├── presence.py                # نموذج التواجد الفوري
│   │   ├── audit.py                   # نموذج التدقيق
│   │   ├── settings.py                # نموذج الإعدادات
│   │   └── ...
│   ├── routes/
│   │   ├── auth.py                    # مسارات المصادقة
│   │   ├── employees.py               # مسارات الموظفين
│   │   ├── attendance.py              # مسارات الحضور
│   │   ├── dashboard.py               # لوحة التحكم
│   │   ├── payroll.py                 # مسارات الرواتب
│   │   ├── performance.py             # مسارات الأداء
│   │   ├── leave.py                   # مسارات الإجازات
│   │   ├── user.py                    # مسارات إدارة المستخدمين
│   │   ├── client_support.py          # مسارات شكاوى العملاء
│   │   ├── presence.py                # API التواجد الفوري
│   │   ├── account.py                 # مسارات إعدادات الحساب ⭐ جديد
│   │   ├── settings.py                # مسارات الإعدادات
│   │   ├── audit.py                   # مسارات التدقيق
│   │   ├── reports.py                 # مسارات التقارير
│   │   └── ...
│   ├── templates/
│   │   ├── base.html                  # النموذج الأساسي
│   │   ├── dashboard.html             # لوحة التحكم
│   │   ├── employees.html             # صفحة الموظفين
│   │   ├── attendance.html            # صفحة الحضور
│   │   ├── payroll.html               # صفحة الرواتب
│   │   ├── account_settings.html      # إعدادات الحساب ⭐ جديد
│   │   ├── client_support.html        # صفحة شكاوى العملاء
│   │   ├── login.html                 # صفحة تسجيل الدخول
│   │   └── ...
│   └── static/
│       ├── css/
│       ├── js/
│       └── img/
├── instance/
│   └── hrcloud.db                     # قاعدة البيانات
├── run.py                             # ملف التشغيل الرئيسي
├── requirements.txt                   # المتطلبات
└── README.md                          # التوثيق الأساسي
```

---

## 🔌 API Endpoints المتاحة حالياً

### مسارات المصادقة
```
POST   /login                          # تسجيل الدخول
POST   /logout                         # تسجيل الخروج
GET    /login                          # صفحة تسجيل الدخول
```

### مسارات إدارة الموظفين
```
GET    /employees                      # عرض الموظفين
POST   /employees                      # إضافة موظف
PUT    /employees/<id>                 # تعديل موظف
DELETE /employees/<id>                 # حذف موظف
GET    /employee/<id>                  # عرض ملف الموظف
```

### مسارات الحضور
```
GET    /attendance                     # عرض سجلات الحضور
POST   /attendance                     # تسجيل حضور
DELETE /attendance/<id>                # حذف سجل
GET    /attendance/<employee_id>       # سجل موظف محدد
```

### مسارات الرواتب
```
GET    /payroll                        # عرض الرواتب
POST   /payroll                        # إضافة راتب
GET    /payroll/payslip/<id>           # كشف الراتب
GET    /payroll/export                 # تصدير PDF/Excel
```

### مسارات التواجد الفوري
```
POST   /api/presence/update            # تحديث الحالة
GET    /api/presence/status/<emp_id>   # حالة الموظف
GET    /api/presence/dashboard         # لوحة المعلومات
```

### مسارات الإجازات
```
GET    /leave                          # عرض الإجازات
POST   /leave                          # طلب إجازة
PUT    /leave/<id>/approve             # الموافقة
PUT    /leave/<id>/reject              # الرفض
```

### مسارات شكاوى العملاء
```
GET    /client-support                 # عرض الشكاوى
POST   /client-support                 # إضافة شكوى
POST   /client-support/respond/<id>    # الرد على الشكوى
```

### مسارات إدارة المستخدمين
```
GET    /add_user                       # صفحة إضافة مستخدم
POST   /add_user                       # إضافة مستخدم
GET    /manage_roles                   # صفحة إدارة الأدوار
POST   /manage_roles                   # تحديث الدور
```

### مسارات إعدادات الحساب
```
GET    /account/settings               # صفحة الإعدادات
POST   /account/settings               # تحديث البيانات
```

---

## 🔐 نظام الصلاحيات (Permissions)

### الملف: `app/permissions.py`

#### دالة `has_permission()`
```python
has_permission(['admin', 'manager'])  # يسمح للـ admin و manager
has_permission('admin')                # يسمح للـ admin فقط
```

#### ميزة خاصة: المستخدم برقم 1
- **اسم المستخدم**: `1`
- **كلمة المرور**: `1`
- **الصلاحيات**: ✨ جميع الصلاحيات بدون استثناء

```python
if current_user.username == '1':
    return True  # وصول كامل لكل شيء
```

---

## 📊 نماذج البيانات (Models)

### 1. User
```python
- id (PK)
- username (VARCHAR, UNIQUE)
- password_hash (VARCHAR)
- role (VARCHAR) - admin/manager/employee
- active (BOOL)
```

### 2. Employee
```python
- id (PK)
- code (VARCHAR)
- name (VARCHAR)
- department (VARCHAR)
- job_title (VARCHAR)
- email (VARCHAR)
- phone (VARCHAR)
- salary (FLOAT)
- active (BOOL)
```

### 3. Attendance
```python
- id (PK)
- employee_id (FK)
- date (DATE)
- time_in (TIME)
- time_out (TIME)
- location (VARCHAR)
- timestamp (DATETIME)
```

### 4. EmployeePresence
```python
- id (PK)
- employee_id (FK)
- status (VARCHAR) - online/offline/away
- last_activity (DATETIME)
- session_start (DATETIME)
- ip_address (VARCHAR)
- is_online (BOOL)
```

### 5. ClientSupport
```python
- id (PK)
- client_phone (VARCHAR)
- client_name (VARCHAR)
- issue (TEXT)
- resolved (BOOL)
- escalated (BOOL)
- response (TEXT)
- created_at (DATETIME)
```

---

## 🎯 المرحلة التالية: الميزات المخططة

### ✨ المرحلة 2.0 - القادمة

#### 1. **تحسين نظام الحضور** 🏢
- [ ] كشف النشاط التلقائي (حركة الماوس/لوحة المفاتيح)
- [ ] تقارير التواجد اليومية
- [ ] رسوم بيانية للحضور
- [ ] تنبيهات الغياب

#### 2. **نظام الإشعارات** 📢
- [ ] بريد إلكتروني
- [ ] رسائل نصية (SMS)
- [ ] Push notifications
- [ ] إشعارات داخل التطبيق

#### 3. **دمج واتساب Business API** 💬
- [ ] استقبال رسائل العملاء
- [ ] إرسال ردود فورية
- [ ] أرشيف المحادثات
- [ ] ربط برقم الهاتف

#### 4. **لوحات تحكم متقدمة** 📈
- [ ] لوحة مدير متقدمة
- [ ] لوحة موظف شخصية
- [ ] رسوم بيانية وإحصائيات
- [ ] تقارير شاملة

#### 5. **نظام التقارير** 📋
- [ ] تقارير الحضور
- [ ] تقارير الرواتب
- [ ] تقارير الأداء
- [ ] تقارير الشكاوى
- [ ] تصدير (PDF, Excel, CSV)

#### 6. **الأمان والحماية** 🔒
- [ ] تشفير البيانات الحساسة
- [ ] حدود المعدل (Rate Limiting)
- [ ] سجلات التدقيق المتقدمة
- [ ] المصادقة متعددة العوامل (2FA)

---

## 🚀 كيفية البدء

### 1. تسجيل الدخول
```
URL: http://127.0.0.1:5000/login
اسم المستخدم: 1
كلمة المرور: 1
```

### 2. الوصول إلى الصفحات الرئيسية
- **لوحة التحكم**: http://127.0.0.1:5000/dashboard
- **الموظفين**: http://127.0.0.1:5000/employees
- **الحضور**: http://127.0.0.1:5000/attendance
- **الرواتب**: http://127.0.0.1:5000/payroll
- **الإجازات**: http://127.0.0.1:5000/leave
- **شكاوى العملاء**: http://127.0.0.1:5000/client-support
- **إعدادات الحساب**: http://127.0.0.1:5000/account/settings

---

## 🛠️ التطوير والتخصيص

### إضافة مسار جديد
```python
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.permissions import has_permission

new_bp = Blueprint('new_feature', __name__)

@new_bp.route('/new-feature')
@login_required
def new_feature():
    if not has_permission(['admin']):
        return render_template('unauthorized.html')
    return render_template('new_feature.html')
```

### التحقق من الصلاحيات
```python
# في الكود
if has_permission(['admin', 'manager']):
    # قم بشيء
    pass

# في التيمبليت
{% if current_user.username == '1' or current_user.role in ['admin', 'manager'] %}
    <!-- محتوى للمسؤولين والمديرين -->
{% endif %}
```

---

## 📞 الدعم والتطوير المستقبلي

### التالي الذي يجب فعله:
1. ✅ تشغيل الخادم والتحقق من عمل جميع الصفحات
2. ⏳ إضافة نظام الإشعارات
3. ⏳ دمج واتساب Business API
4. ⏳ تحسين لوحات التحكم
5. ⏳ نظام التقارير المتقدم

### ملاحظات مهمة:
- النظام يدعم اللغة العربية والإنجليزية
- قاعدة البيانات تحدث نفسها تلقائياً (Auto-migration)
- كل المستخدمات محمية بـ CSRF Protection
- نظام الصلاحيات قابل للتوسع بسهولة

---

**آخر تحديث**: نوفمبر 1، 2025
**الحالة**: 🟢 يعمل بنجاح
**الإصدار**: 1.0
