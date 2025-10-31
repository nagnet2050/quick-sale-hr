from flask import Blueprint, render_template, request, session, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app.models.employee import Employee
from app.models.payroll import Payroll
from app import db
from datetime import datetime
import io
import csv

payroll_bp = Blueprint('payroll', __name__)


def _apply_filters(query, start, end, employee_id):
    if start:
        try:
            s = datetime.strptime(start, '%Y-%m-%d').date()
            query = query.filter(Payroll.period_start >= s)
        except Exception:
            pass
    if end:
        try:
            e = datetime.strptime(end, '%Y-%m-%d').date()
            query = query.filter(Payroll.period_end <= e)
        except Exception:
            pass
    if employee_id:
        try:
            eid = int(employee_id)
            query = query.filter(Payroll.employee_id == eid)
        except Exception:
            pass
    return query


@payroll_bp.route('/payroll', methods=['GET', 'POST'])
@login_required
def payroll():
    # only admins/managers can manage payroll
    if current_user.role not in ('admin', 'manager'):
        return render_template('unauthorized.html')

    # employees for selector
    employees = Employee.query.order_by(Employee.name).all()

    # Generate payroll (POST)
    if request.method == 'POST':
        start = request.form.get('period_start')
        end = request.form.get('period_end')
        employee_id = request.form.get('employee_id')
        try:
            period_start = datetime.strptime(start, '%Y-%m-%d').date() if start else None
            period_end = datetime.strptime(end, '%Y-%m-%d').date() if end else None
        except Exception:
            period_start = None
            period_end = None

        # if an employee_id is provided, generate only for that employee, else for all active
        targets = []
        if employee_id:
            e = Employee.query.get(int(employee_id)) if employee_id.isdigit() else None
            if e:
                targets = [e]
        else:
            targets = Employee.query.filter_by(active=True).all()

        for emp in targets:
            basic = emp.salary or 0.0
            allowances = round(basic * 0.1, 2)  # example rule
            # read optional overrides from form (bonus, overtime, deductions)
            try:
                bonus = float(request.form.get('bonus') or 0.0)
            except Exception:
                bonus = 0.0
            try:
                overtime = float(request.form.get('overtime') or 0.0)
            except Exception:
                overtime = 0.0
            try:
                deductions = float(request.form.get('deductions') or 0.0)
            except Exception:
                deductions = 0.0

            p = Payroll(employee_id=emp.id, period_start=period_start, period_end=period_end, basic=basic, allowances=allowances, bonus=bonus, overtime=overtime, deductions=deductions, generated_by=current_user.id)
            p.compute_net()
            db.session.add(p)
        db.session.commit()
        flash('Payroll generated', 'success')
        return redirect(url_for('payroll.payroll'))

    # LIST with filters (GET)
    start = request.args.get('period_start')
    end = request.args.get('period_end')
    employee_id = request.args.get('employee_id')

    q = Payroll.query.order_by(Payroll.generated_at.desc())
    q = _apply_filters(q, start, end, employee_id)
    rows = q.limit(1000).all()

    payroll_rows = []
    for r in rows:
        emp = Employee.query.get(r.employee_id)
        payroll_rows.append({
            'id': r.id,
            'employee': emp.name if emp else '—',
            'period_start': r.period_start,
            'period_end': r.period_end,
            'basic': r.basic,
            'allowances': r.allowances,
            'deductions': r.deductions,
            'net': r.net,
            'generated_at': r.generated_at
        })

    return render_template('payroll.html', payroll_rows=payroll_rows, employees=employees, filters={'period_start': start, 'period_end': end, 'employee_id': employee_id}, lang=session.get('lang', 'ar'))


@payroll_bp.route('/payroll/export', methods=['GET'])
@login_required
def payroll_export():
    if current_user.role not in ('admin', 'manager'):
        return render_template('unauthorized.html')

    start = request.args.get('period_start')
    end = request.args.get('period_end')
    employee_id = request.args.get('employee_id')

    q = Payroll.query.order_by(Payroll.generated_at.desc())
    q = _apply_filters(q, start, end, employee_id)
    rows = q.limit(5000).all()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID','Employee','Period Start','Period End','Basic','Allowances','Deductions','Net','Generated At'])
    for r in rows:
        emp = Employee.query.get(r.employee_id)
        writer.writerow([r.id, emp.name if emp else '', r.period_start, r.period_end, r.basic, r.allowances, r.deductions, r.net, r.generated_at])
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=payroll_export.csv"})


