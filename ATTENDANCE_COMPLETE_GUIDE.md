# 🎯 نظام الحضور والانصراف المتكامل - دليل شامل

## 📋 نظرة عامة على النظام

نظام حضور وانصراف متطور ومتكامل يشمل:

### ✅ الميزات الأساسية
1. **التحقق الثلاثي:**
   - 📍 الموقع GPS (Geolocation)
   - ⏰ الوقت (Time-based)
   - 💻 الجهاز (Device Fingerprinting/MAC)

2. **RBAC (Role-Based Access Control):**
   - قواعد مخصصة للأدوار
   - صلاحيات حسب المستخدم/القسم/الموقع
   - منع التسجيل للأجهزة غير المصرح بها

3. **التكامل مع الرواتب:**
   - حساب التأخير تلقائياً
   - حساب الغياب والخصومات
   - حساب الساعات الإضافية والمكافآت
   - ربط مباشر مع نظام Payroll

4. **التقارير المتقدمة:**
   - لوحة تحكم يومية/أسبوعية/شهرية
   - متوسط التأخير لكل موظف
   - Top Late Employees
   - إحصائيات المخالفات

5. **Offline Support:**
   - Queue للسجلات أثناء عدم الاتصال
   - Delta Sync للمزامنة الذكية
   - دعم Web وMobile وDesktop

6. **تطبيق macOS:**
   - Tauri + Rust
   - الوصول الحقيقي لـ MAC Address
   - قراءة SSID للشبكة
   - Serial Number للجهاز
   - تخزين آمن في Keychain

---

## 🗄️ بنية قاعدة البيانات

### الجداول الأساسية

#### 1. `attendance` (محدّث)
```sql
- id (PK)
- employee_id (FK)
- date
- check_in_time
- check_out_time
- lat, lng, address
- lat_out, lng_out, address_out
- mac_address ⭐ جديد
- device_info ⭐ جديد
- location_verified ⭐ جديد
- time_verified ⭐ جديد
- device_verified ⭐ جديد
- verification_notes ⭐ جديد
- status
```

#### 2. `attendance_settings` (محدّث)
```sql
- id (PK)
- company_lat, company_lng
- max_distance_meters
- check_in_start, check_in_end
- check_out_start, check_out_end
- require_location_verification
- require_time_verification
- require_device_verification
- allow_outside_hours
- auto_link_payroll ⭐ جديد
- late_deduction_per_minute ⭐ جديد
- absence_deduction_per_day ⭐ جديد
- overtime_bonus_per_hour ⭐ جديد
- grace_period_minutes ⭐ جديد
- min_work_hours_per_day ⭐ جديد
```

#### 3. `registered_device` (جديد)
```sql
- id (PK)
- employee_id (FK)
- mac_address (UNIQUE)
- device_name
- device_info
- is_active
- registered_at
- last_used
```

#### 4. `attendance_report` (جديد)
```sql
- id (PK)
- employee_id (FK)
- period_type (daily/weekly/monthly)
- period_start, period_end
- total_days, present_days, absent_days, late_days
- total_work_minutes
- total_late_minutes
- total_overtime_minutes
- average_late_minutes
- location_violations
- time_violations
- device_violations
- linked_to_payroll
- payroll_id (FK)
- generated_at, generated_by
```

#### 5. `attendance_sync` (جديد - Offline)
```sql
- id (PK)
- employee_id (FK)
- action (check_in/check_out)
- timestamp
- lat, lng, address
- mac_address, device_info
- sync_status (pending/synced/failed)
- sync_attempts
- last_sync_attempt
- error_message
- original_data (JSON)
- created_at, synced_at
```

#### 6. `attendance_rbac` (جديد)
```sql
- id (PK)
- rule_name, description
- rule_type (user/role/department/device/location/time)
- applies_to (JSON)
- can_check_in, can_check_out, can_check_for_others
- allowed_devices (JSON)
- allowed_locations (JSON)
- allowed_time_ranges (JSON)
- is_active, priority
- created_at, created_by, updated_at
```

