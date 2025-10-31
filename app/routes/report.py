from flask import Blueprint, render_template, request, session
from flask_login import login_required, current_user
from app.models.report import Report
from app import db

report_bp = Blueprint('report', __name__)

@report_bp.route('/report', methods=['GET'])
@login_required
def report():
    # TODO: Advanced reporting logic
    return render_template('report.html', lang=session.get('lang', 'ar'))
