"""
Routes للتقارير المتقدمة والتكامل مع الرواتب
"""
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from app import db, csrf
from app.models.attendance import Attendance, AttendanceSettings
from app.models.attendance_advanced import (
    AttendanceReport, AttendanceSync, AttendanceRBAC, PayrollAttendanceLink
)
from app.models.employee import Employee
from app.models.payroll import Payroll
from app.permissions import has_permission
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
import json

attendance_reports_bp = Blueprint('attendance_reports', __name__)


# ==================== لوحة التقارير ====================

@attendance_reports_bp.route('/attendance/reports/dashboard')
@login_required
def reports_dashboard():
    """لوحة تقارير الحضور: اليوم/الأسبوع/الشهر"""
    if not current_user.has_permission(module='attendance', action='view'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    period = request.args.get('period', 'today')  # today, week, month
    employee_id = request.args.get('employee_id')
    
    # تحديد الفترة
    today = date.today()
    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
    else:
        start_date = today
        end_date = today
    
    # بناء الاستعلام
    query = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    )
    
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    
    # الإحصائيات العامة
    stats = {
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_checkins': query.filter(Attendance.check_in_time.isnot(None)).count(),
        'total_checkouts': query.filter(Attendance.check_out_time.isnot(None)).count(),
        'location_violations': query.filter(Attendance.location_verified == False).count(),
        'time_violations': query.filter(Attendance.time_verified == False).count(),
        'device_violations': query.filter(Attendance.device_verified == False).count(),
    }
    
    return render_template('attendance_reports.html', 
                         stats=stats,
                         period=period,
                         lang=session.get('lang', 'ar'))


