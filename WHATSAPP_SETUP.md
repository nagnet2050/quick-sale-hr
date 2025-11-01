# 📱 دليل إعداد WhatsApp Business API

## 🎯 الخطوة 1: إنشاء حساب Facebook Developer

1. اذهب إلى [Facebook Developers](https://developers.facebook.com/)
2. أنشئ حساب جديد أو سجل دخول
3. اضغط على "My Apps" ثم "Create App"
4. اختر "Business" كنوع التطبيق
5. املأ معلومات التطبيق

## 📞 الخطوة 2: إضافة WhatsApp Product

1. من لوحة تحكم التطبيق، اضغط على "Add Product"
2. ابحث عن "WhatsApp" واضغط "Set Up"
3. اختر أو أنشئ Business Account
4. أضف رقم هاتف للعمل (يجب أن يكون غير مسجل في واتساب عادي)

## 🔑 الخطوة 3: الحصول على Access Token

1. اذهب إلى WhatsApp > Getting Started
2. انسخ **Phone Number ID**
3. انسخ **WhatsApp Business Account ID**
4. قم بإنشاء **Permanent Access Token**:
   - اذهب إلى Settings > Basic
   - احصل على App ID و App Secret
   - استخدمهم لإنشاء توكن دائم

## 🌐 الخطوة 4: إعداد Webhook

### أ. إعداد المتغيرات البيئية

أنشئ ملف `.env` في جذر المشروع:

```env
# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN=your_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_WEBHOOK_TOKEN=your_custom_webhook_verify_token_123456

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here
```

### ب. تحديث app/config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # إعدادات موجودة...
    
    # إعدادات WhatsApp
    WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    WHATSAPP_WEBHOOK_TOKEN = os.environ.get('WHATSAPP_WEBHOOK_TOKEN')
```

### ج. إعداد الـ Webhook URL

1. **للتطوير المحلي - استخدم ngrok:**

```bash
# تثبيت ngrok
# من https://ngrok.com/download

# تشغيل ngrok
ngrok http 5000
```

سيعطيك رابط مثل: `https://abc123.ngrok.io`

2. **تسجيل الـ Webhook في Facebook:**

- اذهب إلى WhatsApp > Configuration
- اضغط "Configure Webhooks"
- أدخل:
  - **Callback URL**: `https://your-domain.com/api/whatsapp/webhook`
  - **Verify Token**: نفس قيمة `WHATSAPP_WEBHOOK_TOKEN` من `.env`
- اضغط "Verify and Save"
- اختر الـ Subscriptions: `messages`

## ✅ الخطوة 5: اختبار النظام

### 1. إرسال رسالة تجريبية:

```bash
# من WhatsApp Developer Console
# اذهب لـ API Setup
# أرسل رسالة اختبار لرقمك
```

### 2. التحقق من استقبال الرسائل:

```bash
# تشغيل السيرفر
python run.py

# في المتصفح
http://localhost:5000/whatsapp/chat
```

### 3. إرسال رسالة من النظام:

1. سجل دخول بحساب admin (1 / 1)
2. اذهب إلى "واتساب" من القائمة
3. اختر محادثة
4. أرسل رسالة نصية أو صوتية

## 🎤 الخطوة 6: تسجيل الصوت

المتصفح سيطلب صلاحية الوصول للميكروفون:
- Chrome/Edge: اضغط "Allow"
- Firefox: اضغط "Share"
- Safari: اذهب للإعدادات وفعّل الميكروفون

## 📋 قوائم التحقق

### ✅ التحقق من الإعداد الصحيح:

- [ ] Access Token صحيح
- [ ] Phone Number ID صحيح  
- [ ] Webhook URL تم التحقق منه
- [ ] Subscriptions مفعّلة (messages)
- [ ] الجداول تم إنشاؤها في قاعدة البيانات
- [ ] المسارات مسجلة في `__init__.py`
- [ ] الصلاحيات صحيحة (admin/manager فقط)

### 🔧 حل المشاكل الشائعة:

**1. Webhook Verification Failed:**
- تأكد من أن `WHATSAPP_WEBHOOK_TOKEN` متطابق
- تحقق من أن السيرفر يعمل
- تأكد من أن ngrok نشط (للتطوير المحلي)

**2. لا تصل الرسائل:**
- تحقق من Subscriptions في Webhook Config
- راجع logs السيرفر
- تأكد من صحة Access Token

**3. فشل الإرسال:**
- تحقق من Access Token
- تأكد من Phone Number ID
- راجع الرد من API في Console

**4. الميكروفون لا يعمل:**
- تأكد من أن المتصفح يدعم MediaRecorder
- امنح الصلاحيات للمتصفح
- استخدم HTTPS (أو localhost)

## 🚀 الخطوة 7: الإنتاج (Production)

### 1. استضافة السيرفر:

```bash
# مثال على Heroku
heroku create your-app-name
git push heroku main

# ضبط المتغيرات البيئية
heroku config:set WHATSAPP_ACCESS_TOKEN=xxx
heroku config:set WHATSAPP_PHONE_NUMBER_ID=xxx
```

### 2. تحديث Webhook URL:

- غيّر من ngrok إلى رابط الاستضافة الدائم
- مثال: `https://your-app.herokuapp.com/api/whatsapp/webhook`

### 3. إعدادات الأمان:

```python
# في app/whatsapp_config.py
# أضف التحقق من الـ signature
def verify_webhook_signature(payload, signature):
    import hmac
    import hashlib
    
    expected = hmac.new(
        APP_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
```

## 📊 الميزات المتاحة

### ✅ جاهزة للاستخدام:

- ✅ استقبال رسائل نصية
- ✅ استقبال رسائل صوتية
- ✅ استقبال صور
- ✅ إرسال رسائل نصية
- ✅ إرسال رسائل صوتية
- ✅ تسجيل صوتي من المتصفح
- ✅ واجهة دردشة متكاملة
- ✅ تحديث تلقائي كل 5 ثواني
- ✅ عداد الرسائل غير المقروءة
- ✅ قوالب ردود جاهزة

### 🔄 قيد التطوير:

- ⏳ إرسال صور
- ⏳ إرسال مستندات
- ⏳ إرسال فيديو
- ⏳ الردود الآلية (Chatbot)
- ⏳ تقارير المحادثات

## 🆘 الدعم

للمزيد من المساعدة:
- [WhatsApp Business API Docs](https://developers.facebook.com/docs/whatsapp)
- [Cloud API Quick Start](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
- [Webhook Reference](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)

---

**آخر تحديث**: نوفمبر 2025
**الإصدار**: 1.0
