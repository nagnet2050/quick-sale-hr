from flask import Blueprint, render_template, session

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/ai')
def ai_home():
    return render_template('ai.html', lang=session.get('lang', 'ar'))
