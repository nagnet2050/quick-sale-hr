"""
مسارات WhatsApp Business API
"""
from flask import Blueprint, request, jsonify, render_template, session, current_app
from flask_login import login_required, current_user
from app import db
from app.models.whatsapp_models import WhatsAppConversation, WhatsAppMessage, WhatsAppTemplate
from app.whatsapp_config import WhatsAppConfig
from app.permissions import has_permission
from datetime import datetime
import requests
import os
import json
from werkzeug.utils import secure_filename

whatsapp_bp = Blueprint('whatsapp', __name__)


# ==================== Webhook ====================

@whatsapp_bp.route('/api/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """
    Webhook لاستقبال الرسائل من WhatsApp Business API
    GET: للتحقق من الـ webhook (verification)
    POST: لاستقبال الرسائل
    """
    
    if request.method == 'GET':
        # التحقق من الـ webhook
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == WhatsAppConfig.WEBHOOK_VERIFY_TOKEN:
            current_app.logger.info('Webhook verified successfully')
            return challenge, 200
        else:
            current_app.logger.warning('Webhook verification failed')
            return 'Verification failed', 403
    
    # POST - استقبال الرسائل
    try:
        data = request.get_json()
        
        if not data or 'entry' not in data:
            return jsonify({'error': 'Invalid data'}), 400
        
        # معالجة كل إدخال
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                
                # التحقق من وجود رسائل
                if 'messages' in value:
                    for message in value['messages']:
                        process_incoming_message(message, value)
                
                # معالجة حالة الرسالة (delivered, read, etc.)
                if 'statuses' in value:
                    for status in value['statuses']:
                        update_message_status(status)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        current_app.logger.error(f'Webhook error: {str(e)}')
        return jsonify({'error': str(e)}), 500


def process_incoming_message(message_data, value):
    """معالجة الرسالة الواردة"""
    try:
        customer_phone = message_data.get('from')
        message_id = message_data.get('id')
        message_type = message_data.get('type')
        timestamp = datetime.fromtimestamp(int(message_data.get('timestamp', 0)))
        
        # الحصول على المحادثة أو إنشاء واحدة جديدة
        conversation = WhatsAppConversation.query.filter_by(
            customer_phone=customer_phone
        ).first()
        
        if not conversation:
            # إنشاء محادثة جديدة
            customer_name = value.get('contacts', [{}])[0].get('profile', {}).get('name', customer_phone)
            conversation = WhatsAppConversation(
                customer_phone=customer_phone,
                customer_name=customer_name,
                status='active'
            )
            db.session.add(conversation)
            db.session.flush()
        
        # استخراج محتوى الرسالة
        message_content = ''
        media_url = None
        caption = None
        
        if message_type == 'text':
            message_content = message_data['text']['body']
        
        elif message_type == 'audio':
            audio_id = message_data['audio']['id']
            media_url = download_whatsapp_media(audio_id)
            message_content = 'رسالة صوتية'
        
        elif message_type == 'image':
            image_id = message_data['image']['id']
            media_url = download_whatsapp_media(image_id)
            caption = message_data['image'].get('caption', '')
            message_content = caption or 'صورة'
        
        elif message_type == 'document':
            doc_id = message_data['document']['id']
            media_url = download_whatsapp_media(doc_id)
            caption = message_data['document'].get('caption', '')
            message_content = caption or 'مستند'
        
        elif message_type == 'video':
            video_id = message_data['video']['id']
            media_url = download_whatsapp_media(video_id)
            caption = message_data['video'].get('caption', '')
            message_content = caption or 'فيديو'
        
        # حفظ الرسالة
        new_message = WhatsAppMessage(
            conversation_id=conversation.id,
            message_id=message_id,
            message_type=message_type,
            message_content=message_content,
            audio_url=media_url if message_type == 'audio' else None,
            image_url=media_url if message_type == 'image' else None,
            document_url=media_url if message_type == 'document' else None,
            video_url=media_url if message_type == 'video' else None,
            caption=caption,
            direction='incoming',
            timestamp=timestamp
        )
        db.session.add(new_message)
        
        # تحديث المحادثة
        conversation.last_message = message_content
        conversation.last_message_type = message_type
        conversation.last_message_direction = 'incoming'
        conversation.unread_count += 1
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f'Message saved: {message_id} from {customer_phone}')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error processing message: {str(e)}')


def download_whatsapp_media(media_id):
    """تحميل الوسائط من WhatsApp"""
    try:
        # الحصول على رابط الوسائط
        url = WhatsAppConfig.get_api_url(media_id)
        headers = {
            'Authorization': f'Bearer {WhatsAppConfig.ACCESS_TOKEN}'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            media_info = response.json()
            media_url = media_info.get('url')
            mime_type = media_info.get('mime_type')
            
            if media_url:
                # تحميل الملف
                media_response = requests.get(media_url, headers=headers)
                
                if media_response.status_code == 200:
                    # حفظ الملف
                    filename = f"{media_id}_{datetime.now().timestamp()}.{get_extension_from_mime(mime_type)}"
                    filepath = os.path.join(WhatsAppConfig.MEDIA_UPLOAD_FOLDER, filename)
                    
                    # التأكد من وجود المجلد
                    os.makedirs(WhatsAppConfig.MEDIA_UPLOAD_FOLDER, exist_ok=True)
                    
                    with open(filepath, 'wb') as f:
                        f.write(media_response.content)
                    
                    # إرجاع الرابط النسبي
                    return f'/static/whatsapp_media/{filename}'
        
        return None
        
    except Exception as e:
        current_app.logger.error(f'Error downloading media: {str(e)}')
        return None


def get_extension_from_mime(mime_type):
    """الحصول على الامتداد من نوع MIME"""
    extensions = {
        'audio/mpeg': 'mp3',
        'audio/ogg': 'ogg',
        'audio/wav': 'wav',
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'video/mp4': 'mp4',
        'application/pdf': 'pdf',
    }
    return extensions.get(mime_type, 'bin')


def update_message_status(status_data):
    """تحديث حالة الرسالة (delivered, read, etc.)"""
    try:
        message_id = status_data.get('id')
        status = status_data.get('status')
        
        message = WhatsAppMessage.query.filter_by(message_id=message_id).first()
        if message:
            message.status = status
            db.session.commit()
            
    except Exception as e:
        current_app.logger.error(f'Error updating status: {str(e)}')


# ==================== API للإرسال ====================

@whatsapp_bp.route('/api/whatsapp/send-message', methods=['POST'])
@login_required
def send_whatsapp_message():
    """إرسال رسالة نصية"""
    if not has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        message = data.get('message')
        
        if not conversation_id or not message:
            return jsonify({'error': 'Missing parameters'}), 400
        
        conversation = WhatsAppConversation.query.get_or_404(conversation_id)
        
        # إرسال الرسالة
        result = send_text_message(conversation.customer_phone, message)
        
        if result['success']:
            # حفظ في قاعدة البيانات
            new_message = WhatsAppMessage(
                conversation_id=conversation_id,
                message_id=result['message_id'],
                message_type='text',
                message_content=message,
                direction='outgoing',
                status='sent'
            )
            db.session.add(new_message)
            
            # تحديث المحادثة
            conversation.last_message = message
            conversation.last_message_type = 'text'
            conversation.last_message_direction = 'outgoing'
            conversation.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({'success': True, 'message': new_message.to_dict()})
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@whatsapp_bp.route('/api/whatsapp/send-audio', methods=['POST'])
@login_required
def send_whatsapp_audio():
    """إرسال رسالة صوتية"""
    if not has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        conversation_id = request.form.get('conversation_id')
        audio_file = request.files.get('audio')
        
        if not conversation_id or not audio_file:
            return jsonify({'error': 'Missing parameters'}), 400
        
        conversation = WhatsAppConversation.query.get_or_404(conversation_id)
        
        # حفظ الملف الصوتي
        filename = secure_filename(f"{datetime.now().timestamp()}_{audio_file.filename}")
        filepath = os.path.join(WhatsAppConfig.MEDIA_UPLOAD_FOLDER, filename)
        
        os.makedirs(WhatsAppConfig.MEDIA_UPLOAD_FOLDER, exist_ok=True)
        audio_file.save(filepath)
        
        # رفع إلى WhatsApp
        audio_url = upload_media_to_whatsapp(filepath, 'audio')
        
        if audio_url:
            # إرسال الرسالة الصوتية
            result = send_audio_message(conversation.customer_phone, audio_url)
            
            if result['success']:
                # حفظ في قاعدة البيانات
                new_message = WhatsAppMessage(
                    conversation_id=conversation_id,
                    message_id=result['message_id'],
                    message_type='audio',
                    message_content='رسالة صوتية',
                    audio_url=f'/static/whatsapp_media/{filename}',
                    direction='outgoing',
                    status='sent'
                )
                db.session.add(new_message)
                
                # تحديث المحادثة
                conversation.last_message = 'رسالة صوتية'
                conversation.last_message_type = 'audio'
                conversation.last_message_direction = 'outgoing'
                conversation.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                return jsonify({'success': True, 'message': new_message.to_dict()})
            else:
                return jsonify({'success': False, 'error': result['error']}), 500
        else:
            return jsonify({'success': False, 'error': 'Failed to upload media'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== وظائف الإرسال ====================

def send_text_message(phone, message):
    """إرسال رسالة نصية"""
    try:
        url = WhatsAppConfig.get_api_url(WhatsAppConfig.get_messages_endpoint())
        headers = {
            'Authorization': f'Bearer {WhatsAppConfig.ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': phone,
            'type': 'text',
            'text': {'body': message}
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'message_id': result['messages'][0]['id']
            }
        else:
            return {
                'success': False,
                'error': response.text
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_audio_message(phone, audio_url):
    """إرسال رسالة صوتية"""
    try:
        url = WhatsAppConfig.get_api_url(WhatsAppConfig.get_messages_endpoint())
        headers = {
            'Authorization': f'Bearer {WhatsAppConfig.ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': phone,
            'type': 'audio',
            'audio': {'link': audio_url}
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'message_id': result['messages'][0]['id']
            }
        else:
            return {
                'success': False,
                'error': response.text
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}


def upload_media_to_whatsapp(filepath, media_type):
    """رفع وسائط إلى WhatsApp"""
    try:
        url = WhatsAppConfig.get_api_url(WhatsAppConfig.get_media_endpoint())
        headers = {
            'Authorization': f'Bearer {WhatsAppConfig.ACCESS_TOKEN}'
        }
        
        with open(filepath, 'rb') as f:
            files = {
                'file': (os.path.basename(filepath), f, f'audio/mpeg'),
                'messaging_product': (None, 'whatsapp'),
                'type': (None, media_type)
            }
            
            response = requests.post(url, files=files, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('id')
        
        return None
        
    except Exception as e:
        current_app.logger.error(f'Error uploading media: {str(e)}')
        return None


# ==================== API للعرض ====================

@whatsapp_bp.route('/api/whatsapp/conversations', methods=['GET'])
@login_required
def get_conversations():
    """الحصول على قائمة المحادثات"""
    if not has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        conversations = WhatsAppConversation.query.order_by(
            WhatsAppConversation.updated_at.desc()
        ).all()
        
        return jsonify([conv.to_dict() for conv in conversations])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@whatsapp_bp.route('/api/whatsapp/messages/<int:conversation_id>', methods=['GET'])
@login_required
def get_messages(conversation_id):
    """الحصول على رسائل محادثة محددة"""
    if not has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        conversation = WhatsAppConversation.query.get_or_404(conversation_id)
        
        messages = WhatsAppMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(WhatsAppMessage.timestamp.asc()).all()
        
        # تحديث عداد غير المقروءة
        conversation.unread_count = 0
        db.session.commit()
        
        return jsonify([msg.to_dict() for msg in messages])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@whatsapp_bp.route('/api/whatsapp/templates', methods=['GET'])
@login_required
def get_templates():
    """الحصول على قوالب الردود الجاهزة"""
    try:
        templates = WhatsAppTemplate.query.all()
        return jsonify([template.to_dict() for template in templates])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== واجهة HTML ====================

@whatsapp_bp.route('/whatsapp/chat')
@login_required
def whatsapp_chat():
    """صفحة واجهة الدردشة"""
    if not has_permission(['admin', 'manager']):
        return render_template('unauthorized.html')
    
    return render_template('whatsapp_chat.html', lang=session.get('lang', 'ar'))
