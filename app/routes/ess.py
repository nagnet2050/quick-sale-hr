from flask import Blueprint, render_template, session

ess_bp = Blueprint('ess', __name__)

@ess_bp.route('/ess')
def ess_home():
    return render_template('ess.html', lang=session.get('lang', 'ar'))
