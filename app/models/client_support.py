from app import db
from datetime import datetime

class ClientSupport(db.Model):
    """نموذج دعم العملاء مع إمكانية التحويل بين الأقسام"""
    __tablename__ = 'client_support'
    
    id = db.Column(db.Integer, primary_key=True)
    client_phone = db.Column(db.String(32), nullable=False)
    client_name = db.Column(db.String(128), nullable=False)
    client_email = db.Column(db.String(128))
    client_company = db.Column(db.String(128))
    
    issue = db.Column(db.Text, nullable=False)
    issue_type = db.Column(db.String(64))  # technical, sales, billing, general
    priority = db.Column(db.String(16), default='medium')  # low, medium, high, urgent
    
    # معلومات القسم والمسؤول
    department = db.Column(db.String(64), default='technical_support')  # technical_support, sales, billing, management
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))  # الموظف المسؤول
    
    # حالة التذكرة
    status = db.Column(db.String(32), default='new')  # new, assigned, in_progress, pending_transfer, transferred, resolved, closed
    resolved = db.Column(db.Boolean, default=False)
    escalated = db.Column(db.Boolean, default=False)
    
    # الرد والحل
    admin_response = db.Column(db.Text)
    resolution_notes = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    
    # التحويل بين الأقسام
    transfer_count = db.Column(db.Integer, default=0)  # عدد مرات التحويل
    last_transferred_at = db.Column(db.DateTime)
    last_transferred_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    transfer_reason = db.Column(db.Text)  # سبب آخر تحويل
    
    # البيانات الأساسية
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    transfers = db.relationship('ClientTransferHistory', backref='ticket', cascade='all, delete-orphan', lazy=True, order_by='ClientTransferHistory.created_at.desc()')
    
    def __repr__(self):
        return f'<ClientSupport {self.id} - {self.client_name} - {self.department}>'
    
    def to_dict(self):
        """تحويل التذكرة إلى قاموس"""
        return {
            'id': self.id,
            'client_phone': self.client_phone,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'client_company': self.client_company,
            'issue': self.issue,
            'issue_type': self.issue_type,
            'priority': self.priority,
            'department': self.department,
            'assigned_to': self.assigned_to,
            'status': self.status,
            'resolved': self.resolved,
            'escalated': self.escalated,
            'admin_response': self.admin_response,
            'resolution_notes': self.resolution_notes,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'transfer_count': self.transfer_count,
            'last_transferred_at': self.last_transferred_at.isoformat() if self.last_transferred_at else None,
            'transfer_reason': self.transfer_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ClientTransferHistory(db.Model):
    """سجل تاريخ تحويلات العملاء بين الأقسام"""
    __tablename__ = 'client_transfer_history'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('client_support.id'), nullable=False)
    
    # معلومات التحويل
    from_department = db.Column(db.String(64), nullable=False)
    to_department = db.Column(db.String(64), nullable=False)
    from_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    to_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # سبب التحويل
    transfer_reason = db.Column(db.Text, nullable=False)
    transfer_notes = db.Column(db.Text)
    
    # من قام بالتحويل
    transferred_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ClientTransferHistory {self.id} - Ticket {self.ticket_id} - {self.from_department} → {self.to_department}>'
    
    def to_dict(self):
        """تحويل سجل التحويل إلى قاموس"""
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'from_department': self.from_department,
            'to_department': self.to_department,
            'from_user': self.from_user,
            'to_user': self.to_user,
            'transfer_reason': self.transfer_reason,
            'transfer_notes': self.transfer_notes,
            'transferred_by': self.transferred_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
