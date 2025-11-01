from flask import Blueprint, render_template, session
from flask_login import login_required

succession_bp = Blueprint('succession', __name__)

@succession_bp.route('/succession')
@login_required
def succession_home():
    return render_template('succession.html', lang=session.get('lang', 'ar'))
