# QuickSale HR - Attendance App for macOS

<div align="center">

![macOS](https://img.shields.io/badge/macOS-10.13+-blue)
![Tauri](https://img.shields.io/badge/Tauri-1.5-orange)
![Rust](https://img.shields.io/badge/Rust-1.70+-red)
![Vue](https://img.shields.io/badge/Vue-3.0-green)

تطبيق حضور وانصراف أصلي لـ macOS

</div>

## ⭐ الميزات

- ✅ **MAC Address حقيقي** من واجهة الشبكة
- ✅ **Serial Number** من IOKit
- ✅ **Wi-Fi SSID** للتحقق من الشبكة
- ✅ **macOS Keychain** للتخزين الآمن
- ✅ **Offline Queue** مع مزامنة تلقائية
- ✅ **GPS Location** دقيق
- ✅ **حجم صغير** (~10-15 MB)

## 🚀 البدء السريع

### المتطلبات

```bash
# Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Tauri CLI
cargo install tauri-cli

# Node.js
brew install node
```

### التثبيت

```bash
# نسخ المشروع
git clone https://github.com/nagnet2050/Quick-Sale-HR.git
cd Quick-Sale-HR/attendance-macos

# تثبيت التبعيات
npm install

# التطوير
cargo tauri dev

# البناء
cargo tauri build
```

## 📱 الاستخدام

### 1. تسجيل الدخول
```javascript
await invoke('save_credentials', { 
  username: 'ahmed', 
  password: 'secret' 
});
```

### 2. الحصول على معلومات الجهاز
```javascript
const deviceInfo = await invoke('get_device_info');
// { mac: "aa:bb:cc:dd:ee:ff", serial: "C02XYZ", ssid: "Office-WiFi" }
```

### 3. تسجيل الحضور
```javascript
await invoke('check_in', {
  employeeId: 123,
  lat: 30.0444,
  lng: 31.2357
});
```

### 4. مزامنة السجلات
```javascript
const result = await invoke('sync_queue');
// "تم مزامنة 5 سجل، فشل 0"
```

## 🏗️ البنية

```
attendance-macos/
├── src-tauri/           # Rust backend
│   ├── src/
│   │   ├── main.rs      # Entry point
│   │   ├── mac_utils.rs # MAC, Serial, SSID
│   │   └── keychain.rs  # Keychain access
│   └── Cargo.toml
├── src/                 # Vue frontend
│   ├── App.vue
│   └── components/
└── package.json
```

## 🔐 الأمان

- **Code Signing:** التطبيق موقع رقمياً
- **Sandboxing:** بيئة معزولة
- **Keychain:** تخزين آمن للبيانات الحساسة
- **HTTPS Only:** كل الاتصالات مشفرة

## 📦 البناء للإنتاج

```bash
cargo tauri build
```

**الناتج:**
- `QuickSale-Attendance.dmg` - للتوزيع
- `QuickSale-Attendance.app` - للتثبيت المباشر

## 🛠️ التخصيص

### تغيير عنوان السيرفر

في `main.rs`:
```rust
let response = client
    .post("https://your-server.com/api/attendance")
    .json(record)
    .send()
    .await?;
```

### إضافة شبكات Wi-Fi مسموحة

في `mac_utils.rs`:
```rust
let allowed_ssids = vec![
    "QuickSale-Office".to_string(),
    "QuickSale-Guest".to_string()
];
```

## 📖 التوثيق الكامل

راجع [MACOS_APP_GUIDE.md](../MACOS_APP_GUIDE.md) للدليل الشامل.

## 🐛 الإبلاغ عن المشاكل

[فتح Issue جديد](https://github.com/nagnet2050/Quick-Sale-HR/issues)

## 📄 الترخيص

MIT License

---

Made with ❤️ using Tauri + Rust + Vue