#### 7. `payroll_attendance_link` (جديد)
```sql
- id (PK)
- payroll_id (FK)
- report_id (FK)
- late_deduction_amount
- absence_deduction_amount
- overtime_bonus_amount
- late_deduction_rate
- absence_deduction_rate
- overtime_bonus_rate
- auto_calculated
- approved, approved_by, approved_at
- created_at, updated_at
```

---

## 🔧 API Reference

### 1. تسجيل الحضور/الانصراف

**Endpoint:** `POST /api/attendance`

**Request:**
```json
{
  "action": "حضور",
  "employee_id": 123,
  "lat": 30.0444,
  "lng": 31.2357,
  "address": "Cairo, Egypt",
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "device_info": "Windows 11 - Chrome"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "تم تسجيل الحضور بنجاح",
  "verification_details": {
    "location": {
      "verified": true,
      "message": "الموقع صحيح (المسافة: 45 متر)"
    },
    "time": {
      "verified": true,
      "message": "الوقت مناسب للحضور"
    },
    "device": {
      "verified": true,
      "message": "الجهاز مسجل: Laptop"
    }
  }
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "فشل التحقق من الموقع",
  "verification_details": { ... }
}
```

### 2. إدارة الأجهزة

#### تسجيل جهاز جديد
`POST /api/attendance/register-device`
```json
{
  "employee_id": 123,
  "mac_address": "00:11:22:33:44:55",
  "device_name": "Laptop - Ahmed",
  "device_info": "Windows 11"
}
```

#### قائمة أجهزة الموظف
`GET /api/attendance/devices/{employee_id}`

#### حذف جهاز
`DELETE /api/attendance/device/{device_id}`

#### تفعيل/تعطيل جهاز
`POST /api/attendance/device/{device_id}/toggle`

### 3. التقارير

#### إحصائيات التأخير
`GET /api/attendance/reports/late-stats?period=month&limit=10`

**Response:**
```json
{
  "period": "month",
  "start_date": "2025-11-01",
  "overall_average_late_minutes": 23.5,
  "total_late_employees": 15,
  "top_late_employees": [
    {
      "id": 123,
      "name": "أحمد محمد",
      "department": "المبيعات",
      "total_late_minutes": 450,
      "late_count": 12,
      "average_late_minutes": 37.5
    }
  ]
}
```

#### توليد تقرير
`POST /api/attendance/reports/generate`
```json
{
  "employee_id": 123,
  "period_type": "monthly",
  "period_start": "2025-11-01",
  "period_end": "2025-11-30"
}
```

### 4. التكامل مع الرواتب

#### ربط تقرير بالراتب
`POST /api/attendance/link-to-payroll`
```json
{
  "report_id": 45,
  "payroll_id": 78
}
```

**Response:**
```json
{
  "status": "success",
  "message": "تم ربط الحضور بالراتب بنجاح",
  "link": {
    "late_deduction": 120.0,
    "absence_deduction": 300.0,
    "overtime_bonus": 250.0,
    "total_adjustment": -170.0
  },
  "payroll": {
    "id": 78,
    "gross_salary": 5250.0,
    "total_deductions": 420.0,
    "net": 4830.0
  }
}
```

### 5. Offline Support

#### إضافة لقائمة المزامنة
`POST /api/attendance/sync/queue`
```json
{
  "employee_id": 123,
  "action": "check_in",
  "timestamp": "2025-11-01T08:30:00Z",
  "lat": 30.0444,
  "lng": 31.2357,
  "address": "Cairo",
  "mac_address": "a1:b2:c3:d4:e5:f6"
}
```

#### معالجة قائمة المزامنة
`POST /api/attendance/sync/process`

**Response:**
```json
{
  "status": "success",
  "processed": 15,
  "failed": 2,
  "remaining": 0
}
```

### 6. الإعدادات

#### جلب الإعدادات
`GET /api/attendance/settings`

#### تحديث الإعدادات
`POST /api/attendance/settings`
```json
{
  "company_lat": 30.0444,
  "company_lng": 31.2357,
  "max_distance_meters": 100,
  "check_in_start": "07:00",
  "check_in_end": "10:00",
  "check_out_start": "14:00",
  "check_out_end": "18:00",
  "require_location_verification": true,
  "require_time_verification": true,
  "require_device_verification": false,
  "allow_outside_hours": false,
  "late_deduction_per_minute": 1.0,
  "absence_deduction_per_day": 100.0,
  "overtime_bonus_per_hour": 50.0
}
```

