from flask import Blueprint, render_template, request, session
from flask_login import login_required, current_user
from app.models.contract import Contract
from app.models.employee import Employee
from app import db

contract_bp = Blueprint('contract', __name__)

@contract_bp.route('/contract', methods=['GET', 'POST'])
@login_required
def contract():
    # TODO: Contract management logic
    return render_template('contract.html', lang=session.get('lang', 'ar'))
