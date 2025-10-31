from flask import Blueprint, render_template, request, session
from flask_login import login_required, current_user
from app.models.attendance import Attendance
from app import db

attendance_bp = Blueprint('attendance', __name__)

from app import csrf

@attendance_bp.route('/attendance', methods=['GET'])
@login_required
def attendance():
    # TODO: Fetch attendance records for current user
    return render_template('attendance.html', lang=session.get('lang', 'ar'))

@attendance_bp.route('/api/attendance', methods=['POST'])
@csrf.exempt
@login_required
def api_attendance():
    data = request.get_json()
    action = data.get('action')
    lat = data.get('lat')
    lng = data.get('lng')
    address = data.get('address')
    from datetime import datetime, date
    from app.models.attendance import Attendance
    att = Attendance(
        employee_id=current_user.id,
        check_in_time=datetime.now() if action == 'حضور' else None,
        check_out_time=datetime.now() if action == 'انصراف' else None,
        lat=lat,
        lng=lng,
        address=address,
        status='inside',  # يمكن إضافة منطق تحديد داخل/خارج الشركة لاحقاً
        date=date.today()
    )
    db.session.add(att)
    db.session.commit()
    return {'status': 'تم تسجيل الموقع بنجاح'}

@attendance_bp.route('/attendance-map', methods=['GET'])
@login_required
def attendance_map():
    from app.models.attendance import Attendance
    from app.models.employee import Employee
    import json
    # جلب كل الحضور مع بيانات الموظف
    records = Attendance.query.join(Employee, Attendance.employee_id == Employee.id).add_columns(
        Attendance.lat, Attendance.lng, Attendance.address, Attendance.check_in_time, Attendance.check_out_time, Employee.name
    ).all()
    attendance_json = []
    for r in records:
        attendance_json.append({
            'lat': r.lat,
            'lng': r.lng,
            'address': r.address,
            'name': r.name,
            'action': 'حضور' if r.check_in_time else 'انصراف',
            'time': str(r.check_in_time or r.check_out_time)
        })
    return render_template('attendance_map.html', attendance_json=json.dumps(attendance_json), lang=session.get('lang', 'ar'))
