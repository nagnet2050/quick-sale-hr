from flask import Blueprint, render_template, session
from flask_login import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # TODO: Fetch attendance stats, headcount, shortcuts
    return render_template('dashboard.html', lang=session.get('lang', 'ar'))