@payroll_bp.route('/payroll/payslip/<int:pay_id>', methods=['GET'])
@login_required
def payroll_payslip(pay_id):
    if current_user.role not in ('admin', 'manager'):
        return render_template('unauthorized.html')
    p = Payroll.query.get(pay_id)
    if not p:
        return ("", 404)
    emp = Employee.query.get(p.employee_id)

    # Try PDF via reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        import os

        buffer = io.BytesIO()
        width, height = A4
        c = canvas.Canvas(buffer, pagesize=A4)

        # Arabic labels
        labels_ar = {
            'Payslip': 'قسيمة راتب',
            'Employee': 'الموظف',
            'Period': 'الفترة',
            'Basic': 'الأساسي',
            'Allowances': 'البدلات',
            'Bonus': 'المكافأة',
            'Overtime': 'عمل إضافي',
            'Deductions': 'الخصومات',
            'Tax': 'الضريبة',
            'Insurance': 'التأمين',
            'Net': 'الصافي',
            'Generated at': 'تاريخ الإنشاء'
        }

        # Draw logo if configured
        logo_cfg = current_app.config.get('LOGO_PATH')
        if logo_cfg:
            try:
                logo_path = os.path.join(current_app.root_path, logo_cfg.lstrip('/\\'))
                if os.path.exists(logo_path):
                    img_w = 40 * mm
                    img_h = 20 * mm
                    c.drawImage(logo_path, 40, height - img_h - 40, width=img_w, height=img_h, preserveAspectRatio=True)
            except Exception:
                pass

        # Header (RTL)
        c.setFont('Helvetica-Bold', 16)
        c.drawRightString(width - 40, height - 60, labels_ar['Payslip'])
        c.setFont('Helvetica', 10)
        c.drawRightString(width - 40, height - 80, f"{labels_ar['Employee']}: {emp.name if emp else ''}")
        c.drawRightString(width - 40, height - 95, f"{labels_ar['Period']}: {p.period_start} - {p.period_end}")

        # Table of components (RTL)
        table_x = width - 40
        table_y = height - 160
        line_height = 16

        rows = [
            (labels_ar['Basic'], getattr(p, 'basic', 0.0)),
            (labels_ar['Allowances'], getattr(p, 'allowances', 0.0)),
            (labels_ar['Bonus'], getattr(p, 'bonus', 0.0)),
            (labels_ar['Overtime'], getattr(p, 'overtime', 0.0)),
            (labels_ar['Deductions'], getattr(p, 'deductions', 0.0)),
            (labels_ar['Tax'], getattr(p, 'tax', 0.0)),
            (labels_ar['Insurance'], getattr(p, 'insurance', 0.0)),
        ]

        # Draw table header
        c.setFont('Helvetica-Bold', 10)
        c.drawRightString(table_x, table_y, 'المكون')
        c.drawRightString(table_x - 120, table_y, 'المبلغ')
        c.setStrokeColor(colors.grey)
        c.line(table_x - 120, table_y - 2, table_x, table_y - 2)

        # Draw rows RTL
        c.setFont('Helvetica', 10)
        y = table_y - line_height
        for label, value in rows:
            c.drawRightString(table_x, y, label)
            c.drawRightString(table_x - 120, y, f'{value:.2f}')
            y -= line_height

        # Net
        c.setFont('Helvetica-Bold', 11)
        c.drawRightString(table_x, y - 4, labels_ar['Net'])
        c.drawRightString(table_x - 120, y - 4, f'{getattr(p, "net", 0.0):.2f}')

        # Footer
        c.setFont('Helvetica', 8)
        c.setFillColor(colors.grey)
        c.drawRightString(width - 40, 40, f"{labels_ar['Generated at']}: {p.generated_at}")

        c.showPage()
        c.save()
        buffer.seek(0)
        from flask import send_file
        return send_file(buffer, mimetype='application/pdf', download_name=f'payslip_{pay_id}.pdf', as_attachment=True)
    except Exception:
        # fallback: render HTML template
        rendered = render_template('payslip.html', p=p, emp=emp, lang=session.get('lang', 'ar'))
        # return as HTML download
        return Response(rendered, mimetype='text/html', headers={"Content-Disposition":f"attachment;filename=payslip_{pay_id}.html"})
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.employee import Employee
from app.models.payroll import Payroll
from app import db
from datetime import datetime
import io

payroll_bp = Blueprint('payroll', __name__)


