from flask import Blueprint, render_template, session
from flask_login import login_required

presence_status_bp = Blueprint('presence_status', __name__)

@presence_status_bp.route('/presence-status')
@login_required
def presence_status():
    return render_template('presence_status.html', lang=session.get('lang', 'ar'))
