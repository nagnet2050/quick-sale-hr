<<<<<<< HEAD
# Quick Sale HR Cloud

HR Cloud Attendance System built with Flask, SQLite (upgrade-ready for PostgreSQL), SQLAlchemy, Bootstrap 5, and full Arabic/English support (RTL/LTR).

## Features
- Authentication (Admin/Employee)
- Employee Management (CRUD)
- GPS Attendance (Check-in/out, location, company radius)
- Presence Monitoring (popup, sound, auto-absent)
- Dashboard (attendance status, headcount, shortcuts)
- Language switch (Arabic/English, RTL/LTR)
- Security (hashed passwords, CSRF, HTTPS)
- Mobile-first, SaaS-style UI

## Directory Structure
```
app/
  routes/
  templates/
  static/
  models/
  config.py
run.py
requirements.txt
README.md
```

## How to Run Locally
1. Install Python 3.9+
2. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Initialize the database:
   ```
   python app/init_db.py
   ```
5. Create admin user:
   ```
   python app/create_admin.py
   ```
6. Run the app:
   ```
   python run.py
   ```

## Deploy to Render.com
- Set environment variables: `SECRET_KEY`, `DATABASE_URL` (PostgreSQL)
- Use Gunicorn for production:
  ```
  gunicorn run:app
  ```
- Add build and start commands in Render dashboard

## Demo Data
- Use `app/demo_data.py` to populate sample employees and attendance records.

## Branding
- Theme color: #0D6EFD
- Fonts: Cairo (Arabic), Open Sans (English)
- Logo: Cloud HR (placeholder in `/static/img/logo.png`)

## Future Modules
- Face recognition
- Offline mode
- Payroll

---
جميع الشاشات تدعم اللغة العربية بالكامل (اتجاه الكتابة من اليمين إلى اليسار).
=======
# Quick-Sale-HR
>>>>>>> 2f7024bad354160398caf85e726059d30b430684
