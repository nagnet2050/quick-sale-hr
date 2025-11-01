from flask import Blueprint, render_template, request, session, current_app, jsonify
from flask_login import login_required, current_user
from app.models.attendance import Attendance, AttendanceSettings, RegisteredDevice
from sqlalchemy import inspect, text
from app import db, csrf
from app.models.employee import Employee
from app.permissions import has_permission
from flask_wtf.csrf import CSRFError
from flask import flash, redirect, url_for
from datetime import datetime, date, time
from math import radians, cos, sin, asin, sqrt
import csv
from io import StringIO

attendance_bp = Blueprint('attendance', __name__)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    حساب المسافة بين نقطتين GPS بالمتر باستخدام Haversine formula
    """
    # تحويل من درجات إلى راديان
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # نصف قطر الأرض بالكيلومتر
    r = 6371
    
    # المسافة بالمتر
    return c * r * 1000


def verify_location(lat, lng):
    """
    التحقق من أن الموقع داخل النطاق المسموح
    """
    settings = AttendanceSettings.query.first()
    if not settings:
        # إنشاء إعدادات افتراضية
        settings = AttendanceSettings()
        db.session.add(settings)
        db.session.commit()
    
    if not settings.require_location_verification:
        return True, "التحقق من الموقع معطل"
    
    if not lat or not lng:
        return False, "الموقع غير متوفر"
    
    distance = calculate_distance(
        settings.company_lat,
        settings.company_lng,
        lat,
        lng
    )
    
    if distance <= settings.max_distance_meters:
        return True, f"الموقع صحيح (المسافة: {int(distance)} متر)"
    else:
        return False, f"الموقع بعيد عن الشركة (المسافة: {int(distance)} متر، المسموح: {settings.max_distance_meters} متر)"


def verify_time(action):
    """
    التحقق من أن الوقت ضمن ساعات العمل المسموحة
    """
    settings = AttendanceSettings.query.first()
    if not settings:
        settings = AttendanceSettings()
        db.session.add(settings)
        db.session.commit()
    
    if not settings.require_time_verification:
        return True, "التحقق من الوقت معطل"
    
    current_time = datetime.now().time()
    
    if action == 'حضور':
        if settings.check_in_start <= current_time <= settings.check_in_end:
            return True, f"الوقت مناسب للحضور"
        else:
            if settings.allow_outside_hours:
                return True, f"تسجيل خارج الأوقات المحددة ({settings.check_in_start.strftime('%H:%M')} - {settings.check_in_end.strftime('%H:%M')})"
            return False, f"الوقت غير مناسب للحضور (الأوقات المسموحة: {settings.check_in_start.strftime('%H:%M')} - {settings.check_in_end.strftime('%H:%M')})"
    
    elif action == 'انصراف':
        if settings.check_out_start <= current_time <= settings.check_out_end:
            return True, f"الوقت مناسب للانصراف"
        else:
            if settings.allow_outside_hours:
                return True, f"تسجيل خارج الأوقات المحددة ({settings.check_out_start.strftime('%H:%M')} - {settings.check_out_end.strftime('%H:%M')})"
            return False, f"الوقت غير مناسب للانصراف (الأوقات المسموحة: {settings.check_out_start.strftime('%H:%M')} - {settings.check_out_end.strftime('%H:%M')})"
    
    return True, ""


def verify_device(employee_id, mac_address):
    """
    التحقق من أن الجهاز مسجل للموظف
    """
    settings = AttendanceSettings.query.first()
    if not settings or not settings.require_device_verification:
        return True, "التحقق من الجهاز معطل"
    
    if not mac_address:
        return False, "MAC Address غير متوفر"
    
    device = RegisteredDevice.query.filter_by(
        employee_id=employee_id,
        mac_address=mac_address,
        is_active=True
    ).first()
    
    if device:
        # تحديث آخر استخدام
        device.last_used = datetime.now()
        db.session.commit()
        return True, f"الجهاز مسجل: {device.device_name or mac_address}"
    else:
        return False, f"الجهاز غير مسجل للموظف (MAC: {mac_address})"


@attendance_bp.route('/attendance', methods=['GET'])
@login_required
def attendance():
    if not current_user.has_any_permission(module='attendance', actions=['view', 'view_own']):
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard.dashboard'))

    attendance_log = []
    search_name = request.args.get('search_name', '').strip()
    search_date = request.args.get('search_date', '').strip()
    query = Attendance.query.join(Employee, Attendance.employee_id == Employee.id)

    # إذا كان المستخدم لديه صلاحية عرض سجلاته فقط
    if not current_user.has_permission(module='attendance', action='view'):
        query = query.filter(Attendance.employee_id == current_user.id)
    
    if search_date:
        from datetime import datetime
        try:
            date_obj = datetime.strptime(search_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date == date_obj)
        except ValueError:
            flash('تنسيق التاريخ غير صالح. استخدم YYYY-MM-DD', 'warning')

    if search_name:
        query = query.filter(Employee.name.ilike(f"%{search_name}%"))

    records = query.order_by(Attendance.date.desc(), Attendance.check_in_time.desc()).limit(200).all()
    
    attendance_log = []
    for att in records:
        emp = att.employee # Access the joined employee object
        attendance_log.append({
            'id': att.id,
            'action': 'حضور' if att.check_in_time else 'انصراف',
            'time': att.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if att.check_in_time else (att.check_out_time.strftime('%Y-%m-%d %H:%M:%S') if att.check_out_time else ''),
            'address': att.address,
            'name': emp.name if emp else 'موظف غير معروف'
        })
    
    # تحديد الموظفين الذين يمكن تسجيل حضورهم
    employees = []
    if current_user.has_permission(module='attendance', action='view'):
        # المدير يمكنه تسجيل حضور جميع الموظفين
        employees = Employee.query.filter_by(active=True).order_by(Employee.name).all()
    else:
        # الموظف العادي يسجل حضوره فقط
        # محاولة الحصول على معلومات الموظف من session أو username
        employee_id = session.get('employee_id')
        if employee_id:
            employee = Employee.query.get(employee_id)
            if employee:
                employees = [employee]
        elif current_user.username.startswith('emp_'):
            # استخراج ID الموظف من username
            try:
                emp_id = int(current_user.username.split('_')[1])
                employee = Employee.query.get(emp_id)
                if employee:
                    employees = [employee]
            except:
                pass
        
        # إذا لم نجد الموظف بعد، نحاول البحث برقم المستخدم
        if not employees and current_user.username.isdigit():
            employee = Employee.query.get(int(current_user.username))
            if employee:
                employees = [employee]
    
    # حساب إحصائيات اليوم
    from datetime import date
    today = date.today()
    today_checkins = Attendance.query.filter(
        Attendance.date == today,
        Attendance.check_in_time.isnot(None)
    ).count()
    today_checkouts = Attendance.query.filter(
        Attendance.date == today,
        Attendance.check_out_time.isnot(None)
    ).count()
    
    return render_template('attendance.html', 
                         lang=session.get('lang', 'ar'), 
                         attendance_log=attendance_log,
                         employees=employees,
                         today_checkins=today_checkins,
                         today_checkouts=today_checkouts)


@attendance_bp.route('/api/attendance/import', methods=['POST'])
@login_required
def import_attendance_csv():
    """استيراد سجلات الحضور من ملف CSV.
    تنسيقات الأعمدة المدعومة (case-insensitive):
      - date, employee_id, check_in, check_out
      - date, employee_code, check_in, check_out
    التاريخ بصيغة YYYY-MM-DD؛ الأوقات HH:MM أو HH:MM:SS.
    إذا وُجد سجل لنفس (employee_id, date) يتم التحديث بدلاً من الإنشاء.
    """
    if not current_user.has_permission(module='attendance', action='edit'):
        return jsonify({'status': 'error', 'message': 'غير مصرح لك'}), 403

    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'لم يتم إرفاق ملف'}), 400

    f = request.files['file']
    if not f or f.filename == '':
        return jsonify({'status': 'error', 'message': 'اسم الملف غير صالح'}), 400

    try:
        content = f.read().decode('utf-8-sig')
        reader = csv.DictReader(StringIO(content))
        required_cols = set([c.lower() for c in reader.fieldnames or []])
        if not required_cols:
            return jsonify({'status': 'error', 'message': 'ملف CSV فارغ أو بدون رأس'}), 400

        count_created = 0
        count_updated = 0
        errors = []

        for i, row in enumerate(reader, start=2):  # يبدأ العد من 2 (بعد الرأس)
            try:
                # قراءة الحقول مع عدة احتمالات للأسماء
                date_str = row.get('date') or row.get('Date') or row.get('DATE')
                emp_id = row.get('employee_id') or row.get('emp_id')
                emp_code = row.get('employee_code') or row.get('code')
                check_in = row.get('check_in') or row.get('in') or row.get('checkin')
                check_out = row.get('check_out') or row.get('out') or row.get('checkout')

                if not date_str or not (emp_id or emp_code):
                    errors.append(f'سطر {i}: بيانات ناقصة (date/employee)')
                    continue

                # حدد الموظف
                employee = None
                if emp_id:
                    try:
                        employee = Employee.query.get(int(emp_id))
                    except Exception:
                        employee = None
                if not employee and emp_code:
                    employee = Employee.query.filter_by(code=str(emp_code).strip()).first()
                if not employee:
                    errors.append(f'سطر {i}: لم يتم العثور على الموظف (id/code)')
                    continue

                # تحويل التاريخ والأوقات
                d = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()

                def parse_time(t):
                    if not t or str(t).strip() == '':
                        return None
                    t = str(t).strip()
                    fmts = ['%H:%M:%S', '%H:%M']
                    for fmt in fmts:
                        try:
                            tt = datetime.strptime(t, fmt).time()
                            return tt
                        except Exception:
                            pass
                    return None

                tin = parse_time(check_in)
                tout = parse_time(check_out)

                # ابحث أو أنشئ السجل
                att = Attendance.query.filter_by(employee_id=employee.id, date=d).first()
                if not att:
                    att = Attendance(employee_id=employee.id, date=d)
                    db.session.add(att)
                    created = True
                else:
                    created = False

                # حدّث الحقول
                if tin:
                    att.check_in_time = datetime.combine(d, tin)
                if tout:
                    att.check_out_time = datetime.combine(d, tout)

                # حالة داخل/خارج حسب توافر check_out
                if att.check_out_time:
                    att.status = 'outside'
                elif att.check_in_time:
                    att.status = 'inside'

                if created:
                    count_created += 1
                else:
                    count_updated += 1

            except Exception as row_err:
                errors.append(f'سطر {i}: {row_err}')

        db.session.commit()

        return jsonify({
            'status': 'success',
            'created': count_created,
            'updated': count_updated,
            'errors': errors
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CSV import error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@attendance_bp.route('/api/attendance', methods=['POST'])
@csrf.exempt  # تعطيل CSRF لهذا الـ API
@login_required
def api_attendance():
    """
    تسجيل الحضور أو الانصراف للموظف مع التحقق من الموقع والوقت والجهاز
    """
    if not current_user.has_any_permission(module='attendance', actions=['create', 'edit']):
        return jsonify({'status': 'error', 'message': 'غير مصرح لك بالقيام بهذه العملية'}), 403

    # قبول JSON بغض النظر عن Content-Type + دعم النماذج التقليدية كبديل
    data = request.get_json(silent=True, force=True)
    if not data and request.form:
        try:
            data = request.form.to_dict()
        except Exception:
            data = None
    if not data:
        return jsonify({'status': 'error', 'message': 'لا توجد بيانات في الطلب'}), 400

    # توحيد أسماء الحقول والقيم
    action_raw = (data.get('action') or data.get('status') or '').strip()
    # تحويل القيم الإنجليزية إلى العربية المستخدمة داخلياً
    if action_raw.lower() in ['in', 'checkin', 'check-in']:
        action = 'حضور'
    elif action_raw.lower() in ['out', 'checkout', 'check-out']:
        action = 'انصراف'
    else:
        action = action_raw  # قد تكون بالفعل 'حضور' أو 'انصراف'

    employee_id = data.get('employee_id')
    lat = data.get('lat')
    lng = data.get('lng')
    address = data.get('address')
    mac_address = data.get('mac_address')
    device_info = data.get('device_info')
    
    if not employee_id or not action:
        return jsonify({'status': 'error', 'message': 'بيانات الطلب غير مكتملة'}), 400

    # التحقق من الموقع
    location_ok, location_msg = verify_location(lat, lng)
    
    # التحقق من الوقت
    time_ok, time_msg = verify_time(action)
    
    # التحقق من الجهاز
    device_ok, device_msg = verify_device(employee_id, mac_address)
    
    # جمع الملاحظات
    verification_notes = f"الموقع: {location_msg}\nالوقت: {time_msg}\nالجهاز: {device_msg}"
    
    # إذا فشل أي تحقق، إرجاع خطأ
    settings = AttendanceSettings.query.first()
    if settings:
        if settings.require_location_verification and not location_ok:
            return jsonify({
                'status': 'error', 
                'message': f'فشل التحقق من الموقع: {location_msg}',
                'verification_details': {
                    'location': {'verified': location_ok, 'message': location_msg},
                    'time': {'verified': time_ok, 'message': time_msg},
                    'device': {'verified': device_ok, 'message': device_msg}
                }
            }), 403
        
        if settings.require_time_verification and not time_ok and not settings.allow_outside_hours:
            return jsonify({
                'status': 'error', 
                'message': f'فشل التحقق من الوقت: {time_msg}',
                'verification_details': {
                    'location': {'verified': location_ok, 'message': location_msg},
                    'time': {'verified': time_ok, 'message': time_msg},
                    'device': {'verified': device_ok, 'message': device_msg}
                }
            }), 403
        
        if settings.require_device_verification and not device_ok:
            return jsonify({
                'status': 'error', 
                'message': f'فشل التحقق من الجهاز: {device_msg}',
                'verification_details': {
                    'location': {'verified': location_ok, 'message': location_msg},
                    'time': {'verified': time_ok, 'message': time_msg},
                    'device': {'verified': device_ok, 'message': device_msg}
                }
            }), 403
    
    today = date.today()
    
    # ابحث عن سجل حضور موجود اليوم
    existing_attendance = Attendance.query.filter_by(employee_id=employee_id, date=today).first()

    if action == 'حضور':
        if existing_attendance:
            return jsonify({'status': 'error', 'message': 'تم تسجيل الحضور لهذا الموظف اليوم بالفعل'}), 409
        
        new_attendance = Attendance(
            employee_id=employee_id,
            date=today,
            check_in_time=datetime.now(),
            lat=lat,
            lng=lng,
            address=address,
            mac_address=mac_address,
            device_info=device_info,
            location_verified=location_ok,
            time_verified=time_ok,
            device_verified=device_ok,
            verification_notes=verification_notes,
            status='inside'
        )
        db.session.add(new_attendance)
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': 'تم تسجيل الحضور بنجاح',
            'verification_details': {
                'location': {'verified': location_ok, 'message': location_msg},
                'time': {'verified': time_ok, 'message': time_msg},
                'device': {'verified': device_ok, 'message': device_msg}
            }
        })

    elif action == 'انصراف':
        if not existing_attendance:
            return jsonify({'status': 'error', 'message': 'لا يمكن تسجيل الانصراف قبل تسجيل الحضور'}), 404
        
        if existing_attendance.check_out_time:
            return jsonify({'status': 'error', 'message': 'تم تسجيل الانصراف لهذا الموظف اليوم بالفعل'}), 409
            
        existing_attendance.check_out_time = datetime.now()
        existing_attendance.lat_out = lat
        existing_attendance.lng_out = lng
        existing_attendance.address_out = address
        existing_attendance.status = 'outside'
        
        # تحديث معلومات التحقق عند الانصراف
        if not existing_attendance.verification_notes:
            existing_attendance.verification_notes = ""
        existing_attendance.verification_notes += f"\n\nعند الانصراف:\n{verification_notes}"
        
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': 'تم تسجيل الانصراف بنجاح',
            'verification_details': {
                'location': {'verified': location_ok, 'message': location_msg},
                'time': {'verified': time_ok, 'message': time_msg},
                'device': {'verified': device_ok, 'message': device_msg}
            }
        })

    return jsonify({'status': 'error', 'message': 'نوع العملية غير معروف'}), 400

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

@attendance_bp.route('/attendance/delete/<int:attendance_id>', methods=['POST'])
@login_required
def delete_attendance(attendance_id):
    """حذف سجل الحضور والانصراف"""
    attendance_record = Attendance.query.get_or_404(attendance_id)
    if not has_permission(['admin', 'manager']) and attendance_record.employee_id != current_user.id:
        return {'error': 'Unauthorized'}, 403
    db.session.delete(attendance_record)
    db.session.commit()
    return {'status': 'تم حذف السجل بنجاح'}

@attendance_bp.route('/attendance/<int:employee_id>', methods=['GET'])
@login_required
def attendance_by_employee(employee_id):
    attendance_log = Attendance.query.filter_by(employee_id=employee_id).order_by(Attendance.id.desc()).all()
    return render_template('attendance.html', lang=session.get('lang', 'ar'), attendance_log=attendance_log)


# ==================== APIs لإدارة الأجهزة المسجلة ====================

@attendance_bp.route('/api/attendance/register-device', methods=['POST'])
@login_required
def register_device():
    """تسجيل جهاز جديد للموظف"""
    if not current_user.has_permission(module='attendance', action='edit'):
        return jsonify({'status': 'error', 'message': 'غير مصرح لك'}), 403
    
    data = request.get_json()
    employee_id = data.get('employee_id')
    mac_address = data.get('mac_address')
    device_name = data.get('device_name')
    device_info = data.get('device_info')
    
    if not employee_id or not mac_address:
        return jsonify({'status': 'error', 'message': 'بيانات غير مكتملة'}), 400
    
    # التحقق من أن الجهاز غير مسجل من قبل
    existing = RegisteredDevice.query.filter_by(mac_address=mac_address).first()
    if existing:
        return jsonify({
            'status': 'error', 
            'message': f'هذا الجهاز مسجل بالفعل للموظف: {existing.employee.name}'
        }), 409
    
    device = RegisteredDevice(
        employee_id=employee_id,
        mac_address=mac_address,
        device_name=device_name,
        device_info=device_info,
        is_active=True
    )
    
    db.session.add(device)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تسجيل الجهاز بنجاح',
        'device': {
            'id': device.id,
            'mac_address': device.mac_address,
            'device_name': device.device_name
        }
    })


@attendance_bp.route('/api/attendance/devices/<int:employee_id>', methods=['GET'])
@login_required
def get_employee_devices(employee_id):
    """الحصول على قائمة أجهزة الموظف"""
    devices = RegisteredDevice.query.filter_by(employee_id=employee_id).all()
    
    return jsonify({
        'devices': [{
            'id': d.id,
            'mac_address': d.mac_address,
            'device_name': d.device_name,
            'device_info': d.device_info,
            'is_active': d.is_active,
            'registered_at': d.registered_at.isoformat() if d.registered_at else None,
            'last_used': d.last_used.isoformat() if d.last_used else None
        } for d in devices]
    })


@attendance_bp.route('/api/attendance/device/<int:device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id):
    """حذف جهاز مسجل"""
    if not current_user.has_permission(module='attendance', action='edit'):
        return jsonify({'status': 'error', 'message': 'غير مصرح لك'}), 403
    
    device = RegisteredDevice.query.get_or_404(device_id)
    db.session.delete(device)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'تم حذف الجهاز بنجاح'})


@attendance_bp.route('/api/attendance/device/<int:device_id>/toggle', methods=['POST'])
@login_required
def toggle_device(device_id):
    """تفعيل/تعطيل جهاز"""
    if not current_user.has_permission(module='attendance', action='edit'):
        return jsonify({'status': 'error', 'message': 'غير مصرح لك'}), 403
    
    device = RegisteredDevice.query.get_or_404(device_id)
    device.is_active = not device.is_active
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'تم {"تفعيل" if device.is_active else "تعطيل"} الجهاز',
        'is_active': device.is_active
    })


# ==================== APIs لإدارة إعدادات الحضور ====================

@attendance_bp.route('/api/attendance/settings', methods=['GET'])
@login_required
def get_attendance_settings():
    """الحصول على إعدادات الحضور"""
    settings = AttendanceSettings.query.first()
    if not settings:
        settings = AttendanceSettings()
        db.session.add(settings)
        db.session.commit()
    
    return jsonify({
        'id': settings.id,
        'company_lat': settings.company_lat,
        'company_lng': settings.company_lng,
        'max_distance_meters': settings.max_distance_meters,
        'check_in_start': settings.check_in_start.strftime('%H:%M') if settings.check_in_start else '07:00',
        'check_in_end': settings.check_in_end.strftime('%H:%M') if settings.check_in_end else '10:00',
        'check_out_start': settings.check_out_start.strftime('%H:%M') if settings.check_out_start else '14:00',
        'check_out_end': settings.check_out_end.strftime('%H:%M') if settings.check_out_end else '18:00',
        'require_location_verification': settings.require_location_verification,
        'require_time_verification': settings.require_time_verification,
        'require_device_verification': settings.require_device_verification,
        'allow_outside_hours': settings.allow_outside_hours
    })


@attendance_bp.route('/api/attendance/settings', methods=['POST'])
@login_required
def update_attendance_settings():
    """تحديث إعدادات الحضور"""
    if not has_permission(['admin']):
        return jsonify({'status': 'error', 'message': 'غير مصرح لك'}), 403
    
    data = request.get_json()
    settings = AttendanceSettings.query.first()
    
    if not settings:
        settings = AttendanceSettings()
        db.session.add(settings)
    
    # تحديث الإعدادات
    if 'company_lat' in data:
        settings.company_lat = float(data['company_lat'])
    if 'company_lng' in data:
        settings.company_lng = float(data['company_lng'])
    if 'max_distance_meters' in data:
        settings.max_distance_meters = int(data['max_distance_meters'])
    
    if 'check_in_start' in data:
        settings.check_in_start = datetime.strptime(data['check_in_start'], '%H:%M').time()
    if 'check_in_end' in data:
        settings.check_in_end = datetime.strptime(data['check_in_end'], '%H:%M').time()
    if 'check_out_start' in data:
        settings.check_out_start = datetime.strptime(data['check_out_start'], '%H:%M').time()
    if 'check_out_end' in data:
        settings.check_out_end = datetime.strptime(data['check_out_end'], '%H:%M').time()
    
    if 'require_location_verification' in data:
        settings.require_location_verification = bool(data['require_location_verification'])
    if 'require_time_verification' in data:
        settings.require_time_verification = bool(data['require_time_verification'])
    if 'require_device_verification' in data:
        settings.require_device_verification = bool(data['require_device_verification'])
    if 'allow_outside_hours' in data:
        settings.allow_outside_hours = bool(data['allow_outside_hours'])
    
    settings.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تحديث الإعدادات بنجاح'
    })


@attendance_bp.route('/attendance/settings', methods=['GET'])
@login_required
def attendance_settings_page():
    """صفحة إعدادات الحضور والانصراف"""
    if not has_permission(['admin']):
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('attendance.attendance'))
    
    return render_template('attendance_settings.html', lang=session.get('lang', 'ar'))
