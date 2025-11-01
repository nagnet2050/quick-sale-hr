from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.settings import Settings
from app import db
from app.permissions import has_permission
from datetime import datetime
import os
from werkzeug.utils import secure_filename

settings_bp = Blueprint('settings', __name__)

UPLOAD_FOLDER = 'app/static/uploads/company'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@settings_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    """عرض صفحة الإعدادات"""
    if not has_permission('settings_view'):
        return render_template('unauthorized.html', lang=session.get('lang', 'ar'))
    
    settings_obj = Settings.get_settings()
    return render_template('settings.html', 
                         settings=settings_obj,
                         lang=session.get('lang', 'ar'))

@settings_bp.route('/api/settings/update', methods=['POST'])
@login_required
def update_settings():
    """تحديث الإعدادات"""
    if not has_permission('settings_edit'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    try:
        data = request.form
        settings_obj = Settings.get_settings()
        
        # معلومات الشركة
        if 'company_name_ar' in data:
            settings_obj.company_name_ar = data['company_name_ar']
        if 'company_name_en' in data:
            settings_obj.company_name_en = data['company_name_en']
        if 'company_email' in data:
            settings_obj.company_email = data['company_email']
        if 'company_phone' in data:
            settings_obj.company_phone = data['company_phone']
        if 'company_address_ar' in data:
            settings_obj.company_address_ar = data['company_address_ar']
        if 'company_address_en' in data:
            settings_obj.company_address_en = data['company_address_en']
        if 'company_website' in data:
            settings_obj.company_website = data['company_website']
        if 'tax_number' in data:
            settings_obj.tax_number = data['tax_number']
        if 'commercial_register' in data:
            settings_obj.commercial_register = data['commercial_register']
        
        # إعدادات الموقع
        if 'company_lat' in data and data['company_lat']:
            settings_obj.company_lat = float(data['company_lat'])
        if 'company_lng' in data and data['company_lng']:
            settings_obj.company_lng = float(data['company_lng'])
        if 'allowed_radius_meters' in data:
            settings_obj.allowed_radius_meters = int(data['allowed_radius_meters'])
        
        # أوقات العمل
        if 'work_start' in data:
            settings_obj.work_start = data['work_start']
        if 'work_end' in data:
            settings_obj.work_end = data['work_end']
        if 'break_start' in data:
            settings_obj.break_start = data['break_start']
        if 'break_end' in data:
            settings_obj.break_end = data['break_end']
        if 'work_days' in data:
            settings_obj.work_days = data['work_days']
        if 'weekend_days' in data:
            settings_obj.weekend_days = data['weekend_days']
        
        # إعدادات الحضور
        if 'presence_interval_min' in data:
            settings_obj.presence_interval_min = int(data['presence_interval_min'])
        if 'presence_grace_min' in data:
            settings_obj.presence_grace_min = int(data['presence_grace_min'])
        if 'late_arrival_threshold_min' in data:
            settings_obj.late_arrival_threshold_min = int(data['late_arrival_threshold_min'])
        if 'early_leave_threshold_min' in data:
            settings_obj.early_leave_threshold_min = int(data['early_leave_threshold_min'])
        if 'auto_checkout_time' in data:
            settings_obj.auto_checkout_time = data['auto_checkout_time']
        
        # Boolean fields
        settings_obj.presence_sound_enabled = 'presence_sound_enabled' in data
        settings_obj.auto_checkout_enabled = 'auto_checkout_enabled' in data
        settings_obj.require_checkout_location = 'require_checkout_location' in data
        
        # إعدادات الإجازات
        if 'annual_leave_days' in data:
            settings_obj.annual_leave_days = int(data['annual_leave_days'])
        if 'sick_leave_days' in data:
            settings_obj.sick_leave_days = int(data['sick_leave_days'])
        if 'casual_leave_days' in data:
            settings_obj.casual_leave_days = int(data['casual_leave_days'])
        if 'max_carry_forward_days' in data:
            settings_obj.max_carry_forward_days = int(data['max_carry_forward_days'])
        if 'min_leave_notice_days' in data:
            settings_obj.min_leave_notice_days = int(data['min_leave_notice_days'])
        
        settings_obj.carry_forward_leaves = 'carry_forward_leaves' in data
        settings_obj.leave_approval_required = 'leave_approval_required' in data
        
        # إعدادات الرواتب
        if 'payroll_currency' in data:
            settings_obj.payroll_currency = data['payroll_currency']
        if 'payroll_day' in data:
            settings_obj.payroll_day = int(data['payroll_day'])
        if 'overtime_rate' in data:
            settings_obj.overtime_rate = float(data['overtime_rate'])
        if 'weekend_overtime_rate' in data:
            settings_obj.weekend_overtime_rate = float(data['weekend_overtime_rate'])
        if 'holiday_overtime_rate' in data:
            settings_obj.holiday_overtime_rate = float(data['holiday_overtime_rate'])
        if 'late_deduction_rate' in data:
            settings_obj.late_deduction_rate = float(data['late_deduction_rate'])
        
        settings_obj.auto_calculate_overtime = 'auto_calculate_overtime' in data
        settings_obj.deduct_late_from_salary = 'deduct_late_from_salary' in data
        
        # إعدادات الإشعارات
        settings_obj.email_notifications_enabled = 'email_notifications_enabled' in data
        settings_obj.sms_notifications_enabled = 'sms_notifications_enabled' in data
        settings_obj.whatsapp_notifications_enabled = 'whatsapp_notifications_enabled' in data
        settings_obj.notify_on_late_arrival = 'notify_on_late_arrival' in data
        settings_obj.notify_on_absence = 'notify_on_absence' in data
        settings_obj.notify_on_leave_request = 'notify_on_leave_request' in data
        settings_obj.notify_managers_on_employee_actions = 'notify_managers_on_employee_actions' in data
        
        # إعدادات الأمان
        if 'password_min_length' in data:
            settings_obj.password_min_length = int(data['password_min_length'])
        if 'password_expiry_days' in data:
            settings_obj.password_expiry_days = int(data['password_expiry_days'])
        if 'max_login_attempts' in data:
            settings_obj.max_login_attempts = int(data['max_login_attempts'])
        if 'session_timeout_minutes' in data:
            settings_obj.session_timeout_minutes = int(data['session_timeout_minutes'])
        
        settings_obj.require_password_change_first_login = 'require_password_change_first_login' in data
        settings_obj.two_factor_enabled = 'two_factor_enabled' in data
        
        # إعدادات النظام
        if 'language' in data:
            settings_obj.language = data['language']
        if 'timezone' in data:
            settings_obj.timezone = data['timezone']
        if 'date_format' in data:
            settings_obj.date_format = data['date_format']
        if 'time_format' in data:
            settings_obj.time_format = data['time_format']
        if 'fiscal_year_start_month' in data:
            settings_obj.fiscal_year_start_month = int(data['fiscal_year_start_month'])
        if 'records_per_page' in data:
            settings_obj.records_per_page = int(data['records_per_page'])
        
        # إعدادات التقارير
        if 'report_footer_text_ar' in data:
            settings_obj.report_footer_text_ar = data['report_footer_text_ar']
        if 'report_footer_text_en' in data:
            settings_obj.report_footer_text_en = data['report_footer_text_en']
        
        settings_obj.auto_backup_enabled = 'auto_backup_enabled' in data
        settings_obj.report_logo_enabled = 'report_logo_enabled' in data
        
        # إعدادات الأداء
        if 'performance_review_frequency_months' in data:
            settings_obj.performance_review_frequency_months = int(data['performance_review_frequency_months'])
        if 'min_performance_score' in data:
            settings_obj.min_performance_score = float(data['min_performance_score'])
        if 'max_performance_score' in data:
            settings_obj.max_performance_score = float(data['max_performance_score'])
        
        settings_obj.auto_generate_performance_alerts = 'auto_generate_performance_alerts' in data

        # مزود البريد - Email Provider config & keys (store securely)
        if 'email_provider' in data:
            settings_obj.email_provider = (data['email_provider'] or '').upper() or None
        if 'sendgrid_api_key' in data:
            # حفظ كما هو؛ يمكن لاحقاً التشفير قبل التخزين إذا لزم
            settings_obj.sendgrid_api_key = data['sendgrid_api_key'] or None
        if 'sendgrid_password_changed_template_id' in data:
            settings_obj.sendgrid_password_changed_template_id = data['sendgrid_password_changed_template_id'] or None
        
        # تحديث البيانات الوصفية
        settings_obj.updated_at = datetime.utcnow()
        settings_obj.updated_by = current_user.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث الإعدادات بنجاح' if session.get('lang') == 'ar' else 'Settings updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@settings_bp.route('/api/settings/upload-logo', methods=['POST'])
@login_required
def upload_logo():
    """رفع شعار الشركة"""
    if not has_permission('settings_edit'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    try:
        if 'logo' not in request.files:
            return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
        
        if file and allowed_file(file.filename):
            # إنشاء المجلد إذا لم يكن موجوداً
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # حفظ الملف
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logo_{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # تحديث قاعدة البيانات
            settings_obj = Settings.get_settings()
            settings_obj.company_logo = f"/static/uploads/company/{filename}"
            settings_obj.updated_at = datetime.utcnow()
            settings_obj.updated_by = current_user.id
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'تم رفع الشعار بنجاح',
                'logo_url': settings_obj.company_logo
            })
        
        return jsonify({'success': False, 'message': 'نوع الملف غير مدعوم'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@settings_bp.route('/api/settings/get', methods=['GET'])
@login_required
def get_settings():
    """الحصول على الإعدادات الحالية"""
    if not has_permission('settings_view'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    try:
        settings_obj = Settings.get_settings()
        
        return jsonify({
            'success': True,
            'settings': {
                # معلومات الشركة
                'company_name_ar': settings_obj.company_name_ar,
                'company_name_en': settings_obj.company_name_en,
                'company_logo': settings_obj.company_logo,
                'company_email': settings_obj.company_email,
                'company_phone': settings_obj.company_phone,
                'company_address_ar': settings_obj.company_address_ar,
                'company_address_en': settings_obj.company_address_en,
                'company_website': settings_obj.company_website,
                'tax_number': settings_obj.tax_number,
                'commercial_register': settings_obj.commercial_register,
                
                # إعدادات الموقع
                'company_lat': settings_obj.company_lat,
                'company_lng': settings_obj.company_lng,
                'allowed_radius_meters': settings_obj.allowed_radius_meters,
                
                # أوقات العمل
                'work_start': settings_obj.work_start,
                'work_end': settings_obj.work_end,
                'break_start': settings_obj.break_start,
                'break_end': settings_obj.break_end,
                'work_days': settings_obj.work_days,
                'weekend_days': settings_obj.weekend_days,
                
                # إعدادات الحضور
                'presence_interval_min': settings_obj.presence_interval_min,
                'presence_grace_min': settings_obj.presence_grace_min,
                'presence_sound_enabled': settings_obj.presence_sound_enabled,
                'late_arrival_threshold_min': settings_obj.late_arrival_threshold_min,
                'early_leave_threshold_min': settings_obj.early_leave_threshold_min,
                'auto_checkout_enabled': settings_obj.auto_checkout_enabled,
                'auto_checkout_time': settings_obj.auto_checkout_time,
                'require_checkout_location': settings_obj.require_checkout_location,
                
                # إعدادات الإجازات
                'annual_leave_days': settings_obj.annual_leave_days,
                'sick_leave_days': settings_obj.sick_leave_days,
                'casual_leave_days': settings_obj.casual_leave_days,
                'carry_forward_leaves': settings_obj.carry_forward_leaves,
                'max_carry_forward_days': settings_obj.max_carry_forward_days,
                'leave_approval_required': settings_obj.leave_approval_required,
                'min_leave_notice_days': settings_obj.min_leave_notice_days,
                
                # إعدادات الرواتب
                'payroll_currency': settings_obj.payroll_currency,
                'payroll_day': settings_obj.payroll_day,
                'overtime_rate': settings_obj.overtime_rate,
                'weekend_overtime_rate': settings_obj.weekend_overtime_rate,
                'holiday_overtime_rate': settings_obj.holiday_overtime_rate,
                'auto_calculate_overtime': settings_obj.auto_calculate_overtime,
                'deduct_late_from_salary': settings_obj.deduct_late_from_salary,
                'late_deduction_rate': settings_obj.late_deduction_rate,
                
                # إعدادات الإشعارات
                'email_notifications_enabled': settings_obj.email_notifications_enabled,
                'sms_notifications_enabled': settings_obj.sms_notifications_enabled,
                'whatsapp_notifications_enabled': settings_obj.whatsapp_notifications_enabled,
                'notify_on_late_arrival': settings_obj.notify_on_late_arrival,
                'notify_on_absence': settings_obj.notify_on_absence,
                'notify_on_leave_request': settings_obj.notify_on_leave_request,
                'notify_managers_on_employee_actions': settings_obj.notify_managers_on_employee_actions,
                
                # إعدادات الأمان
                'password_min_length': settings_obj.password_min_length,
                'password_expiry_days': settings_obj.password_expiry_days,
                'max_login_attempts': settings_obj.max_login_attempts,
                'session_timeout_minutes': settings_obj.session_timeout_minutes,
                'require_password_change_first_login': settings_obj.require_password_change_first_login,
                'two_factor_enabled': settings_obj.two_factor_enabled,
                
                # إعدادات النظام
                'language': settings_obj.language,
                'timezone': settings_obj.timezone,
                'date_format': settings_obj.date_format,
                'time_format': settings_obj.time_format,
                'fiscal_year_start_month': settings_obj.fiscal_year_start_month,
                'records_per_page': settings_obj.records_per_page,
                
                # إعدادات التقارير
                'auto_backup_enabled': settings_obj.auto_backup_enabled,
                'report_logo_enabled': settings_obj.report_logo_enabled,
                'report_footer_text_ar': settings_obj.report_footer_text_ar,
                'report_footer_text_en': settings_obj.report_footer_text_en,
                
                # إعدادات الأداء
                'performance_review_frequency_months': settings_obj.performance_review_frequency_months,
                'min_performance_score': settings_obj.min_performance_score,
                'max_performance_score': settings_obj.max_performance_score,
                'auto_generate_performance_alerts': settings_obj.auto_generate_performance_alerts
                ,
                # Email provider
                'email_provider': settings_obj.email_provider or 'SMTP',
                'sendgrid_api_key': '***' if settings_obj.sendgrid_api_key else '',
                'sendgrid_password_changed_template_id': settings_obj.sendgrid_password_changed_template_id or ''
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@settings_bp.route('/api/settings/reset-defaults', methods=['POST'])
@login_required
def reset_defaults():
    """إعادة تعيين الإعدادات للقيم الافتراضية"""
    if not has_permission('settings_edit'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    try:
        settings_obj = Settings.get_settings()
        
        # إعادة تعيين القيم الافتراضية
        settings_obj.work_start = '09:00'
        settings_obj.work_end = '17:00'
        settings_obj.presence_interval_min = 30
        settings_obj.presence_grace_min = 5
        settings_obj.presence_sound_enabled = True
        settings_obj.late_arrival_threshold_min = 15
        settings_obj.early_leave_threshold_min = 15
        settings_obj.auto_checkout_enabled = False
        settings_obj.require_checkout_location = True
        settings_obj.annual_leave_days = 21
        settings_obj.sick_leave_days = 30
        settings_obj.casual_leave_days = 7
        settings_obj.carry_forward_leaves = True
        settings_obj.max_carry_forward_days = 5
        settings_obj.leave_approval_required = True
        settings_obj.min_leave_notice_days = 3
        settings_obj.payroll_currency = 'SAR'
        settings_obj.payroll_day = 1
        settings_obj.overtime_rate = 1.5
        settings_obj.weekend_overtime_rate = 2.0
        settings_obj.holiday_overtime_rate = 2.5
        settings_obj.auto_calculate_overtime = True
        settings_obj.deduct_late_from_salary = True
        settings_obj.late_deduction_rate = 0.5
        settings_obj.password_min_length = 6
        settings_obj.password_expiry_days = 90
        settings_obj.max_login_attempts = 5
        settings_obj.session_timeout_minutes = 120
        settings_obj.require_password_change_first_login = True
        settings_obj.two_factor_enabled = False
        settings_obj.records_per_page = 25
        settings_obj.performance_review_frequency_months = 6
        settings_obj.min_performance_score = 0.0
        settings_obj.max_performance_score = 5.0
        
        settings_obj.updated_at = datetime.utcnow()
        settings_obj.updated_by = current_user.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تمت إعادة تعيين الإعدادات للقيم الافتراضية بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
