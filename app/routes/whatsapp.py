from flask import Blueprint, request, jsonify, render_template, current_app
from app import db
from app.models.whatsapp_models import WhatsAppMessage, WhatsAppConversation, WhatsAppTemplate
from app.models.customer_complaints import CustomerComplaint
from flask_login import current_user, login_required
from datetime import datetime
import requests
import os
from werkzeug.utils import secure_filename

whatsapp_bp = Blueprint('whatsapp', __name__)

# إعدادات واتساب (يجب وضعها في config)
# سيتم الحصول عليها داخل الدوال لتجنب مشاكل السياق

@whatsapp_bp.before_app_request
def ensure_app_context():
    """تأكد من أن التطبيق يعمل داخل سياق التطبيق"""
    if not current_app:
        raise RuntimeError("This route requires an application context.")

@whatsapp_bp.route('/api/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """التحقق من الـ webhook أو استقبال الرسائل من واتساب"""
    WHATSAPP_VERIFY_TOKEN = current_app.config.get('WHATSAPP_VERIFY_TOKEN', '')

    if request.method == 'GET':
        # التحقق من الـ webhook
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == WHATSAPP_VERIFY_TOKEN:
            return challenge, 200
        else:
            return 'Verification failed', 403

    # POST - استقبال الرسائل
    data = request.get_json()

    if not data or 'entry' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    # معالجة الرسالة
    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']

        if 'messages' in value:
            message = value['messages'][0]
            phone = message['from']
            message_type = message['type']

            # استخراج المحتوى حسب النوع
            content = ''
            if message_type == 'text':
                content = message['text']['body']
            elif message_type == 'image':
                content = message['image']['id']  # في الواقع يجب تحميل الملف
            elif message_type == 'audio':
                content = message['audio']['id']
            elif message_type == 'document':
                content = message['document']['id']

            # حفظ الرسالة
            whatsapp_msg = WhatsAppMessage(
                customer_phone=phone,
                message_type=message_type,
                message_content=content,
                direction='incoming'
            )

            # ربط بالشكوى إذا كان رقم معروف
            complaint = CustomerComplaint.query.filter_by(customer_phone=phone).first()
            if complaint:
                whatsapp_msg.complaint_id = complaint.id

            db.session.add(whatsapp_msg)
            db.session.commit()

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'error': 'Processing failed'}), 500

@whatsapp_bp.route('/api/whatsapp/send', methods=['POST'])
@login_required
def send_whatsapp_message():
    """إرسال رسالة عبر واتساب"""
    WHATSAPP_ACCESS_TOKEN = current_app.config.get('WHATSAPP_ACCESS_TOKEN', '')
    WHATSAPP_PHONE_NUMBER_ID = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID', '')

    data = request.get_json()
    phone = data.get('phone')
    message = data.get('message')
    message_type = data.get('type', 'text')

    if not phone or not message:
        return jsonify({'success': False, 'error': 'Phone and message required'}), 400

    # إعداد payload للواتساب API
    payload = {
        'messaging_product': 'whatsapp',
        'to': phone,
        'type': message_type
    }

    if message_type == 'text':
        payload['text'] = {'body': message}
    elif message_type == 'image':
        payload['image'] = {'link': message}
    elif message_type == 'audio':
        payload['audio'] = {'link': message}
    elif message_type == 'document':
        payload['document'] = {'link': message}

    # إرسال إلى واتساب API
    try:
        url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload, headers=headers)
        result = response.json()

        if response.status_code == 200:
            # حفظ في قاعدة البيانات
            whatsapp_msg = WhatsAppMessage(
                customer_phone=phone,
                message_type=message_type,
                message_content=message,
                direction='outgoing',
                sent_by=current_user.id,
                status='sent'
            )

            # ربط بالشكوى
            complaint = CustomerComplaint.query.filter_by(customer_phone=phone).first()
            if complaint:
                whatsapp_msg.complaint_id = complaint.id

            db.session.add(whatsapp_msg)
            db.session.commit()

            return jsonify({'success': True, 'message_id': result.get('messages', [{}])[0].get('id')})
        else:
            return jsonify({'success': False, 'error': result.get('error', {}).get('message')}), 400

    except Exception as e:
        print(f"Error sending message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@whatsapp_bp.route('/api/whatsapp/conversation/<phone>')
@login_required
def get_conversation(phone):
    """الحصول على محادثة عميل"""
    messages = WhatsAppMessage.query.filter_by(customer_phone=phone).order_by(WhatsAppMessage.message_date).all()

    return jsonify([{
        'id': msg.id,
        'message_type': msg.message_type,
        'message_content': msg.message_content,
        'direction': msg.direction,
        'message_date': msg.message_date.strftime('%Y-%m-%d %H:%M:%S'),
        'status': msg.status
    } for msg in messages])

@whatsapp_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """رفع الملفات للمشاركة عبر واتساب"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if file:
        filename = secure_filename(file.filename)
        # إنشاء مجلد uploads إذا لم يكن موجوداً
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        # إرجاع رابط الملف
        file_url = f"/static/uploads/{filename}"
        return jsonify({'success': True, 'url': file_url})

    return jsonify({'success': False, 'error': 'Upload failed'}), 500