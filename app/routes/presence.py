from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app.models.presence import EmployeePresence
from app.models.employee import Employee
from app import db
from app.permissions import has_permission
from datetime import datetime, timedelta

presence_bp = Blueprint('presence', __name__)

# Cache for last update times to prevent too frequent updates
_last_updates = {}
UPDATE_INTERVAL = timedelta(minutes=30)  # Only allow updates every 30 minutes

@presence_bp.route('/api/presence/update', methods=['POST'])
@login_required
def update_presence():
    data = request.get_json() or {}
    employee_id = data.get('employee_id') or current_user.id
    
    # Rate limiting: check if last update was recent
    cache_key = f"presence_{employee_id}"
    now = datetime.utcnow()
    
    if cache_key in _last_updates:
        last_update = _last_updates[cache_key]
        if now - last_update < UPDATE_INTERVAL:
            # Too soon, return success without updating database
            return jsonify({'status': 'success', 'cached': True})
    
    # Update cache
    _last_updates[cache_key] = now
    
    # Update database
    ip_address = request.remote_addr
    presence = EmployeePresence.query.filter_by(employee_id=employee_id).first()
    
    try:
        if not presence:
            presence = EmployeePresence(
                employee_id=employee_id, 
                status='online', 
                last_activity=now, 
                session_start=now, 
                ip_address=ip_address
            )
            db.session.add(presence)
        else:
            presence.last_activity = now
            presence.status = 'online'
            presence.ip_address = ip_address
        
        db.session.commit()
        return jsonify({'status': 'success', 'updated': True})
    except Exception as e:
        db.session.rollback()
        # Return success anyway to avoid client-side errors
        return jsonify({'status': 'success', 'error': str(e)})

@presence_bp.route('/api/presence/status/<int:employee_id>', methods=['GET'])
@login_required
def get_employee_status(employee_id):
    presence = EmployeePresence.query.filter_by(employee_id=employee_id).first()
    if not presence:
        return jsonify({'status': 'offline', 'last_activity': None})
    return jsonify({'status': presence.status, 'last_activity': presence.last_activity})

@presence_bp.route('/api/presence/dashboard', methods=['GET'])
@login_required
def get_presence_dashboard():
    # Only admin/manager can view dashboard
    if not has_permission(['admin', 'manager']):
        return jsonify({'error': 'unauthorized'}), 403
    employees = Employee.query.all()
    dashboard = []
    for emp in employees:
        presence = EmployeePresence.query.filter_by(employee_id=emp.id).first()
        dashboard.append({
            'name': emp.name,
            'department': emp.department,
            'status': presence.status if presence else 'offline',
            'last_activity': presence.last_activity if presence else None,
            'session_start': presence.session_start if presence else None
        })
    return jsonify(dashboard)