---

## 📱 الواجهات

### 1. صفحة الحضور والانصراف
**المسار:** `/attendance`

**الميزات:**
- تسجيل حضور/انصراف
- عرض السجلات
- إحصائيات اليوم
- رابط للإعدادات (للمسؤولين)

### 2. صفحة إعدادات الحضور
**المسار:** `/attendance/settings`
**الصلاحية:** Admin فقط

**الأقسام:**
- إعدادات الموقع
- إعدادات الوقت
- إعدادات الأجهزة
- إعدادات الربط بالرواتب

### 3. لوحة التقارير
**المسار:** `/attendance/reports/dashboard`
**الصلاحية:** Manager, Admin

**المحتوى:**
- إحصائيات عامة (اليوم/الأسبوع/الشهر)
- متوسط التأخير
- Top 5 Late Employees
- أدوات إنشاء التقارير
- ربط بالرواتب

---

## 🔐 RBAC - أمثلة القواعد

### القاعدة 1: المسؤولون
```json
{
  "rule_name": "Admin Full Access",
  "rule_type": "role",
  "applies_to": ["admin"],
  "can_check_in": true,
  "can_check_out": true,
  "can_check_for_others": true,
  "priority": 100
}
```

### القاعدة 2: المديرون
```json
{
  "rule_name": "Manager Team Access",
  "rule_type": "role",
  "applies_to": ["manager"],
  "can_check_in": true,
  "can_check_out": true,
  "can_check_for_others": true,
  "allowed_departments": ["Sales", "Marketing"],
  "priority": 50
}
```

### القاعدة 3: الموظفون
```json
{
  "rule_name": "Employee Self Only",
  "rule_type": "role",
  "applies_to": ["employee"],
  "can_check_in": true,
  "can_check_out": true,
  "can_check_for_others": false,
  "priority": 10
}
```

### القاعدة 4: قيود الموقع
```json
{
  "rule_name": "Office Only",
  "rule_type": "location",
  "allowed_locations": [
    {
      "name": "Main Office",
      "lat": 30.0444,
      "lng": 31.2357,
      "radius": 100
    }
  ],
  "priority": 30
}
```

### القاعدة 5: قيود الأجهزة
```json
{
  "rule_name": "Registered Devices Only",
  "rule_type": "device",
  "allowed_devices": ["aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"],
  "priority": 40
}
```

---

## 🚀 سيناريوهات الاستخدام

### السيناريو 1: موظف يسجل حضوراً عادياً
```
1. الموظف يفتح التطبيق/الموقع
2. يضغط "حضور"
3. النظام يجمع:
   - الموقع GPS
   - الوقت الحالي
   - معرف الجهاز
4. التحقق:
   ✓ الموقع: 45 متر من المقر (ضمن 100 متر)
   ✓ الوقت: 8:30 ص (ضمن 7:00-10:00)
   ✓ الجهاز: مسجل
5. النتيجة: تم التسجيل بنجاح ✅
```

### السيناريو 2: موظف متأخر
```
1. الموظف يحاول التسجيل الساعة 10:45 ص
2. التحقق:
   ✓ الموقع: صحيح
   ✗ الوقت: 10:45 (خارج 7:00-10:00)
   ✓ الجهاز: مسجل
3. النتيجة:
   - إذا allow_outside_hours = false: رفض ❌
   - إذا allow_outside_hours = true: قبول مع تحذير ⚠️
4. في حالة القبول:
   - يُسجّل التأخير: 45 دقيقة
   - يُحسب الخصم: 45 × 1 جنيه = 45 جنيه
```

### السيناريو 3: موظف يعمل ساعات إضافية
```
1. الموظف يسجل حضور: 8:00 ص
2. الموظف يسجل انصراف: 6:30 م
3. ساعات العمل: 10.5 ساعة
4. الحد الأدنى: 8 ساعات
5. الساعات الإضافية: 2.5 ساعة
6. المكافأة: 2.5 × 50 جنيه = 125 جنيه ✅
```