@payroll_bp.route('/payroll', methods=['GET', 'POST'])
@login_required
def payroll():
    # only admins/managers can generate payroll
    if current_user.role not in ('admin', 'manager'):
        return render_template('unauthorized.html')
    payroll_rows = []
    if request.method == 'POST':
        # simple period inputs
        start = request.form.get('period_start')
        end = request.form.get('period_end')
        try:
            period_start = datetime.strptime(start, '%Y-%m-%d').date() if start else None
            period_end = datetime.strptime(end, '%Y-%m-%d').date() if end else None
        except Exception:
            period_start = None
            period_end = None
        employees = Employee.query.filter_by(active=True).all()
        for emp in employees:
            basic = emp.salary or 0.0
            allowances = round(basic * 0.1, 2)  # example: 10% allowance
            deductions = 0.0
            p = Payroll(employee_id=emp.id, period_start=period_start, period_end=period_end, basic=basic, allowances=allowances, deductions=deductions, generated_by=current_user.id)
            p.compute_net()
            db.session.add(p)
            db.session.commit()
        flash('Payroll generated for active employees', 'success')
        return redirect(url_for('payroll.payroll'))

    # list recent payroll entries
    rows = Payroll.query.order_by(Payroll.generated_at.desc()).limit(100).all()
    payroll_rows = []
    for r in rows:
        emp = Employee.query.get(r.employee_id)
        payroll_rows.append({
            'id': r.id,
            'employee': emp.name if emp else '—',
            'period_start': r.period_start,
            'period_end': r.period_end,
            'basic': r.basic,
            'allowances': r.allowances,
            'deductions': r.deductions,
            'net': r.net,
            'generated_at': r.generated_at
        })
    return render_template('payroll.html', payroll_rows=payroll_rows, lang=session.get('lang', 'ar'))


@payroll_bp.route('/payroll/export', methods=['GET'])
@login_required
def payroll_export():
    # only admins/managers
    if current_user.role not in ('admin', 'manager'):
        return render_template('unauthorized.html')
    import csv
    from io import StringIO
    rows = Payroll.query.order_by(Payroll.generated_at.desc()).limit(1000).all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID','Employee','Period Start','Period End','Basic','Allowances','Deductions','Net','Generated At'])
    for r in rows:
        emp = Employee.query.get(r.employee_id)
        writer.writerow([r.id, emp.name if emp else '', r.period_start, r.period_end, r.basic, r.allowances, r.deductions, r.net, r.generated_at])
    output = si.getvalue()
    from flask import Response
    return Response(output, mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=payroll_export.csv"})


@payroll_bp.route('/payroll/payslip/<int:pay_id>', methods=['GET'])
@login_required
def payroll_payslip(pay_id):
    # only admins/managers
    if current_user.role not in ('admin', 'manager'):
        return render_template('unauthorized.html')
    p = Payroll.query.get(pay_id)
    if not p:
        return ("", 404)
    emp = Employee.query.get(p.employee_id)
    # Try to generate PDF via reportlab if available
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        text = c.beginText(40, 800)
        text.setFont('Helvetica', 12)
        text.textLine(f'Payslip for: {emp.name if emp else ""}')
        text.textLine(f'Period: {p.period_start} - {p.period_end}')
        text.textLine(f'Basic: {p.basic}')
        text.textLine(f'Allowances: {p.allowances}')
        text.textLine(f'Deductions: {p.deductions}')
        text.textLine(f'Net: {p.net}')
        c.drawText(text)
        c.showPage()
        c.save()
        buffer.seek(0)
        from flask import send_file
        return send_file(buffer, mimetype='application/pdf', download_name=f'payslip_{pay_id}.pdf', as_attachment=True)
    except Exception:
        # Fallback: return simple HTML payslip as attachment
        html = f"""
        <html><body>
        <h2>Payslip for: {emp.name if emp else ''}</h2>
        <p>Period: {p.period_start} - {p.period_end}</p>
        <p>Basic: {p.basic}</p>
        <p>Allowances: {p.allowances}</p>
        <p>Deductions: {p.deductions}</p>
        <p><strong>Net: {p.net}</strong></p>
        </body></html>
        """
        from flask import Response
        return Response(html, mimetype='text/html', headers={"Content-Disposition":f"attachment;filename=payslip_{pay_id}.html"})
from flask import Blueprint, render_template, request, session
from flask_login import login_required, current_user
from app.models.payroll import Payroll
from app.models.employee import Employee
from app import db

payroll_bp = Blueprint('payroll', __name__)

@payroll_bp.route('/payroll', methods=['GET', 'POST'])
@login_required
def payroll():
    # TODO: Payroll management logic
    return render_template('payroll.html', lang=session.get('lang', 'ar'))
