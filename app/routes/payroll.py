from flask import Blueprint, render_template, request, jsonify, current_app, make_response
from flask_login import login_required, current_user
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.settings import Settings
from app.models.leave import Leave
from app.models.payroll import Payroll, PayrollTemplate, EmployeeLoan, PayrollBatch
from app import db
from app.permissions import has_permission
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import csv
from io import StringIO

payroll_bp = Blueprint('payroll', __name__)


def _compute_attendance_metrics(emp_id: int, period_start: date, period_end: date):
    """احسب الغياب والتأخير للموظف خلال الفترة المحددة بالاعتماد على جدول الحضور.
    - الغياب: أيام العمل التي لا يوجد لها سجل حضور
    - التأخير: دقائق التأخير مقارنة بوقت بداية الدوام من الإعدادات
    """
    settings = Settings.get_settings()
    # أيام العمل من الإعدادات كنص "0,1,2,3,4" (0=Sunday)
    work_days = set((settings.work_days or '0,1,2,3,4').split(','))
    # وقت بداية الدوام من الإعدادات
    work_start_str = settings.work_start or current_app.config.get('WORK_START', '08:00')
    try:
        work_start_time = datetime.strptime(work_start_str, '%H:%M').time()
    except Exception:
        work_start_time = datetime.strptime('08:00', '%H:%M').time()

    # جلب حضور الموظف ضمن الفترة
    recs = Attendance.query.filter(
        Attendance.employee_id == emp_id,
        Attendance.date >= period_start,
        Attendance.date <= period_end
    ).all()
    # تجميع حسب اليوم
    by_date = {}
    for r in recs:
        by_date.setdefault(r.date, []).append(r)

    # اجتياز أيام الفترة
    cur = period_start
    absence_days = 0
    total_late_minutes = 0
    working_days_count = 0
    while cur <= period_end:
        weekday = (cur.weekday() + 1) % 7  # Python: Monday=0; mapping to Sunday=0
        if str(weekday) in work_days:
            working_days_count += 1
            day_recs = by_date.get(cur)
            if not day_recs:
                absence_days += 1
            else:
                # احسب أول دخول لليوم
                first_in = None
                for rec in day_recs:
                    if rec.check_in_time and (first_in is None or rec.check_in_time < first_in):
                        first_in = rec.check_in_time
                if first_in:
                    # دقائق التأخير
                    scheduled_dt = datetime.combine(first_in.date(), work_start_time)
                    if first_in > scheduled_dt:
                        delta = first_in - scheduled_dt
                        total_late_minutes += max(0, int(delta.total_seconds() // 60))
        cur += relativedelta(days=1)

    return absence_days, total_late_minutes, working_days_count


def _get_leave_dates(emp_id: int, period_start: date, period_end: date):
    """اجلب أيام الإجازات الموافق عليها ضمن الفترة كتواريخ منفصلة.
    - يرجع مجموعتين: paid_dates, unpaid_dates
    - يدعم الإجازة المرضية ذات الدفع الجزئي باستخدام Leave.paid_days
    """
    leaves = Leave.query.filter(
        Leave.employee_id == emp_id,
        Leave.status == 'Approved',
        Leave.end_date >= period_start,
        Leave.start_date <= period_end
    ).all()
    paid_dates = set()
    unpaid_dates = set()
    for lv in leaves:
        cur = max(lv.start_date, period_start)
        end = min(lv.end_date, period_end)
        # اجمع كل الأيام أولاً
        dates = []
        while cur <= end:
            dates.append(cur)
            cur += relativedelta(days=1)
        # توزيع الأيام على مدفوعة/غير مدفوعة
        if lv.leave_type == 'sick' and lv.paid_days is not None:
            paid_portion = max(0, min(len(dates), int(lv.paid_days or 0)))
            for d in dates[:paid_portion]:
                paid_dates.add(d)
            for d in dates[paid_portion:]:
                unpaid_dates.add(d)
        else:
            # حالات عامة: paid=True → كل الأيام مدفوعة، وإلا غير مدفوعة
            if lv.paid:
                for d in dates:
                    paid_dates.add(d)
            else:
                for d in dates:
                    unpaid_dates.add(d)
    return paid_dates, unpaid_dates


def _compute_loan_due_amount(emp_id: int, period_end: date) -> float:
    """احسب إجمالي قسط السلف/القروض المستحق لهذا الشهر بدون تعديل سجلات القروض.
    - يجمع القسط الشهري لكل قرض/سلفة نشطة مع مراعاة المبلغ المتبقي.
    - إذا كان monthly_deduction غير محدد ولكن يوجد عدد أقساط، يحسب مؤقتاً amount/installments.
    - إذا remaining_amount غير معرف، يعتبر amount للأغراض الحسابية فقط.
    """
    if not current_app.config.get('PAYROLL_AUTO_LOAN_DEDUCTION', True):
        return 0.0

    total_due = 0.0
    loans = EmployeeLoan.query.filter(
        EmployeeLoan.employee_id == emp_id,
        EmployeeLoan.status == 'active'
    ).all()

    for loan in loans:
        # تجاهل القروض التي لم يبدأ سدادها بعد
        if loan.start_date and loan.start_date > period_end:
            continue
        remaining = float(loan.remaining_amount if loan.remaining_amount is not None else (loan.amount or 0.0))
        if remaining <= 0:
            continue
        monthly = loan.monthly_deduction
        if (monthly is None or monthly == 0) and loan.amount and loan.installments:
            try:
                monthly = round(float(loan.amount) / float(loan.installments), 2)
            except Exception:
                monthly = 0.0
        monthly = float(monthly or 0.0)
        if monthly <= 0:
            continue
        total_due += min(remaining, monthly)

    return round(total_due, 2)


def _compute_loan_due_breakdown(emp_id: int, period_end: date):
    """إرجاع تفصيل قسط السلف/القروض المستحق لكل قرض لهذا الشهر دون تعديل سجلات القروض."""
    if not current_app.config.get('PAYROLL_AUTO_LOAN_DEDUCTION', True):
        return []
    breakdown = []
    loans = EmployeeLoan.query.filter(
        EmployeeLoan.employee_id == emp_id,
        EmployeeLoan.status == 'active'
    ).order_by(EmployeeLoan.issued_date.asc()).all()

    for loan in loans:
        if loan.start_date and loan.start_date > period_end:
            continue
        remaining = float(loan.remaining_amount if loan.remaining_amount is not None else (loan.amount or 0.0))
        if remaining <= 0:
            continue
        monthly = loan.monthly_deduction
        if (monthly is None or monthly == 0) and loan.amount and loan.installments:
            try:
                monthly = round(float(loan.amount) / float(loan.installments), 2)
            except Exception:
                monthly = 0.0
        monthly = float(monthly or 0.0)
        if monthly <= 0:
            continue
        due = min(remaining, monthly)
        breakdown.append({
            'id': loan.id,
            'type': loan.loan_type,
            'reason': loan.reason,
            'monthly': monthly,
            'remaining': remaining,
            'due': due
        })
    return breakdown


@payroll_bp.route('/payroll')
@login_required
def payroll_list():
    """عرض قائمة الرواتب"""
    if not current_user.has_permission(module='payroll', action='view'):
        return render_template('unauthorized.html')
    
    # جلب الشهور والسنوات المتاحة للفلترة
    available_periods = db.session.query(Payroll.year, Payroll.month).distinct().order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    
    # جلب جميع الموظفين
    employees = Employee.query.filter_by(active=True).order_by(Employee.name).all()
    
    # الحصول على filters من request
    filters = {
        'period_start': request.args.get('period_start', ''),
        'period_end': request.args.get('period_end', ''),
        'employee_id': request.args.get('employee_id', '')
    }
    
    # حساب الإحصائيات
    total_payroll = db.session.query(db.func.sum(Payroll.net)).scalar() or 0
    paid_payrolls = Payroll.query.filter_by(status='paid').count()
    unpaid_payrolls = Payroll.query.filter(Payroll.status != 'paid').count()
    
    from flask import session
    return render_template('payroll.html', 
                         lang=session.get('lang', 'ar'),
                         available_periods=available_periods,
                         employees=employees,
                         filters=filters,
                         total_payroll=total_payroll,
                         paid_payrolls=paid_payrolls,
                         unpaid_payrolls=unpaid_payrolls)


@payroll_bp.route('/payroll/payslip/<int:payroll_id>')
@login_required
def payslip(payroll_id):
    """عرض إيصال الدفع"""
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # التحقق من الصلاحية: إما أن يكون الموظف نفسه أو مدير لديه صلاحية العرض
    if not (current_user.id == payroll.employee_id or current_user.has_permission(module='payroll', action='view')):
        return render_template('unauthorized.html')
        
    from flask import session
    emp = Employee.query.get(payroll.employee_id)
    # تفصيل أقساط السُلف/القروض لهذا الشهر
    period_end = payroll.period_end or date(payroll.year, payroll.month, 1) + relativedelta(months=1, days=-1)
    loan_breakdown = _compute_loan_due_breakdown(payroll.employee_id, period_end)
    return render_template('payslip.html', lang=session.get('lang', 'ar'), p=payroll, emp=emp, loan_breakdown=loan_breakdown)


# ==================== API Routes ====================

@payroll_bp.route('/api/payroll', methods=['GET'])
@login_required
def get_payrolls():
    """الحصول على قائمة الرواتب مع الفلترة"""
    if not current_user.has_permission(module='payroll', action='view'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        query = db.session.query(Payroll).join(Employee)
        
        # Filters
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        
        if month:
            query = query.filter(Payroll.month == month)
        if year:
            query = query.filter(Payroll.year == year)
        if status:
            query = query.filter(Payroll.status == status)
        if search:
            query = query.filter(Employee.full_name.ilike(f'%{search}%'))
        
        payrolls = query.order_by(Payroll.year.desc(), Payroll.month.desc(), Payroll.id.desc()).all()
        
        result = []
        for p in payrolls:
            result.append({
                'id': p.id,
                'employee_id': p.employee_id,
                'month': p.month,
                'year': p.year,
                'period_start': p.period_start.isoformat() if p.period_start else None,
                'period_end': p.period_end.isoformat() if p.period_end else None,
                'basic': float(p.basic or 0),
                'allowances': float(p.allowances or 0),
                'housing_allowance': float(p.housing_allowance or 0),
                'transport_allowance': float(p.transport_allowance or 0),
                'food_allowance': float(p.food_allowance or 0),
                'phone_allowance': float(p.phone_allowance or 0),
                'other_allowances': float(p.other_allowances or 0),
                'bonus': float(p.bonus or 0),
                'commission': float(p.commission or 0),
                'incentives': float(p.incentives or 0),
                'overtime_hours': float(p.overtime_hours or 0),
                'overtime_amount': float(p.overtime_amount or 0),
                'absence_days': int(p.absence_days or 0),
                'absence_deduction': float(p.absence_deduction or 0),
                'late_minutes': int(p.late_minutes or 0),
                'late_deduction': float(p.late_deduction or 0),
                'loan_deduction': float(p.loan_deduction or 0),
                'other_deductions': float(p.other_deductions or 0),
                'gross_salary': float(p.gross_salary or 0),
                'total_deductions': float(p.total_deductions or 0),
                'tax': float(p.tax or 0),
                'insurance': float(p.insurance or 0),
                'net': float(p.net or 0),
                'status': p.status,
                'notes': p.notes,
                'generated_at': p.generated_at.isoformat() if p.generated_at else None,
                'last_recalc_net_diff': float(p.last_recalc_net_diff or 0),
                'last_recalc_at': p.last_recalc_at.isoformat() if p.last_recalc_at else None
            })
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error fetching payrolls: {e}")
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/api/payroll/<int:payroll_id>', methods=['GET'])
@login_required
def get_payroll(payroll_id):
    """الحصول على تفاصيل راتب محدد"""
    if not current_user.has_permission(module='payroll', action='view'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    payroll = Payroll.query.get_or_404(payroll_id)
    
    return jsonify({
        'id': payroll.id,
        'employee_id': payroll.employee_id,
        'month': payroll.month,
        'year': payroll.year,
        'period_start': payroll.period_start.isoformat() if payroll.period_start else None,
        'period_end': payroll.period_end.isoformat() if payroll.period_end else None,
        'basic': float(payroll.basic or 0),
        'housing_allowance': float(payroll.housing_allowance or 0),
        'transport_allowance': float(payroll.transport_allowance or 0),
        'food_allowance': float(payroll.food_allowance or 0),
        'phone_allowance': float(payroll.phone_allowance or 0),
        'other_allowances': float(payroll.other_allowances or 0),
        'bonus': float(payroll.bonus or 0),
        'commission': float(payroll.commission or 0),
        'incentives': float(payroll.incentives or 0),
        'overtime_hours': float(payroll.overtime_hours or 0),
        'overtime_amount': float(payroll.overtime_amount or 0),
        'absence_days': int(payroll.absence_days or 0),
        'absence_deduction': float(payroll.absence_deduction or 0),
        'late_minutes': int(payroll.late_minutes or 0),
        'late_deduction': float(payroll.late_deduction or 0),
        'loan_deduction': float(payroll.loan_deduction or 0),
        'other_deductions': float(payroll.other_deductions or 0),
        'gross_salary': float(payroll.gross_salary or 0),
        'total_deductions': float(payroll.total_deductions or 0),
        'tax': float(payroll.tax or 0),
        'insurance': float(payroll.insurance or 0),
        'health_insurance': float(payroll.health_insurance or 0),
        'net': float(payroll.net or 0),
        'status': payroll.status,
        'notes': payroll.notes,
        'payment_date': payroll.payment_date.isoformat() if payroll.payment_date else None,
        'payment_method': payroll.payment_method
    })


@payroll_bp.route('/api/payroll', methods=['POST'])
@login_required
def create_payroll():
    """إنشاء راتب جديد"""
    if not current_user.has_permission(module='payroll', action='create'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        
        # Check if payroll already exists
        existing = Payroll.query.filter_by(
            employee_id=data['employee_id'],
            month=data['month'],
            year=data['year']
        ).first()
        
        if existing:
            return jsonify({'error': 'Payroll already exists for this period'}), 400
        
        # Create new payroll
        payroll = Payroll(
            employee_id=data['employee_id'],
            month=data['month'],
            year=data['year'],
            basic=data.get('basic', 0),
            housing_allowance=data.get('housing_allowance', 0),
            transport_allowance=data.get('transport_allowance', 0),
            food_allowance=data.get('food_allowance', 0),
            phone_allowance=data.get('phone_allowance', 0),
            other_allowances=data.get('other_allowances', 0),
            bonus=data.get('bonus', 0),
            commission=data.get('commission', 0),
            incentives=data.get('incentives', 0),
            overtime_hours=data.get('overtime_hours', 0),
            overtime_amount=data.get('overtime_amount', 0),
            absence_days=data.get('absence_days', 0),
            absence_deduction=data.get('absence_deduction', 0),
            late_minutes=data.get('late_minutes', 0),
            late_deduction=data.get('late_deduction', 0),
            loan_deduction=data.get('loan_deduction', 0),
            other_deductions=data.get('other_deductions', 0),
            status=data.get('status', 'pending'),
            notes=data.get('notes'),
            generated_by=current_user.id,
            generated_at=datetime.utcnow()
        )
        
        # Set period dates
        payroll.period_start = date(data['year'], data['month'], 1)
        payroll.period_end = payroll.period_start + relativedelta(months=1, days=-1)

        # Auto compute absence/late from attendance if not supplied
        if (data.get('absence_days') is None) or (data.get('late_minutes') is None):
            abs_days, late_mins, working_days = _compute_attendance_metrics(payroll.employee_id, payroll.period_start, payroll.period_end)
            # استبعاد أيام الإجازة من الغياب وإضافة خصم للإجازات غير المدفوعة
            paid_dates, unpaid_dates = _get_leave_dates(payroll.employee_id, payroll.period_start, payroll.period_end)
            # إعادة حساب الغياب باستثناء أي يوم به إجازة (مدفوعة أو غير مدفوعة)
            # نحسب الغياب من جديد على مستوى الأيام
            # لبساطة التنفيذ: إنقاص عدد الأيام غير المدفوعة والمدفوعة من الغياب إن كانت محسوبة ضمن الغياب
            # (دون الدخول في تفاصيل الحضور اليومي)
            adj_absence = max(0, int(abs_days) - len(paid_dates) - len(unpaid_dates))
            payroll.absence_days = adj_absence
            payroll.late_minutes = late_mins
            # Compute deductions based on config
            cfg = current_app.config
            # basic fallback: if not provided, try employee.salary
            if not payroll.basic or payroll.basic == 0:
                emp = Employee.query.get(payroll.employee_id)
                payroll.basic = float(emp.salary or 0.0) if emp else 0.0
            daily_rate = (float(payroll.basic) / float(working_days or 30)) if (working_days or 0) > 0 else (float(payroll.basic) / 30.0)
            absence_rate = float(cfg.get('PAYROLL_ABSENCE_DEDUCTION_RATE', 1.0))
            payroll.absence_deduction = round(daily_rate * abs_days * absence_rate, 2)
            # late
            hourly_basic = (float(payroll.basic) / 240.0) if payroll.basic else 0.0
            per_hour = float(cfg.get('PAYROLL_LATE_DEDUCTION_PER_HOUR', 0.0)) or hourly_basic
            payroll.late_deduction = round(per_hour * (payroll.late_minutes or 0) / 60.0, 2)
            # خصم الإجازات غير المدفوعة
            payroll.unpaid_leave_days = len(unpaid_dates)
            payroll.unpaid_leave_deduction = round(daily_rate * payroll.unpaid_leave_days, 2)
        
        # Auto compute loan/advance monthly deduction if not provided
        if data.get('loan_deduction') is None:
            payroll.loan_deduction = _compute_loan_due_amount(payroll.employee_id, payroll.period_end)
        
        # Calculate net salary
        payroll.compute_net()
        
        db.session.add(payroll)
        db.session.commit()
        
        return jsonify({'success': True, 'id': payroll.id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating payroll: {e}")
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/api/payroll/<int:payroll_id>', methods=['PUT'])
@login_required
def update_payroll(payroll_id):
    """تحديث راتب"""
    if not current_user.has_permission(module='payroll', action='edit'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        payroll = Payroll.query.get_or_404(payroll_id)
        
        # Only allow editing if pending
        if payroll.status not in ['pending', 'approved']:
            return jsonify({'error': 'Cannot edit paid or cancelled payroll'}), 400
        
        data = request.get_json()
        
        # Update fields
        payroll.month = data.get('month', payroll.month)
        payroll.year = data.get('year', payroll.year)
        payroll.basic = data.get('basic', payroll.basic)
        payroll.housing_allowance = data.get('housing_allowance', payroll.housing_allowance)
        payroll.transport_allowance = data.get('transport_allowance', payroll.transport_allowance)
        payroll.food_allowance = data.get('food_allowance', payroll.food_allowance)
        payroll.phone_allowance = data.get('phone_allowance', payroll.phone_allowance)
        payroll.other_allowances = data.get('other_allowances', payroll.other_allowances)
        payroll.bonus = data.get('bonus', payroll.bonus)
        payroll.commission = data.get('commission', payroll.commission)
        payroll.incentives = data.get('incentives', payroll.incentives)
        payroll.overtime_hours = data.get('overtime_hours', payroll.overtime_hours)
        payroll.overtime_amount = data.get('overtime_amount', payroll.overtime_amount)
        payroll.absence_days = data.get('absence_days', payroll.absence_days)
        payroll.absence_deduction = data.get('absence_deduction', payroll.absence_deduction)
        payroll.late_minutes = data.get('late_minutes', payroll.late_minutes)
        payroll.late_deduction = data.get('late_deduction', payroll.late_deduction)
        payroll.loan_deduction = data.get('loan_deduction', payroll.loan_deduction)
        payroll.other_deductions = data.get('other_deductions', payroll.other_deductions)
        payroll.status = data.get('status', payroll.status)
        payroll.notes = data.get('notes', payroll.notes)
        
        # Update period dates
        payroll.period_start = date(payroll.year, payroll.month, 1)
        payroll.period_end = payroll.period_start + relativedelta(months=1, days=-1)
        
        # If asked to recalc from attendance
        if data.get('recalc_from_attendance'):
            before_net = float(payroll.net or 0.0)
            period_start = date(payroll.year, payroll.month, 1)
            period_end = period_start + relativedelta(months=1, days=-1)
            abs_days, late_mins, working_days = _compute_attendance_metrics(payroll.employee_id, period_start, period_end)
            paid_dates, unpaid_dates = _get_leave_dates(payroll.employee_id, period_start, period_end)
            adj_absence = max(0, int(abs_days) - len(paid_dates) - len(unpaid_dates))
            payroll.absence_days = adj_absence
            payroll.late_minutes = late_mins
            cfg = current_app.config
            daily_rate = (float(payroll.basic or 0.0) / float(working_days or 30)) if (working_days or 0) > 0 else (float(payroll.basic or 0.0) / 30.0)
            absence_rate = float(cfg.get('PAYROLL_ABSENCE_DEDUCTION_RATE', 1.0))
            payroll.absence_deduction = round(daily_rate * adj_absence * absence_rate, 2)
            hourly_basic = (float(payroll.basic or 0.0) / 240.0) if payroll.basic else 0.0
            per_hour = float(cfg.get('PAYROLL_LATE_DEDUCTION_PER_HOUR', 0.0)) or hourly_basic
            payroll.late_deduction = round(per_hour * (late_mins or 0) / 60.0, 2)

            # Also recalc monthly loan/advance due
            payroll.loan_deduction = _compute_loan_due_amount(payroll.employee_id, period_end)
            # Recalc unpaid leave deduction
            payroll.unpaid_leave_days = len(unpaid_dates)
            payroll.unpaid_leave_deduction = round(daily_rate * payroll.unpaid_leave_days, 2)

        # Recalculate net
        payroll.compute_net()

        # If this was a recalc operation, store the diff and timestamp
        if data.get('recalc_from_attendance'):
            after_net = float(payroll.net or 0.0)
            payroll.last_recalc_net_diff = round(after_net - before_net, 2)
            payroll.last_recalc_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating payroll: {e}")
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/api/payroll/<int:payroll_id>', methods=['DELETE'])
@login_required
def delete_payroll(payroll_id):
    """حذف راتب"""
    if not current_user.has_permission(module='payroll', action='delete'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        payroll = Payroll.query.get_or_404(payroll_id)
        
        # Only allow deleting if not paid
        if payroll.status == 'paid':
            return jsonify({'error': 'Cannot delete paid payroll'}), 400
        
        db.session.delete(payroll)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting payroll: {e}")
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/api/payroll/<int:payroll_id>/approve', methods=['POST'])
@login_required
def approve_payroll(payroll_id):
    """اعتماد راتب"""
    if not current_user.has_permission(module='payroll', action='approve'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        payroll = Payroll.query.get_or_404(payroll_id)
        
        if payroll.status != 'pending':
            return jsonify({'error': 'Only pending payrolls can be approved'}), 400
        
        payroll.status = 'approved'
        payroll.approved_by = current_user.id
        payroll.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving payroll: {e}")
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/api/payroll/<int:payroll_id>/pay', methods=['POST'])
@login_required
def pay_payroll(payroll_id):
    """تحديد الراتب كمدفوع"""
    if not current_user.has_permission(module='payroll', action='pay'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        payroll = Payroll.query.get_or_404(payroll_id)
        
        if payroll.status != 'approved':
            return jsonify({'error': 'Only approved payrolls can be marked as paid'}), 400
        
        payroll.status = 'paid'
        payroll.paid_by = current_user.id
        payroll.paid_at = datetime.utcnow()
        payroll.payment_date = datetime.utcnow().date()
        
        # Apply loan repayments upon payment using the amount already counted in payroll.loan_deduction
        try:
            if current_app.config.get('PAYROLL_AUTO_LOAN_DEDUCTION', True) and float(payroll.loan_deduction or 0.0) > 0:
                remaining_to_apply = float(payroll.loan_deduction or 0.0)
                loans = EmployeeLoan.query.filter(
                    EmployeeLoan.employee_id == payroll.employee_id,
                    EmployeeLoan.status == 'active'
                ).order_by(EmployeeLoan.issued_date.asc()).all()
                for loan in loans:
                    if remaining_to_apply <= 0:
                        break
                    if loan.start_date and loan.start_date > payroll.period_end:
                        continue
                    # Initialize remaining if None
                    if loan.remaining_amount is None:
                        loan.remaining_amount = float(loan.amount or 0.0)
                    if (loan.remaining_amount or 0.0) <= 0:
                        continue
                    monthly = loan.monthly_deduction
                    if (not monthly or monthly <= 0) and loan.amount and loan.installments:
                        try:
                            monthly = round(float(loan.amount) / float(loan.installments), 2)
                        except Exception:
                            monthly = 0.0
                    monthly = float(monthly or 0.0)
                    if monthly <= 0:
                        continue
                    apply_amt = min(monthly, float(loan.remaining_amount or 0.0), remaining_to_apply)
                    if apply_amt <= 0:
                        continue
                    loan.remaining_amount = round(float(loan.remaining_amount or 0.0) - apply_amt, 2)
                    loan.paid_installments = int((loan.paid_installments or 0)) + 1
                    if loan.remaining_amount <= 0:
                        loan.status = 'completed'
                        loan.completed_date = datetime.utcnow().date()
                    remaining_to_apply = round(remaining_to_apply - apply_amt, 2)
        except Exception as loan_err:
            current_app.logger.error(f"Error applying loan repayments on pay: {loan_err}")

        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking payroll as paid: {e}")
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/api/payroll/template/<int:employee_id>', methods=['GET'])
@login_required
def get_employee_template(employee_id):
    """الحصول على قالب راتب الموظف"""
    if not current_user.has_permission(module='payroll', action='view'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    template = PayrollTemplate.query.filter_by(employee_id=employee_id, is_active=True).first()
    
    if not template:
        return jsonify(None)
    
    return jsonify({
        'basic_salary': float(template.basic_salary or 0),
        'housing_allowance': float(template.housing_allowance or 0),
        'transport_allowance': float(template.transport_allowance or 0),
        'food_allowance': float(template.food_allowance or 0),
        'phone_allowance': float(template.phone_allowance or 0),
        'other_allowances': float(template.other_allowances or 0),
        'overtime_rate': float(template.overtime_rate or 1.5)
    })


@payroll_bp.route('/api/payroll/batch', methods=['POST'])
@login_required
def generate_batch():
    """إنشاء دفعة رواتب شهرية"""
    if not current_user.has_permission(module='payroll', action='create'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        month = data['month']
        year = data['year']
        
        # Check if batch already exists
        existing_count = Payroll.query.filter_by(month=month, year=year).count()
        if existing_count > 0:
            return jsonify({'error': f'Payroll batch already exists for this period ({existing_count} records)'}), 400
        
        # Get all active employees with templates
        templates = PayrollTemplate.query.join(Employee).filter(
            Employee.active == True,
            PayrollTemplate.is_active == True
        ).all()
        
        if not templates:
            return jsonify({'error': 'No active employee templates found'}), 400
        
        count = 0
        period_start = date(year, month, 1)
        period_end = period_start + relativedelta(months=1, days=-1)
        
        for template in templates:
            payroll = Payroll(
                employee_id=template.employee_id,
                month=month,
                year=year,
                period_start=period_start,
                period_end=period_end,
                basic=template.basic_salary,
                housing_allowance=template.housing_allowance,
                transport_allowance=template.transport_allowance,
                food_allowance=template.food_allowance,
                phone_allowance=template.phone_allowance,
                other_allowances=template.other_allowances,
                status='pending',
                generated_by=current_user.id,
                generated_at=datetime.utcnow()
            )
            
            # Auto compute attendance-based metrics
            abs_days, late_mins, working_days = _compute_attendance_metrics(template.employee_id, period_start, period_end)
            paid_dates, unpaid_dates = _get_leave_dates(template.employee_id, period_start, period_end)
            adj_absence = max(0, int(abs_days) - len(paid_dates) - len(unpaid_dates))
            payroll.absence_days = adj_absence
            payroll.late_minutes = late_mins
            cfg = current_app.config
            daily_rate = (float(payroll.basic) / float(working_days or 30)) if (working_days or 0) > 0 else (float(payroll.basic) / 30.0)
            absence_rate = float(cfg.get('PAYROLL_ABSENCE_DEDUCTION_RATE', 1.0))
            payroll.absence_deduction = round(daily_rate * adj_absence * absence_rate, 2)
            hourly_basic = (float(payroll.basic) / 240.0) if payroll.basic else 0.0
            per_hour = float(cfg.get('PAYROLL_LATE_DEDUCTION_PER_HOUR', 0.0)) or hourly_basic
            payroll.late_deduction = round(per_hour * (late_mins or 0) / 60.0, 2)
            payroll.unpaid_leave_days = len(unpaid_dates)
            payroll.unpaid_leave_deduction = round(daily_rate * payroll.unpaid_leave_days, 2)
            
            # Auto compute loan/advance deduction per employee
            payroll.loan_deduction = _compute_loan_due_amount(template.employee_id, period_end)

            # Calculate net
            payroll.compute_net()
            
            db.session.add(payroll)
            count += 1
        
        # Create batch record
        batch = PayrollBatch(
            month=month,
            year=year,
            period_start=period_start,
            period_end=period_end,
            total_employees=count,
            status='draft',
            generated_by=current_user.id
        )
        db.session.add(batch)
        
        db.session.commit()
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error generating batch: {e}")
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/api/payroll/recalc/batch', methods=['POST'])
@login_required
def batch_recalculate_payrolls():
    """إعادة حساب جميع رواتب شهر/سنة محددين (غير المدفوعة) من الحضور وتحديث خصم السلف.
    ترجع عدد السجلات التي تم تحديثها والمجموع الكلي للفروقات في الصافي.
    """
    if not current_user.has_permission(module='payroll', action='edit'):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.get_json() or {}
        month = int(data.get('month')) if data.get('month') is not None else None
        year = int(data.get('year')) if data.get('year') is not None else None
        if not month or not year:
            return jsonify({'error': 'Month and year are required'}), 400

        period_start = date(year, month, 1)
        period_end = period_start + relativedelta(months=1, days=-1)

        qs = Payroll.query.filter(
            Payroll.month == month,
            Payroll.year == year,
            Payroll.status.in_(['pending', 'approved'])
        ).all()

        updated = 0
        total_diff = 0.0
        cfg = current_app.config

        for p in qs:
            before_net = float(p.net or 0.0)

            abs_days, late_mins, working_days = _compute_attendance_metrics(p.employee_id, period_start, period_end)
            paid_dates, unpaid_dates = _get_leave_dates(p.employee_id, period_start, period_end)
            adj_absence = max(0, int(abs_days) - len(paid_dates) - len(unpaid_dates))
            p.absence_days = adj_absence
            p.late_minutes = late_mins

            daily_rate = (float(p.basic or 0.0) / float(working_days or 30)) if (working_days or 0) > 0 else (float(p.basic or 0.0) / 30.0)
            absence_rate = float(cfg.get('PAYROLL_ABSENCE_DEDUCTION_RATE', 1.0))
            p.absence_deduction = round(daily_rate * adj_absence * absence_rate, 2)

            hourly_basic = (float(p.basic or 0.0) / 240.0) if p.basic else 0.0
            per_hour = float(cfg.get('PAYROLL_LATE_DEDUCTION_PER_HOUR', 0.0)) or hourly_basic
            p.late_deduction = round(per_hour * (late_mins or 0) / 60.0, 2)

            # Update loan deduction
            p.loan_deduction = _compute_loan_due_amount(p.employee_id, period_end)
            # Update unpaid leave
            p.unpaid_leave_days = len(unpaid_dates)
            p.unpaid_leave_deduction = round(daily_rate * p.unpaid_leave_days, 2)

            # Recompute net
            p.compute_net()

            after_net = float(p.net or 0.0)
            diff = round(after_net - before_net, 2)
            p.last_recalc_net_diff = diff
            p.last_recalc_at = datetime.utcnow()
            updated += 1
            total_diff = round(total_diff + diff, 2)

        db.session.commit()

        return jsonify({'success': True, 'updated': updated, 'total_diff': total_diff})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error batch recalculating payrolls: {e}")
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/api/payroll/<int:payroll_id>/payslip', methods=['GET'])
@login_required
def download_payslip(payroll_id):
    """تحميل إيصال الراتب PDF - سيتم تطويره لاحقاً"""
    return jsonify({'error': 'Payslip generation not implemented yet'}), 501


@payroll_bp.route('/payroll/export')
@login_required
def payroll_export():
    """تصدير بيانات الرواتب إلى CSV"""
    if not current_user.has_permission(module='payroll', action='view'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # بناء الاستعلام
    query = Payroll.query
    
    # تطبيق الفلاتر
    period_start = request.args.get('period_start')
    period_end = request.args.get('period_end')
    employee_id = request.args.get('employee_id')
    
    if period_start:
        try:
            start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
            query = query.filter(Payroll.period_start >= start_date)
        except ValueError:
            pass
    
    if period_end:
        try:
            end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
            query = query.filter(Payroll.period_end <= end_date)
        except ValueError:
            pass
    
    if employee_id:
        query = query.filter_by(employee_id=int(employee_id))
    
    # جلب البيانات
    payrolls = query.order_by(Payroll.period_start.desc()).all()
    
    # إنشاء ملف CSV
    si = StringIO()
    writer = csv.writer(si)
    
    # كتابة الرأس
    writer.writerow([
        'ID',
        'اسم الموظف',
        'الفترة من',
        'الفترة إلى',
        'السنة',
        'الشهر',
        'الراتب الأساسي',
        'البدلات',
        'الخصومات',
        'صافي الراتب',
        'الحالة',
        'تاريخ الإنشاء'
    ])
    
    # كتابة البيانات
    for p in payrolls:
        total_allowances = (
            (p.housing_allowance or 0) +
            (p.transport_allowance or 0) +
            (p.food_allowance or 0) +
            (p.phone_allowance or 0) +
            (p.other_allowances or 0) +
            (p.commission or 0) +
            (p.overtime_amount or 0) +
            (p.incentives or 0)
        )
        
        total_deductions = (
            (p.absence_deduction or 0) +
            (p.late_deduction or 0) +
            (p.loan_deduction or 0) +
            (p.other_deductions or 0) +
            (p.health_insurance or 0)
        )
        
        writer.writerow([
            p.id,
            p.employee.name if p.employee else '',
            p.period_start.strftime('%Y-%m-%d') if p.period_start else '',
            p.period_end.strftime('%Y-%m-%d') if p.period_end else '',
            p.year or '',
            p.month or '',
            p.basic or 0,
            total_allowances,
            total_deductions,
            p.net or 0,
            p.status or '',
            p.generated_at.strftime('%Y-%m-%d %H:%M') if p.generated_at else ''
        ])
    
    # إنشاء الاستجابة
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=payroll_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8-sig"
    
    return output
