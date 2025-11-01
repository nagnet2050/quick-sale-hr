<<<<<<< HEAD
# Quick Sale HR Cloud

HR Cloud Attendance System built with Flask, SQLite (upgrade-ready for PostgreSQL), SQLAlchemy, Bootstrap 5, and full Arabic/English support (RTL/LTR).

## Features
- Authentication (Admin/Employee)
# Quick-Sale-HR

HR Cloud system built with Flask, SQLAlchemy, Bootstrap 5, and full Arabic/English support (RTL/LTR). Includes Attendance, Payroll, Permissions, Support Hub, and WhatsApp integration helpers.

## Features
- Authentication (Admin/Manager/Employee), hashed passwords, CSRF
- Employee management, role/permission system with seeding
- Attendance: GPS/time/device verification, reports and settings UIs
- Payroll: monthly batches, templates, calculations and linking with attendance
- Support Hub: unified, role-aware flows (manager/employee)
- WhatsApp helpers and conversations models
- Arabic/English, RTL/LTR, modern Bootstrap 5 UI

## Run locally
1) Python 3.10+ recommended
2) Create and activate a virtual env (Windows PowerShell):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3) Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4) Run the app:
   ```powershell
   python run.py
   ```

Optional utilities:
- Initialize/seed permissions and admin mapping: `python init_permissions.py`
- Optimize DB indexes: `python optimize_database.py`
- Attendance upgrades: `python upgrade_attendance.py` / `python upgrade_attendance_advanced.py`

## Migrations
This repo includes Alembic migrations under `migrations/`. To initialize or upgrade:
```powershell
flask db upgrade
```

## Auto push changes to GitHub (Windows)
If you want every local change to be automatically committed and pushed, use the watcher script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/auto_push.ps1 -RepoPath . -Branch main -IntervalSeconds 10
```

Notes:
- Respects `.gitignore` (DB files, caches, media uploads stay out of Git).
- Pulls with `--rebase` before pushing to reduce conflicts.
- Stop anytime with Ctrl+C.

## Environment
Copy `.env.example` to `.env` and set variables as needed (SECRET_KEY, DB URL, WhatsApp keys, etc.).

## License
Copyright © 2025. All rights reserved.
- Theme color: #0D6EFD
