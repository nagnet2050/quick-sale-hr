from flask import Blueprint, render_template, session
from flask_login import login_required

ats_bp = Blueprint('ats', __name__)

@ats_bp.route('/ats')
@login_required
def ats_home():
    return render_template('ats.html', lang=session.get('lang', 'ar'))
