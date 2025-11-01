from flask import Blueprint, render_template, session

ehs_bp = Blueprint('ehs', __name__)

@ehs_bp.route('/ehs')
def ehs_home():
    return render_template('ehs.html', lang=session.get('lang', 'ar'))
