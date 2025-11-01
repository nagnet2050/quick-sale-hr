"""fix_settings_table_manual

Revision ID: c3ec48cff7e1
Revises: 78fad1d3c651
Create Date: 2025-11-01 07:06:32.673592

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3ec48cff7e1'
down_revision = '78fad1d3c651'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('settings', if_exists=True)
    op.create_table('settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_name_ar', sa.String(length=128), nullable=True),
    sa.Column('company_name_en', sa.String(length=128), nullable=True),
    sa.Column('company_logo', sa.String(length=256), nullable=True),
    sa.Column('company_email', sa.String(length=128), nullable=True),
    sa.Column('company_phone', sa.String(length=32), nullable=True),
    sa.Column('company_address_ar', sa.String(length=256), nullable=True),
    sa.Column('company_address_en', sa.String(length=256), nullable=True),
    sa.Column('company_website', sa.String(length=128), nullable=True),
    sa.Column('tax_number', sa.String(length=64), nullable=True),
    sa.Column('commercial_register', sa.String(length=64), nullable=True),
    sa.Column('company_lat', sa.Float(), nullable=True),
    sa.Column('company_lng', sa.Float(), nullable=True),
    sa.Column('allowed_radius_meters', sa.Integer(), nullable=True),
    sa.Column('work_start', sa.Time(), nullable=True),
    sa.Column('work_end', sa.Time(), nullable=True),
    sa.Column('break_start', sa.Time(), nullable=True),
    sa.Column('break_end', sa.Time(), nullable=True),
    sa.Column('work_days', sa.String(length=128), nullable=True),
    sa.Column('weekend_days', sa.String(length=128), nullable=True),
    sa.Column('presence_interval_min', sa.Integer(), nullable=True),
    sa.Column('presence_grace_min', sa.Integer(), nullable=True),
    sa.Column('presence_sound_enabled', sa.Boolean(), nullable=True),
    sa.Column('late_arrival_threshold_min', sa.Integer(), nullable=True),
    sa.Column('early_leave_threshold_min', sa.Integer(), nullable=True),
    sa.Column('auto_checkout_enabled', sa.Boolean(), nullable=True),
    sa.Column('auto_checkout_time', sa.Time(), nullable=True),
    sa.Column('require_checkout_location', sa.Boolean(), nullable=True),
    sa.Column('annual_leave_days', sa.Integer(), nullable=True),
    sa.Column('sick_leave_days', sa.Integer(), nullable=True),
    sa.Column('casual_leave_days', sa.Integer(), nullable=True),
    sa.Column('carry_forward_leaves', sa.Boolean(), nullable=True),
    sa.Column('max_carry_forward_days', sa.Integer(), nullable=True),
    sa.Column('leave_approval_required', sa.Boolean(), nullable=True),
    sa.Column('min_leave_notice_days', sa.Integer(), nullable=True),
    sa.Column('payroll_currency', sa.String(length=16), nullable=True),
    sa.Column('payroll_day', sa.Integer(), nullable=True),
    sa.Column('overtime_rate', sa.Float(), nullable=True),
    sa.Column('weekend_overtime_rate', sa.Float(), nullable=True),
    sa.Column('holiday_overtime_rate', sa.Float(), nullable=True),
    sa.Column('auto_calculate_overtime', sa.Boolean(), nullable=True),
    sa.Column('deduct_late_from_salary', sa.Boolean(), nullable=True),
    sa.Column('late_deduction_rate', sa.Float(), nullable=True),
    sa.Column('email_notifications_enabled', sa.Boolean(), nullable=True),
    sa.Column('sms_notifications_enabled', sa.Boolean(), nullable=True),
    sa.Column('whatsapp_notifications_enabled', sa.Boolean(), nullable=True),
    sa.Column('notify_on_late_arrival', sa.Boolean(), nullable=True),
    sa.Column('notify_on_absence', sa.Boolean(), nullable=True),
    sa.Column('notify_on_leave_request', sa.Boolean(), nullable=True),
    sa.Column('notify_managers_on_employee_actions', sa.Boolean(), nullable=True),
    sa.Column('password_min_length', sa.Integer(), nullable=True),
    sa.Column('password_expiry_days', sa.Integer(), nullable=True),
    sa.Column('max_login_attempts', sa.Integer(), nullable=True),
    sa.Column('session_timeout_minutes', sa.Integer(), nullable=True),
    sa.Column('require_password_change_first_login', sa.Boolean(), nullable=True),
    sa.Column('two_factor_enabled', sa.Boolean(), nullable=True),
    sa.Column('language', sa.String(length=8), nullable=True),
    sa.Column('timezone', sa.String(length=64), nullable=True),
    sa.Column('date_format', sa.String(length=32), nullable=True),
    sa.Column('time_format', sa.String(length=32), nullable=True),
    sa.Column('fiscal_year_start_month', sa.Integer(), nullable=True),
    sa.Column('records_per_page', sa.Integer(), nullable=True),
    sa.Column('auto_backup_enabled', sa.Boolean(), nullable=True),
    sa.Column('backup_frequency_days', sa.Integer(), nullable=True),
    sa.Column('last_backup_date', sa.DateTime(), nullable=True),
    sa.Column('report_logo_enabled', sa.Boolean(), nullable=True),
    sa.Column('report_footer_text_ar', sa.Text(), nullable=True),
    sa.Column('report_footer_text_en', sa.Text(), nullable=True),
    sa.Column('performance_review_frequency_months', sa.Integer(), nullable=True),
    sa.Column('min_performance_score', sa.Float(), nullable=True),
    sa.Column('max_performance_score', sa.Float(), nullable=True),
    sa.Column('auto_generate_performance_alerts', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('settings')
