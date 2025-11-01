from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.models.user import User
from app import db
from werkzeug.security import check_password_hash, generate_password_hash

account_bp = Blueprint('account', __name__)

@account_bp.route('/account/settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    """صفحة تغيير بيانات الحساب"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'change_username':
            new_username = request.form.get('new_username', '').strip()
            password = request.form.get('password', '')
            
            if not new_username:
                flash('اسم المستخدم لا يمكن أن يكون فارغاً', 'danger')
                return redirect(url_for('account.account_settings'))
            
            if not password or not current_user.check_password(password):
                flash('كلمة المرور غير صحيحة', 'danger')
                return redirect(url_for('account.account_settings'))
            
            # التحقق من عدم استخدام اسم المستخدم من قبل
            if User.query.filter_by(username=new_username).first():
                flash('اسم المستخدم موجود بالفعل', 'danger')
                return redirect(url_for('account.account_settings'))
            
            current_user.username = new_username
            db.session.commit()
            flash('تم تغيير اسم المستخدم بنجاح', 'success')
            return redirect(url_for('account.account_settings'))
        
        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not current_password or not current_user.check_password(current_password):
                flash('كلمة المرور الحالية غير صحيحة', 'danger')
                return redirect(url_for('account.account_settings'))
            
            if not new_password:
                flash('كلمة المرور الجديدة لا يمكن أن تكون فارغة', 'danger')
                return redirect(url_for('account.account_settings'))
            
            if new_password != confirm_password:
                flash('كلمات المرور الجديدة غير متطابقة', 'danger')
                return redirect(url_for('account.account_settings'))
            
            if len(new_password) < 4:
                flash('كلمة المرور يجب أن تكون 4 أحرف على الأقل', 'danger')
                return redirect(url_for('account.account_settings'))
            
            current_user.set_password(new_password)
            db.session.commit()
            flash('تم تغيير كلمة المرور بنجاح', 'success')
            return redirect(url_for('account.account_settings'))
    
    return render_template('account_settings.html', user=current_user, lang=session.get('lang', 'ar'))
