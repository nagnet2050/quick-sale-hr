from flask import Blueprint, render_template, session

mss_bp = Blueprint('mss', __name__)

@mss_bp.route('/mss')
def mss_home():
    return render_template('mss.html', lang=session.get('lang', 'ar'))
