from flask import Blueprint, render_template, session, request, jsonify
from datetime import date
from app.models.payroll import Payroll
from app import db

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
def analytics_home():
    return render_template('analytics.html', lang=session.get('lang', 'ar'))


@analytics_bp.route('/api/analytics/payroll-summary', methods=['GET'])
def payroll_summary():
    """ملخص شهري للرواتب: إجمالي الصافي، إجمالي خصم السلف، الغياب والتأخير.
    Params: month, year (اختياريان، الافتراضي الشهر الحالي)
    """
    try:
        today = date.today()
        month = request.args.get('month', type=int) or today.month
        year = request.args.get('year', type=int) or today.year

        qs = Payroll.query.filter(Payroll.month == month, Payroll.year == year)

        total_net = db.session.query(db.func.coalesce(db.func.sum(Payroll.net), 0.0)).filter(Payroll.month == month, Payroll.year == year).scalar() or 0.0
        total_loan = db.session.query(db.func.coalesce(db.func.sum(Payroll.loan_deduction), 0.0)).filter(Payroll.month == month, Payroll.year == year).scalar() or 0.0
        total_absence_days = db.session.query(db.func.coalesce(db.func.sum(Payroll.absence_days), 0)).filter(Payroll.month == month, Payroll.year == year).scalar() or 0
        total_late_minutes = db.session.query(db.func.coalesce(db.func.sum(Payroll.late_minutes), 0)).filter(Payroll.month == month, Payroll.year == year).scalar() or 0

        return jsonify({
            'success': True,
            'month': month,
            'year': year,
            'total_net': float(total_net),
            'total_loan_deduction': float(total_loan),
            'total_absence_days': int(total_absence_days),
            'total_late_minutes': int(total_late_minutes)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
