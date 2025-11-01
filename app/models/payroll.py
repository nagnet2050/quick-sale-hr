from app import db
from datetime import datetime
from flask import current_app


class Payroll(db.Model):
    """نموذج الرواتب المتقدم"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    
    # فترة الراتب
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    month = db.Column(db.Integer)  # الشهر (1-12)
    year = db.Column(db.Integer)   # السنة
    
    # الراتب الأساسي
    basic = db.Column(db.Float, default=0.0)
    
    # البدلات المفصلة
    housing_allowance = db.Column(db.Float, default=0.0)      # بدل سكن
    transport_allowance = db.Column(db.Float, default=0.0)    # بدل مواصلات
    food_allowance = db.Column(db.Float, default=0.0)         # بدل غذاء
    phone_allowance = db.Column(db.Float, default=0.0)        # بدل هاتف
    other_allowances = db.Column(db.Float, default=0.0)       # بدلات أخرى
    allowances = db.Column(db.Float, default=0.0)             # إجمالي البدلات (للتوافق)
    
    # الإضافات
    bonus = db.Column(db.Float, default=0.0)                  # مكافآت
    commission = db.Column(db.Float, default=0.0)             # عمولات
    overtime_hours = db.Column(db.Float, default=0.0)         # ساعات إضافية
    overtime_amount = db.Column(db.Float, default=0.0)        # قيمة الساعات الإضافية
    overtime = db.Column(db.Float, default=0.0)               # للتوافق
    incentives = db.Column(db.Float, default=0.0)             # حوافز
    
    # الخصومات المفصلة
    absence_days = db.Column(db.Integer, default=0)           # أيام الغياب
    absence_deduction = db.Column(db.Float, default=0.0)      # خصم الغياب
    late_minutes = db.Column(db.Integer, default=0)           # دقائق التأخير
    late_deduction = db.Column(db.Float, default=0.0)         # خصم التأخير
    loan_deduction = db.Column(db.Float, default=0.0)         # خصم قرض/سلفة
    other_deductions = db.Column(db.Float, default=0.0)       # خصومات أخرى
    unpaid_leave_days = db.Column(db.Integer, default=0)      # أيام الإجازة غير المدفوعة
    unpaid_leave_deduction = db.Column(db.Float, default=0.0) # خصم الإجازة غير المدفوعة
    deductions = db.Column(db.Float, default=0.0)             # إجمالي الخصومات (للتوافق)
    
    # الضرائب والتأمينات
    tax = db.Column(db.Float, default=0.0)                    # الضريبة
    insurance = db.Column(db.Float, default=0.0)              # التأمينات الاجتماعية
    health_insurance = db.Column(db.Float, default=0.0)       # التأمين الصحي
    
    # الصافي والإجمالي
    gross_salary = db.Column(db.Float, default=0.0)           # الراتب الإجمالي
    total_deductions = db.Column(db.Float, default=0.0)       # إجمالي الخصومات
    net = db.Column(db.Float, default=0.0)                    # صافي الراتب
    
    # معلومات الدفع
    status = db.Column(db.String(32), default='pending')      # pending/approved/paid/cancelled
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(32))                 # cash/bank_transfer/check
    bank_name = db.Column(db.String(100))                     # اسم البنك
    account_number = db.Column(db.String(50))                 # رقم الحساب
    reference_number = db.Column(db.String(100))              # رقم مرجعي للتحويل
    
    # التتبع
    generated_by = db.Column(db.Integer)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer)
    approved_at = db.Column(db.DateTime)
    paid_by = db.Column(db.Integer)
    paid_at = db.Column(db.DateTime)
    
    # ملاحظات
    notes = db.Column(db.Text)
    is_final = db.Column(db.Boolean, default=False)           # هل تم اعتماده نهائياً

    # تتبع إعادة الحساب
    last_recalc_net_diff = db.Column(db.Float, default=0.0)   # الفرق في الصافي بعد آخر إعادة حساب
    last_recalc_at = db.Column(db.DateTime)                   # تاريخ آخر إعادة حساب

    def calculate_allowances(self):
        """حساب إجمالي البدلات"""
        detailed_total = (
            float(self.housing_allowance or 0) +
            float(self.transport_allowance or 0) +
            float(self.food_allowance or 0) +
            float(self.phone_allowance or 0) +
            float(self.other_allowances or 0)
        )
        # إذا لم تُحدد البدلات التفصيلية واعتمد الداخل على الحقل allowances مباشرةً (للتوافق مع اختبارات/واجهات قديمة)
        if detailed_total > 0:
            self.allowances = detailed_total
        else:
            self.allowances = float(self.allowances or 0)
        return self.allowances

    def calculate_deductions(self):
        """حساب إجمالي الخصومات"""
        self.deductions = (
            float(self.absence_deduction or 0) +
            float(self.late_deduction or 0) +
            float(self.loan_deduction or 0) +
            float(self.unpaid_leave_deduction or 0) +
            float(self.other_deductions or 0)
        )
        return self.deductions

    def calculate_overtime(self, hourly_rate=None, overtime_rate=1.5):
        """حساب قيمة الساعات الإضافية"""
        if not self.overtime_hours:
            self.overtime_amount = 0.0
            self.overtime = 0.0
            return 0.0
        
        if hourly_rate is None:
            # حساب الأجر بالساعة من الراتب الأساسي
            # افتراض 30 يوم و 8 ساعات يومياً = 240 ساعة
            hourly_rate = float(self.basic or 0) / 240.0
        
        self.overtime_amount = round(
            float(self.overtime_hours) * float(hourly_rate) * float(overtime_rate),
            2
        )
        self.overtime = self.overtime_amount  # للتوافق
        return self.overtime_amount

    def compute_net(self, apply_rules=True):
        """حساب صافي الراتب بالقواعد المتقدمة"""
        
        # حساب البدلات والخصومات
        self.calculate_allowances()
        self.calculate_deductions()
        
        # الراتب الأساسي
        basic = float(self.basic or 0.0)
        allowances = float(self.allowances or 0.0)
        bonus = float(self.bonus or 0.0)
        commission = float(self.commission or 0.0)
        overtime_amt = float(self.overtime_amount or 0.0)
        incentives = float(self.incentives or 0.0)
        
        # الخصومات
        deductions = float(self.deductions or 0.0)
        
        # الراتب الإجمالي
        self.gross_salary = basic + allowances + bonus + commission + overtime_amt + incentives
        
        # حساب الضرائب والتأمينات
        tax_amt = 0.0
        insurance_amt = 0.0
        health_insurance_amt = 0.0

        if apply_rules:
            cfg = current_app.config if current_app else {}
            tax_rate = cfg.get('PAYROLL_TAX_RATE', 0.10)
            insurance_rate = cfg.get('PAYROLL_INSURANCE_RATE', 0.02)
            health_insurance_rate = cfg.get('PAYROLL_HEALTH_INSURANCE_RATE', 0.01)
            exempt_limit = cfg.get('PAYROLL_TAX_EXEMPT_LIMIT', 0.0)

            # الدخل الخاضع للضريبة
            taxable_income = max(0.0, self.gross_salary - deductions)
            if taxable_income > exempt_limit:
                tax_amt = round(taxable_income * float(tax_rate), 2)

            # التأمينات (على الأساسي + البدلات فقط)
            insurance_base = basic + allowances
            insurance_amt = round(insurance_base * float(insurance_rate), 2)
            health_insurance_amt = round(insurance_base * float(health_insurance_rate), 2)

        self.tax = float(tax_amt)
        self.insurance = float(insurance_amt)
        self.health_insurance = float(health_insurance_amt)
        
        # إجمالي الخصومات
        self.total_deductions = deductions + tax_amt + insurance_amt + health_insurance_amt
        
        # صافي الراتب
        self.net = float(round(self.gross_salary - self.total_deductions, 2))

        breakdown = {
            'basic': basic,
            'housing_allowance': float(self.housing_allowance or 0),
            'transport_allowance': float(self.transport_allowance or 0),
            'food_allowance': float(self.food_allowance or 0),
            'phone_allowance': float(self.phone_allowance or 0),
            'other_allowances': float(self.other_allowances or 0),
            'total_allowances': allowances,
            'bonus': bonus,
            'commission': commission,
            'overtime_hours': float(self.overtime_hours or 0),
            'overtime_amount': overtime_amt,
            'incentives': incentives,
            'gross_salary': self.gross_salary,
            'absence_days': int(self.absence_days or 0),
            'absence_deduction': float(self.absence_deduction or 0),
            'late_minutes': int(self.late_minutes or 0),
            'late_deduction': float(self.late_deduction or 0),
            'loan_deduction': float(self.loan_deduction or 0),
            'unpaid_leave_days': int(self.unpaid_leave_days or 0),
            'unpaid_leave_deduction': float(self.unpaid_leave_deduction or 0),
            'other_deductions': float(self.other_deductions or 0),
            'total_deductions_before_tax': deductions,
            'tax': tax_amt,
            'insurance': insurance_amt,
            'health_insurance': health_insurance_amt,
            'total_deductions': self.total_deductions,
            'net_salary': self.net,
            'net': self.net
        }
        return breakdown

    def to_dict(self):
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'month': self.month,
            'year': self.year,
            'basic': self.basic,
            'gross_salary': self.gross_salary,
            'total_deductions': self.total_deductions,
            'net': self.net,
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method
        }


class EmployeeLoan(db.Model):
    """نموذج القروض والسلف"""
    __tablename__ = 'employee_loan'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    # معلومات القرض
    loan_type = db.Column(db.String(50), default='loan')  # loan/advance
    amount = db.Column(db.Float, nullable=False)          # المبلغ الإجمالي
    remaining_amount = db.Column(db.Float)                # المبلغ المتبقي
    monthly_deduction = db.Column(db.Float)               # القسط الشهري
    installments = db.Column(db.Integer)                  # عدد الأقساط
    paid_installments = db.Column(db.Integer, default=0)  # الأقساط المدفوعة
    
    # التواريخ
    issued_date = db.Column(db.Date, default=datetime.utcnow)
    start_date = db.Column(db.Date)                       # تاريخ بدء الخصم
    end_date = db.Column(db.Date)                         # تاريخ الانتهاء المتوقع
    completed_date = db.Column(db.Date)                   # تاريخ الانتهاء الفعلي
    
    # الحالة
    status = db.Column(db.String(32), default='active')   # active/completed/cancelled
    
    # ملاحظات
    reason = db.Column(db.String(200))                    # سبب القرض
    notes = db.Column(db.Text)
    
    # التتبع
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer)
    approved_at = db.Column(db.DateTime)

    def calculate_monthly_deduction(self):
        """حساب القسط الشهري"""
        if self.installments and self.installments > 0:
            self.monthly_deduction = round(float(self.amount) / float(self.installments), 2)
        return self.monthly_deduction

    def process_payment(self, amount=None):
        """معالجة دفعة من القرض"""
        if amount is None:
            amount = self.monthly_deduction
        
        if self.remaining_amount is None:
            self.remaining_amount = self.amount
        
        self.remaining_amount = max(0, float(self.remaining_amount) - float(amount))
        self.paid_installments += 1
        
        if self.remaining_amount <= 0:
            self.status = 'completed'
            self.completed_date = datetime.utcnow().date()
        
        return self.remaining_amount


class PayrollTemplate(db.Model):
    """قالب الراتب الثابت للموظف"""
    __tablename__ = 'payroll_template'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), unique=True)
    
    # الراتب الأساسي والبدلات الثابتة
    basic_salary = db.Column(db.Float, default=0.0)
    housing_allowance = db.Column(db.Float, default=0.0)
    transport_allowance = db.Column(db.Float, default=0.0)
    food_allowance = db.Column(db.Float, default=0.0)
    phone_allowance = db.Column(db.Float, default=0.0)
    other_allowances = db.Column(db.Float, default=0.0)
    
    # إعدادات الساعات الإضافية
    overtime_rate = db.Column(db.Float, default=1.5)      # معدل الساعة الإضافية
    hourly_rate = db.Column(db.Float)                     # الأجر بالساعة
    
    # الحالة
    is_active = db.Column(db.Boolean, default=True)
    effective_from = db.Column(db.Date)
    
    # التتبع
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def calculate_hourly_rate(self):
        """حساب الأجر بالساعة (30 يوم × 8 ساعات = 240 ساعة)"""
        if self.basic_salary:
            self.hourly_rate = round(float(self.basic_salary) / 240.0, 2)
        return self.hourly_rate

    def get_total_fixed_salary(self):
        """إجمالي الراتب الثابت"""
        return (
            float(self.basic_salary or 0) +
            float(self.housing_allowance or 0) +
            float(self.transport_allowance or 0) +
            float(self.food_allowance or 0) +
            float(self.phone_allowance or 0) +
            float(self.other_allowances or 0)
        )


class PayrollBatch(db.Model):
    """دفعة رواتب شهرية"""
    __tablename__ = 'payroll_batch'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # الفترة
    month = db.Column(db.Integer, nullable=False)         # 1-12
    year = db.Column(db.Integer, nullable=False)          # 2024
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    
    # الإحصائيات
    total_employees = db.Column(db.Integer, default=0)
    total_gross = db.Column(db.Float, default=0.0)
    total_deductions = db.Column(db.Float, default=0.0)
    total_net = db.Column(db.Float, default=0.0)
    
    # الحالة
    status = db.Column(db.String(32), default='draft')    # draft/approved/paid/cancelled
    
    # التتبع
    generated_by = db.Column(db.Integer)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer)
    approved_at = db.Column(db.DateTime)
    paid_by = db.Column(db.Integer)
    paid_at = db.Column(db.DateTime)
    
    # ملاحظات
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<PayrollBatch {self.year}-{self.month:02d}>'
