from flask import Blueprint, render_template, session

lms_bp = Blueprint('lms', __name__)

@lms_bp.route('/lms')
def lms_home():
    return render_template('lms.html', lang=session.get('lang', 'ar'))
