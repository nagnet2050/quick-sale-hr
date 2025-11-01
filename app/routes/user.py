from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.models.user import User
from app import db
from app.permissions import has_permission

user_bp = Blueprint('user', __name__)

# تم حذف route القديم /manage_roles
# يرجى استخدام /admin/permissions بدلاً منه