### السيناريو 4: Offline - ثم Sync
```
1. الموظف في منطقة بدون إنترنت
2. يسجل حضور: يُحفظ محلياً في Queue
3. عند عودة الاتصال:
4. النظام يستدعي /api/attendance/sync/process
5. يُرسل كل السجلات المعلقة
6. يُحدث الحالة: pending → synced ✅
```

---

## 📊 حسابات الرواتب التلقائية

### مثال عملي

**بيانات الموظف:**
- الراتب الأساسي: 5000 جنيه
- عدد أيام العمل: 22 يوم
- أيام الحضور: 20 يوم
- أيام الغياب: 2 يوم
- عدد مرات التأخير: 5 مرات
- إجمالي دقائق التأخير: 120 دقيقة
- ساعات العمل الإضافية: 15 ساعة

**الإعدادات:**
- خصم التأخير: 1 جنيه/دقيقة
- خصم الغياب: 100 جنيه/يوم
- مكافأة الإضافي: 50 جنيه/ساعة

**الحسابات:**
```
خصم التأخير = 120 × 1 = 120 جنيه
خصم الغياب = 2 × 100 = 200 جنيه
مكافأة الإضافي = 15 × 50 = 750 جنيه

إجمالي الخصومات = 120 + 200 = 320 جنيه
الراتب الإجمالي = 5000 + 750 = 5750 جنيه
الراتب الصافي = 5750 - 320 = 5430 جنيه ✅
```

---

## 🍎 تطبيق macOS

### الميزات الفريدة
1. **MAC Address حقيقي** من واجهة الشبكة
2. **Serial Number** من IOKit
3. **SSID** للشبكة الحالية
4. **Keychain** للتخزين الآمن
5. **Offline Queue** مع Auto-Sync

### التثبيت
```bash
# تحميل التطبيق من App Store (مستقبلاً)
# أو تثبيت من DMG
open QuickSaleHR-Attendance.dmg
```

### الاستخدام
```
1. فتح التطبيق
2. تسجيل الدخول (يُحفظ في Keychain)
3. السماح بالوصول للموقع
4. ضغط "حضور" أو "انصراف"
5. في حالة Offline: يُحفظ محلياً
6. عند عودة الاتصال: مزامنة تلقائية
```

---

## 📈 الإحصائيات والتقارير

### التقارير المتاحة

#### 1. تقرير يومي
- عدد الحضور/الانصراف
- المتأخرون
- الغائبون
- المخالفات

#### 2. تقرير أسبوعي
- متوسط الحضور
- متوسط التأخير
- إجمالي ساعات العمل
- Top Late (أكثر 5 متأخرين)

#### 3. تقرير شهري
- نسبة الحضور
- إجمالي الغياب
- إجمالي الساعات الإضافية
- التكاليف (خصومات ومكافآت)

---

## 🔧 التثبيت والإعداد

### 1. تحديث قاعدة البيانات
```bash
python upgrade_attendance.py
python upgrade_attendance_advanced.py
```

### 2. تكوين الإعدادات
- الذهاب إلى `/attendance/settings`
- ضبط موقع الشركة
- تحديد أوقات العمل
- تفعيل أنواع التحقق المطلوبة
- ضبط معدلات الخصم/المكافآت

### 3. تسجيل الأجهزة (اختياري)
```bash
# عبر API
POST /api/attendance/register-device
{
  "employee_id": 123,
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "device_name": "Laptop - Ahmed"
}
```

---

## 🎓 أفضل الممارسات

1. **فترة السماح:** اضبط `grace_period_minutes` على 15 دقيقة
2. **الموقع:** حدد `max_distance_meters` على 100-200 متر حسب حجم المقر
3. **الأجهزة:** فعّل التحقق من الأجهزة للوظائف الحساسة فقط
4. **التقارير:** أنشئ تقارير شهرية تلقائياً
5. **المزامنة:** شغّل مزامنة Offline كل 30 دقيقة

---

**تم التطوير بواسطة GitHub Copilot** 🤖
**الإصدار:** 2.0
**التاريخ:** نوفمبر 2025
