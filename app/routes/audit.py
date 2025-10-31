from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from app.models.audit import Audit

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/admin/audit')
@login_required
def audit_list():
    if current_user.role != 'admin':
        return render_template('unauthorized.html')
    records = Audit.query.order_by(Audit.timestamp.desc()).limit(500).all()
    return render_template('audit.html', records=records, lang=session.get('lang', 'ar'))
