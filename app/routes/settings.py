from flask import Blueprint, render_template, request, session
from flask_login import login_required, current_user
from app.models.settings import Settings
from app import db

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if current_user.role != 'admin':
        return render_template('unauthorized.html')
    # TODO: Handle settings update
    return render_template('settings.html', lang=session.get('lang', 'ar'))
