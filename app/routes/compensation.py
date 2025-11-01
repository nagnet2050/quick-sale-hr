from flask import Blueprint, render_template, session

compensation_bp = Blueprint('compensation', __name__)

@compensation_bp.route('/compensation')
def compensation_home():
    return render_template('compensation.html', lang=session.get('lang', 'ar'))