@attendance_reports_bp.route('/api/attendance/reports/late-stats')
@login_required
def late_statistics():
    """إحصائيات التأخير: متوسط التأخير و Top Late"""
    if not current_user.has_permission(module='attendance', action='view'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    period = request.args.get('period', 'month')
    limit = int(request.args.get('limit', 10))
    
    # تحديد الفترة
    today = date.today()
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
    elif period == 'month':
        start_date = today.replace(day=1)
    else:
        start_date = today - timedelta(days=30)
    
    # الحصول على إعدادات النظام
    settings = AttendanceSettings.query.first()
    if not settings:
        return jsonify({'error': 'Settings not found'}), 404
    
    # حساب التأخير لكل موظف
    late_employees = []
    
    employees = Employee.query.filter_by(active=True).all()
    for emp in employees:
        attendances = Attendance.query.filter(
            Attendance.employee_id == emp.id,
            Attendance.date >= start_date,
            Attendance.check_in_time.isnot(None)
        ).all()
        
        if not attendances:
            continue
        
        total_late_minutes = 0
        late_count = 0
        
        for att in attendances:
            check_in_time = att.check_in_time.time()
            if settings.check_in_end and check_in_time > settings.check_in_end:
                # حساب دقائق التأخير
                expected = datetime.combine(att.date, settings.check_in_end)
                actual = att.check_in_time
                late_minutes = int((actual - expected).total_seconds() / 60)
                
                # فترة السماح
                grace_period = getattr(settings, 'grace_period_minutes', 15)
                if late_minutes > grace_period:
                    total_late_minutes += late_minutes
                    late_count += 1
        
        if late_count > 0:
            late_employees.append({
                'id': emp.id,
                'name': emp.name,
                'department': emp.department,
                'total_late_minutes': total_late_minutes,
                'late_count': late_count,
                'average_late_minutes': round(total_late_minutes / late_count, 2)
            })
    
    # ترتيب حسب إجمالي التأخير
    late_employees.sort(key=lambda x: x['total_late_minutes'], reverse=True)
    
    # حساب المتوسط العام
    if late_employees:
        overall_average = sum(e['average_late_minutes'] for e in late_employees) / len(late_employees)
    else:
        overall_average = 0
    
    return jsonify({
        'period': period,
        'start_date': start_date.isoformat(),
        'overall_average_late_minutes': round(overall_average, 2),
        'total_late_employees': len(late_employees),
        'top_late_employees': late_employees[:limit]
    })


@attendance_reports_bp.route('/api/attendance/reports/generate', methods=['POST'])
@csrf.exempt
@login_required
def generate_report():
    """توليد تقرير حضور مجمّع"""
    if not current_user.has_permission(module='attendance', action='view'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json(force=True) if request.data else {}
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    employee_id = data.get('employee_id')
    period_type = data.get('period_type', 'monthly')
    period_start = datetime.strptime(data.get('period_start'), '%Y-%m-%d').date()
    period_end = datetime.strptime(data.get('period_end'), '%Y-%m-%d').date()
    
    if not employee_id:
        return jsonify({'error': 'Employee ID required'}), 400
    
    # جلب سجلات الحضور
    attendances = Attendance.query.filter(
        Attendance.employee_id == employee_id,
        Attendance.date >= period_start,
        Attendance.date <= period_end
    ).all()
    
    # حساب الإحصائيات
    settings = AttendanceSettings.query.first()
    
    total_days = (period_end - period_start).days + 1
    present_days = len(set(att.date for att in attendances if att.check_in_time))
    absent_days = total_days - present_days
    
    total_late_minutes = 0
    late_days = 0
    total_work_minutes = 0
    total_overtime_minutes = 0
    location_violations = 0
    time_violations = 0
    device_violations = 0
    
    for att in attendances:
        # التأخير
        if settings and att.check_in_time:
            check_in_time = att.check_in_time.time()
            if settings.check_in_end and check_in_time > settings.check_in_end:
                expected = datetime.combine(att.date, settings.check_in_end)
                late_minutes = int((att.check_in_time - expected).total_seconds() / 60)
                grace_period = getattr(settings, 'grace_period_minutes', 15)
                if late_minutes > grace_period:
                    total_late_minutes += late_minutes
                    late_days += 1
        
        # ساعات العمل
        if att.check_in_time and att.check_out_time:
            work_minutes = int((att.check_out_time - att.check_in_time).total_seconds() / 60)
            total_work_minutes += work_minutes
            
            # الساعات الإضافية
            min_work_hours = getattr(settings, 'min_work_hours_per_day', 8) if settings else 8
            if work_minutes > (min_work_hours * 60):
                total_overtime_minutes += (work_minutes - min_work_hours * 60)
        
        # المخالفات
        if not att.location_verified:
            location_violations += 1
        if not att.time_verified:
            time_violations += 1
        if not att.device_verified:
            device_violations += 1
    
    average_late_minutes = total_late_minutes / late_days if late_days > 0 else 0
    
    # إنشاء التقرير
    report = AttendanceReport(
        employee_id=employee_id,
        period_type=period_type,
        period_start=period_start,
        period_end=period_end,
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        late_days=late_days,
        total_work_minutes=total_work_minutes,
        total_late_minutes=total_late_minutes,
        total_overtime_minutes=total_overtime_minutes,
        average_late_minutes=average_late_minutes,
        location_violations=location_violations,
        time_violations=time_violations,
        device_violations=device_violations,
        generated_by=current_user.id
    )
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم إنشاء التقرير بنجاح',
        'report': {
            'id': report.id,
            'employee_id': report.employee_id,
            'period_type': report.period_type,
            'total_days': report.total_days,
            'present_days': report.present_days,
            'absent_days': report.absent_days,
            'late_days': report.late_days,
            'average_late_minutes': round(report.average_late_minutes, 2),
            'total_work_hours': round(report.total_work_minutes / 60, 2),
            'total_overtime_hours': round(report.total_overtime_minutes / 60, 2)
        }
    })


# ==================== التكامل مع الرواتب ====================

