"""
إعدادات WhatsApp Business API
"""
import os

class WhatsAppConfig:
    """إعدادات WhatsApp Business API"""
    
    # بيانات الاتصال
    ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', 'YOUR_ACCESS_TOKEN_HERE')
    PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', 'YOUR_PHONE_NUMBER_ID')
    BUSINESS_ACCOUNT_ID = os.environ.get('WHATSAPP_BUSINESS_ACCOUNT_ID', 'YOUR_BUSINESS_ACCOUNT_ID')
    
    # رابط API
    API_URL = 'https://graph.facebook.com/v18.0/'
    
    # Webhook
    WEBHOOK_VERIFY_TOKEN = os.environ.get('WHATSAPP_WEBHOOK_TOKEN', 'YOUR_WEBHOOK_VERIFY_TOKEN_123456')
    
    # إعدادات الملفات
    ALLOWED_AUDIO_TYPES = ['audio/mpeg', 'audio/ogg', 'audio/wav', 'audio/mp3']
    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
    ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    
    MAX_AUDIO_SIZE = 16 * 1024 * 1024  # 16MB
    MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5MB
    MAX_DOCUMENT_SIZE = 100 * 1024 * 1024  # 100MB
    
    # مجلد تخزين الوسائط
    MEDIA_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'whatsapp_media')
    
    # التحديث التلقائي (بالثواني)
    AUTO_REFRESH_INTERVAL = 5
    
    @staticmethod
    def get_api_url(endpoint=''):
        """الحصول على رابط API كامل"""
        return f"{WhatsAppConfig.API_URL}{endpoint}"
    
    @staticmethod
    def get_messages_endpoint():
        """نقطة إرسال الرسائل"""
        return f"{WhatsAppConfig.PHONE_NUMBER_ID}/messages"
    
    @staticmethod
    def get_media_endpoint(media_id=''):
        """نقطة تحميل الوسائط"""
        if media_id:
            return f"{media_id}"
        return f"{WhatsAppConfig.PHONE_NUMBER_ID}/media"
