from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from app.permissions import has_permission

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    lang = session.get('lang', 'ar')
    # إذا لم يكن المستخدم مديرًا أو أدمن، اعرض لوحة الموظف المبسطة
    if not has_permission(['admin', 'manager']):
        return render_template('dashboard_employee.html', lang=lang)
    # لوحة المدير/الأدمن
    return render_template('dashboard.html', lang=lang)
