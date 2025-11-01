from flask import Blueprint, render_template, session

external_workforce_bp = Blueprint('external_workforce', __name__)

@external_workforce_bp.route('/external-workforce')
def external_workforce_home():
    return render_template('external_workforce.html', lang=session.get('lang', 'ar'))
