from flask import Blueprint, render_template, session

rewards_bp = Blueprint('rewards', __name__)

@rewards_bp.route('/rewards')
def rewards_home():
    return render_template('rewards.html', lang=session.get('lang', 'ar'))