@attendance_reports_bp.route('/api/attendance/link-to-payroll', methods=['POST'])
@csrf.exempt
@login_required
def link_to_payroll():
    """ربط تقرير الحضور بالراتب تلقائياً"""
    if not has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json(force=True) if request.data else {}
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    report_id = data.get('report_id')
    payroll_id = data.get('payroll_id')
    
    report = AttendanceReport.query.get_or_404(report_id)
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # التحقق من التطابق
    if report.employee_id != payroll.employee_id:
        return jsonify({'error': 'Employee mismatch'}), 400
    
    # الحصول على الإعدادات
    settings = AttendanceSettings.query.first()
    
    late_deduction_rate = getattr(settings, 'late_deduction_per_minute', 1.0) if settings else 1.0
    absence_deduction_rate = getattr(settings, 'absence_deduction_per_day', 100.0) if settings else 100.0
    overtime_bonus_rate = getattr(settings, 'overtime_bonus_per_hour', 50.0) if settings else 50.0
    
    # الحسابات
    late_deduction = report.total_late_minutes * late_deduction_rate
    absence_deduction = report.absent_days * absence_deduction_rate
    overtime_bonus = (report.total_overtime_minutes / 60) * overtime_bonus_rate
    
    # إنشاء/تحديث الربط
    link = PayrollAttendanceLink.query.filter_by(
        payroll_id=payroll_id,
        report_id=report_id
    ).first()
    
    if not link:
        link = PayrollAttendanceLink(
            payroll_id=payroll_id,
            report_id=report_id
        )
        db.session.add(link)
    
    link.late_deduction_amount = late_deduction
    link.absence_deduction_amount = absence_deduction
    link.overtime_bonus_amount = overtime_bonus
    link.late_deduction_rate = late_deduction_rate
    link.absence_deduction_rate = absence_deduction_rate
    link.overtime_bonus_rate = overtime_bonus_rate
    link.auto_calculated = True
    
    # تحديث الراتب
    payroll.late_deduction = (payroll.late_deduction or 0) + late_deduction
    payroll.absence_deduction = (payroll.absence_deduction or 0) + absence_deduction
    payroll.overtime_amount = (payroll.overtime_amount or 0) + overtime_bonus
    
    # إعادة حساب الراتب الصافي
    payroll.total_deductions = (
        (payroll.late_deduction or 0) +
        (payroll.absence_deduction or 0) +
        (payroll.loan_deduction or 0) +
        (payroll.other_deductions or 0) +
        (payroll.health_insurance or 0)
    )
    
    payroll.gross_salary = (
        (payroll.base or 0) +
        (payroll.housing_allowance or 0) +
        (payroll.transport_allowance or 0) +
        (payroll.overtime_amount or 0)
    )
    
    payroll.net = payroll.gross_salary - payroll.total_deductions
    
    # تحديث التقرير
    report.linked_to_payroll = True
    report.payroll_id = payroll_id
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم ربط الحضور بالراتب بنجاح',
        'link': {
            'late_deduction': round(late_deduction, 2),
            'absence_deduction': round(absence_deduction, 2),
            'overtime_bonus': round(overtime_bonus, 2),
            'total_adjustment': round(overtime_bonus - late_deduction - absence_deduction, 2)
        },
        'payroll': {
            'id': payroll.id,
            'gross_salary': round(payroll.gross_salary, 2),
            'total_deductions': round(payroll.total_deductions, 2),
            'net': round(payroll.net, 2)
        }
    })


# ==================== Offline Support ====================

@attendance_reports_bp.route('/api/attendance/sync/queue', methods=['POST'])
@csrf.exempt
@login_required
def queue_for_sync():
    """إضافة سجل إلى قائمة المزامنة (للوضع Offline)"""
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({'error': 'بيانات JSON غير صالحة'}), 400
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    sync_record = AttendanceSync(
        employee_id=data.get('employee_id'),
        action=data.get('action'),
        timestamp=datetime.fromisoformat(data.get('timestamp')),
        lat=data.get('lat'),
        lng=data.get('lng'),
        address=data.get('address'),
        mac_address=data.get('mac_address'),
        device_info=data.get('device_info'),
        original_data=json.dumps(data)
    )
    
    db.session.add(sync_record)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم إضافة السجل لقائمة المزامنة',
        'sync_id': sync_record.id
    })


@attendance_reports_bp.route('/api/attendance/sync/process', methods=['POST'])
@csrf.exempt
@login_required
def process_sync_queue():
    """معالجة قائمة المزامنة"""
    if not has_permission(['admin']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # جلب السجلات المعلقة
    pending_syncs = AttendanceSync.query.filter_by(sync_status='pending').limit(100).all()
    
    processed = 0
    failed = 0
    
    for sync in pending_syncs:
        try:
            # محاولة إنشاء سجل الحضور
            attendance = Attendance(
                employee_id=sync.employee_id,
                date=sync.timestamp.date(),
                lat=sync.lat,
                lng=sync.lng,
                address=sync.address,
                mac_address=sync.mac_address,
                device_info=sync.device_info
            )
            
            if sync.action == 'check_in':
                attendance.check_in_time = sync.timestamp
            else:
                # البحث عن سجل حضور موجود
                existing = Attendance.query.filter_by(
                    employee_id=sync.employee_id,
                    date=sync.timestamp.date()
                ).first()
                
                if existing:
                    existing.check_out_time = sync.timestamp
                    existing.lat_out = sync.lat
                    existing.lng_out = sync.lng
                    existing.address_out = sync.address
                else:
                    attendance.check_out_time = sync.timestamp
            
            if sync.action == 'check_in' or not existing:
                db.session.add(attendance)
            
            sync.sync_status = 'synced'
            sync.synced_at = datetime.now()
            processed += 1
            
        except Exception as e:
            sync.sync_status = 'failed'
            sync.error_message = str(e)
            sync.sync_attempts += 1
            sync.last_sync_attempt = datetime.now()
            failed += 1
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'processed': processed,
        'failed': failed,
        'remaining': AttendanceSync.query.filter_by(sync_status='pending').count()
    })
