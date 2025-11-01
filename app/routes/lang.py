from flask import Blueprint, redirect, url_for, request, session

lang_bp = Blueprint('lang', __name__)

@lang_bp.route('/lang/<lang>')
def set_lang(lang):
    if lang not in ['ar', 'en']:
        lang = 'ar'
    session['lang'] = lang
    # Redirect back to previous page or dashboard
    next_url = request.referrer or url_for('dashboard.dashboard')
    return redirect(next_url)
