from flask import Blueprint, render_template, session

surveys_bp = Blueprint('surveys', __name__)

@surveys_bp.route('/surveys')
def surveys_home():
    return render_template('surveys.html', lang=session.get('lang', 'ar'))
