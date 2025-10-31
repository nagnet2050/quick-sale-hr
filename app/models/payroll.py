from app import db
from datetime import datetime
from flask import current_app


class Payroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    basic = db.Column(db.Float, default=0.0)
    allowances = db.Column(db.Float, default=0.0)
    bonus = db.Column(db.Float, default=0.0)
    overtime = db.Column(db.Float, default=0.0)  # monetary amount for overtime
    deductions = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    insurance = db.Column(db.Float, default=0.0)
    net = db.Column(db.Float, default=0.0)
    generated_by = db.Column(db.Integer, nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), default='unpaid')  # paid/unpaid

    def compute_net(self, apply_rules=True):
        """Compute net pay applying configurable rules from app config.

        Returns a dict breakdown and sets self.net, self.tax, self.insurance accordingly.
        """
        basic = float(self.basic or 0.0)
        allowances = float(self.allowances or 0.0)
        bonus = float(self.bonus or 0.0)
        overtime_amt = float(self.overtime or 0.0)
        deductions = float(self.deductions or 0.0)

        tax_amt = 0.0
        insurance_amt = 0.0

        if apply_rules:
            cfg = current_app.config if current_app else {}
            tax_rate = cfg.get('PAYROLL_TAX_RATE', 0.10)
            insurance_rate = cfg.get('PAYROLL_INSURANCE_RATE', 0.02)
            exempt_limit = cfg.get('PAYROLL_TAX_EXEMPT_LIMIT', 0.0)

            taxable_income = max(0.0, basic + allowances + bonus + overtime_amt - deductions)
            if taxable_income > exempt_limit:
                tax_amt = round(taxable_income * float(tax_rate), 2)
            else:
                tax_amt = 0.0

            insurance_amt = round((basic + allowances) * float(insurance_rate), 2)

        gross = basic + allowances + bonus + overtime_amt
        net = gross - deductions - tax_amt - insurance_amt

        self.tax = float(tax_amt)
        self.insurance = float(insurance_amt)
        self.net = float(round(net, 2))

        breakdown = {
            'basic': basic,
            'allowances': allowances,
            'bonus': bonus,
            'overtime': overtime_amt,
            'gross': gross,
            'deductions': deductions,
            'tax': tax_amt,
            'insurance': insurance_amt,
            'net': self.net
        }
        return breakdown
