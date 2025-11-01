"""
نماذج WhatsApp للمحادثات والرسائل
"""
from app import db
from datetime import datetime


class WhatsAppConversation(db.Model):
    """محادثات واتساب مع العملاء"""
    __tablename__ = 'whatsapp_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_phone = db.Column(db.String(20), nullable=False, index=True)
    customer_name = db.Column(db.String(100))
    last_message = db.Column(db.Text)
    last_message_type = db.Column(db.String(20))  # text, audio, image, document
    last_message_direction = db.Column(db.String(10))  # incoming, outgoing
    unread_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active, resolved, pending
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))  # موظف HR المسؤول
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    messages = db.relationship('WhatsAppMessage', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    assigned_user = db.relationship('User', backref='whatsapp_conversations')
    
    def to_dict(self):
        """تحويل إلى قاموس للـ JSON"""
        return {
            'id': self.id,
            'customer_phone': self.customer_phone,
            'customer_name': self.customer_name,
            'last_message': self.last_message,
            'last_message_type': self.last_message_type,
            'last_message_direction': self.last_message_direction,
            'unread_count': self.unread_count,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class WhatsAppMessage(db.Model):
    """رسائل واتساب الفردية"""
    __tablename__ = 'whatsapp_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('whatsapp_conversations.id'), nullable=False)
    message_id = db.Column(db.String(255))  # ID من واتساب
    message_type = db.Column(db.String(20), nullable=False)  # text, audio, image, document, video
    message_content = db.Column(db.Text)
    
    # روابط الوسائط
    audio_url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    document_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    caption = db.Column(db.Text)  # شرح للوسائط
    
    direction = db.Column(db.String(10), nullable=False)  # incoming, outgoing
    status = db.Column(db.String(20), default='sent')  # sent, delivered, read, failed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """تحويل إلى قاموس للـ JSON"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'message_id': self.message_id,
            'message_type': self.message_type,
            'message_content': self.message_content,
            'audio_url': self.audio_url,
            'image_url': self.image_url,
            'document_url': self.document_url,
            'video_url': self.video_url,
            'caption': self.caption,
            'direction': self.direction,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WhatsAppTemplate(db.Model):
    """قوالب الردود الجاهزة"""
    __tablename__ = 'whatsapp_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    template_type = db.Column(db.String(20), default='text')  # text, audio
    category = db.Column(db.String(50))  # greeting, support, followup, resolution
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    creator = db.relationship('User', backref='whatsapp_templates')
    
    def to_dict(self):
        """تحويل إلى قاموس للـ JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'template_type': self.template_type,
            'category': self.category,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
