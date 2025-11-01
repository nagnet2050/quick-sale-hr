// Payroll Management JavaScript
let payrollData = [];
let employeesData = [];
const lang = document.documentElement.lang || 'ar';

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeYearFilters();
    loadEmployees();
    loadPayrolls();
    setInterval(loadPayrolls, 60000); // Refresh every minute
});

// Initialize year filters with current year and ±2 years
function initializeYearFilters() {
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1;
    
    ['filterYear', 'year', 'batchYear'].forEach(id => {
        const select = document.getElementById(id);
        if (select) {
            select.innerHTML = id === 'filterYear' ? '<option value="">الكل</option>' : '';
            for (let year = currentYear - 2; year <= currentYear + 2; year++) {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                if (year === currentYear) option.selected = true;
                select.appendChild(option);
            }
        }
    });
    
    // Set current month
    ['month', 'batchMonth'].forEach(id => {
        const select = document.getElementById(id);
        if (select) select.value = currentMonth;
    });
}

// Load employees list
async function loadEmployees() {
    try {
        const response = await fetch('/api/employees');
        if (!response.ok) throw new Error('Failed to load employees');
        
        employeesData = await response.json();
        const select = document.getElementById('employeeId');
        
        select.innerHTML = '<option value="">' + (lang === 'en' ? 'Select Employee' : 'اختر الموظف') + '</option>';
        employeesData.forEach(emp => {
            const option = document.createElement('option');
            option.value = emp.id;
            option.textContent = `${emp.full_name} (${emp.employee_code || emp.id})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading employees:', error);
        showNotification(lang === 'en' ? 'Failed to load employees' : 'فشل تحميل الموظفين', 'error');
    }
}

// Load payrolls with filters
async function loadPayrolls() {
    try {
        const month = document.getElementById('filterMonth').value;
        const year = document.getElementById('filterYear').value;
        const status = document.getElementById('filterStatus').value;
        const search = document.getElementById('searchEmployee').value;
        
        const params = new URLSearchParams();
        if (month) params.append('month', month);
        if (year) params.append('year', year);
        if (status) params.append('status', status);
        if (search) params.append('search', search);
        
        const response = await fetch(`/api/payroll?${params}`);
        if (!response.ok) throw new Error('Failed to load payrolls');
        
        payrollData = await response.json();
        displayPayrolls();
        updateStatistics();
    } catch (error) {
        console.error('Error loading payrolls:', error);
        document.getElementById('payrollTableBody').innerHTML = `
            <tr><td colspan="10" class="text-center text-danger">
                ${lang === 'en' ? 'Error loading payrolls' : 'خطأ في تحميل الرواتب'}
            </td></tr>
        `;
    }
}

// Display payrolls in table
function displayPayrolls() {
    const tbody = document.getElementById('payrollTableBody');
    
    if (payrollData.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="10" class="text-center text-muted">
                ${lang === 'en' ? 'No payroll records found' : 'لا توجد سجلات رواتب'}
            </td></tr>
        `;
        return;
    }
    
    tbody.innerHTML = payrollData.map(payroll => `
        <tr>
            <td>${payroll.id}</td>
            <td>
                <div class="fw-bold">${getEmployeeName(payroll.employee_id)}</div>
                <small class="text-muted">${getEmployeeCode(payroll.employee_id)}</small>
            </td>
            <td>${formatPeriod(payroll.month, payroll.year)}</td>
            <td>${formatCurrency(payroll.basic)}</td>
            <td>${formatCurrency(payroll.allowances || 0)}</td>
            <td class="fw-bold text-success">${formatCurrency(payroll.gross_salary)}</td>
            <td class="text-danger">${formatCurrency(payroll.total_deductions)}</td>
            <td class="fw-bold text-primary">${formatCurrency(payroll.net)}</td>
            <td>${getStatusBadge(payroll.status)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-info" onclick="viewPayroll(${payroll.id})" title="${lang === 'en' ? 'View' : 'عرض'}">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${payroll.status === 'pending' ? `
                        <button class="btn btn-warning" onclick="editPayroll(${payroll.id})" title="${lang === 'en' ? 'Edit' : 'تعديل'}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-success" onclick="approvePayroll(${payroll.id})" title="${lang === 'en' ? 'Approve' : 'اعتماد'}">
                            <i class="fas fa-check"></i>
                        </button>
                    ` : ''}
                    ${payroll.status === 'approved' ? `
                        <button class="btn btn-success" onclick="markAsPaid(${payroll.id})" title="${lang === 'en' ? 'Mark as Paid' : 'تحديد كمدفوع'}">
                            <i class="fas fa-money-bill-wave"></i>
                        </button>
                    ` : ''}
                    ${payroll.status === 'paid' ? `
                        <button class="btn btn-primary" onclick="downloadPayslip(${payroll.id})" title="${lang === 'en' ? 'Download Payslip' : 'تحميل الإيصال'}">
                            <i class="fas fa-file-pdf"></i>
                        </button>
                    ` : ''}
                    ${payroll.status !== 'paid' ? `
                        <button class="btn btn-danger" onclick="deletePayroll(${payroll.id})" title="${lang === 'en' ? 'Delete' : 'حذف'}">
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

// Update statistics cards
function updateStatistics() {
    const total = payrollData.length;
    const totalGross = payrollData.reduce((sum, p) => sum + (parseFloat(p.gross_salary) || 0), 0);
    const totalDed = payrollData.reduce((sum, p) => sum + (parseFloat(p.total_deductions) || 0), 0);
    const totalNet = payrollData.reduce((sum, p) => sum + (parseFloat(p.net) || 0), 0);
    
    document.getElementById('totalCount').textContent = total;
    document.getElementById('totalGross').textContent = formatCurrency(totalGross);
    document.getElementById('totalDeductions').textContent = formatCurrency(totalDed);
    document.getElementById('totalNet').textContent = formatCurrency(totalNet);
}

// Show add payroll modal
function showAddPayroll() {
    document.getElementById('payrollModalTitle').textContent = lang === 'en' ? 'Add Payroll' : 'إضافة راتب';
    document.getElementById('payrollForm').reset();
    document.getElementById('payrollId').value = '';
    
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1;
    document.getElementById('year').value = currentYear;
    document.getElementById('month').value = currentMonth;
    
    calculateNet();
    new bootstrap.Modal(document.getElementById('payrollModal')).show();
}

// Load employee template
async function loadEmployeeTemplate() {
    const employeeId = document.getElementById('employeeId').value;
    if (!employeeId) return;
    
    try {
        const response = await fetch(`/api/payroll/template/${employeeId}`);
        if (!response.ok) return;
        
        const template = await response.json();
        if (template) {
            document.getElementById('basic').value = template.basic_salary || 0;
            document.getElementById('housingAllowance').value = template.housing_allowance || 0;
            document.getElementById('transportAllowance').value = template.transport_allowance || 0;
            document.getElementById('foodAllowance').value = template.food_allowance || 0;
            document.getElementById('phoneAllowance').value = template.phone_allowance || 0;
            document.getElementById('otherAllowances').value = template.other_allowances || 0;
            document.getElementById('overtimeRate').value = template.overtime_rate || 1.5;
            calculateNet();
        }
    } catch (error) {
        console.error('Error loading template:', error);
    }
}

// Calculate net salary
function calculateNet() {
    const basic = parseFloat(document.getElementById('basic').value) || 0;
    const housing = parseFloat(document.getElementById('housingAllowance').value) || 0;
    const transport = parseFloat(document.getElementById('transportAllowance').value) || 0;
    const food = parseFloat(document.getElementById('foodAllowance').value) || 0;
    const phone = parseFloat(document.getElementById('phoneAllowance').value) || 0;
    const other = parseFloat(document.getElementById('otherAllowances').value) || 0;
    const bonus = parseFloat(document.getElementById('bonus').value) || 0;
    const commission = parseFloat(document.getElementById('commission').value) || 0;
    const incentives = parseFloat(document.getElementById('incentives').value) || 0;
    
    // Overtime calculation
    const overtimeHours = parseFloat(document.getElementById('overtimeHours').value) || 0;
    const overtimeRate = parseFloat(document.getElementById('overtimeRate').value) || 1.5;
    const hourlyRate = basic / 240; // 30 days × 8 hours
    const overtimeAmount = overtimeHours * hourlyRate * overtimeRate;
    document.getElementById('overtimeAmount').value = overtimeAmount.toFixed(2);
    
    // Deductions
    const absenceDays = parseInt(document.getElementById('absenceDays').value) || 0;
    const lateMinutes = parseInt(document.getElementById('lateMinutes').value) || 0;
    const dailyRate = basic / 30;
    const absenceDeduction = absenceDays * dailyRate;
    const lateDeduction = (lateMinutes / 60) * hourlyRate;
    
    document.getElementById('absenceDeduction').value = absenceDeduction.toFixed(2);
    document.getElementById('lateDeduction').value = lateDeduction.toFixed(2);
    
    const loanDed = parseFloat(document.getElementById('loanDeduction').value) || 0;
    const otherDed = parseFloat(document.getElementById('otherDeductions').value) || 0;
    
    // Gross salary
    const gross = basic + housing + transport + food + phone + other + bonus + commission + incentives + overtimeAmount;
    
    // Total deductions before tax
    const totalDedBeforeTax = absenceDeduction + lateDeduction + loanDed + otherDed;
    
    // Tax (10% on taxable income)
    const taxableIncome = Math.max(0, gross - totalDedBeforeTax);
    const tax = taxableIncome * 0.10;
    
    // Insurance (2% on basic + allowances)
    const insurance = (basic + housing + transport + food + phone + other) * 0.02;
    
    // Health insurance (1%)
    const healthInsurance = (basic + housing + transport + food + phone + other) * 0.01;
    
    // Total deductions
    const totalDeductions = totalDedBeforeTax + tax + insurance + healthInsurance;
    
    // Net salary
    const net = gross - totalDeductions;
    
    // Update display
    document.getElementById('grossSalary').textContent = formatCurrency(gross);
    document.getElementById('totalDeductionsCalc').textContent = formatCurrency(totalDeductions);
    document.getElementById('taxAmount').textContent = formatCurrency(tax);
    document.getElementById('netSalary').textContent = formatCurrency(net);
}

// Save payroll
async function savePayroll() {
    const payrollId = document.getElementById('payrollId').value;
    const employeeId = document.getElementById('employeeId').value;
    
    if (!employeeId) {
        showNotification(lang === 'en' ? 'Please select an employee' : 'يرجى اختيار الموظف', 'error');
        return;
    }
    
    const data = {
        employee_id: parseInt(employeeId),
        month: parseInt(document.getElementById('month').value),
        year: parseInt(document.getElementById('year').value),
        basic: parseFloat(document.getElementById('basic').value) || 0,
        housing_allowance: parseFloat(document.getElementById('housingAllowance').value) || 0,
        transport_allowance: parseFloat(document.getElementById('transportAllowance').value) || 0,
        food_allowance: parseFloat(document.getElementById('foodAllowance').value) || 0,
        phone_allowance: parseFloat(document.getElementById('phoneAllowance').value) || 0,
        other_allowances: parseFloat(document.getElementById('otherAllowances').value) || 0,
        bonus: parseFloat(document.getElementById('bonus').value) || 0,
        commission: parseFloat(document.getElementById('commission').value) || 0,
        incentives: parseFloat(document.getElementById('incentives').value) || 0,
        overtime_hours: parseFloat(document.getElementById('overtimeHours').value) || 0,
        overtime_amount: parseFloat(document.getElementById('overtimeAmount').value) || 0,
        absence_days: parseInt(document.getElementById('absenceDays').value) || 0,
        absence_deduction: parseFloat(document.getElementById('absenceDeduction').value) || 0,
        late_minutes: parseInt(document.getElementById('lateMinutes').value) || 0,
        late_deduction: parseFloat(document.getElementById('lateDeduction').value) || 0,
        loan_deduction: parseFloat(document.getElementById('loanDeduction').value) || 0,
        other_deductions: parseFloat(document.getElementById('otherDeductions').value) || 0,
        status: document.getElementById('status').value,
        notes: document.getElementById('notes').value
    };
    
    try {
        const url = payrollId ? `/api/payroll/${payrollId}` : '/api/payroll';
        const method = payrollId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save payroll');
        }
        
        showNotification(
            lang === 'en' ? 'Payroll saved successfully' : 'تم حفظ الراتب بنجاح',
            'success'
        );
        
        bootstrap.Modal.getInstance(document.getElementById('payrollModal')).hide();
        loadPayrolls();
    } catch (error) {
        console.error('Error saving payroll:', error);
        showNotification(error.message, 'error');
    }
}

// Edit payroll
async function editPayroll(id) {
    try {
        const response = await fetch(`/api/payroll/${id}`);
        if (!response.ok) throw new Error('Failed to load payroll');
        
        const payroll = await response.json();
        
        document.getElementById('payrollModalTitle').textContent = lang === 'en' ? 'Edit Payroll' : 'تعديل الراتب';
        document.getElementById('payrollId').value = payroll.id;
        document.getElementById('employeeId').value = payroll.employee_id;
        document.getElementById('month').value = payroll.month;
        document.getElementById('year').value = payroll.year;
        document.getElementById('basic').value = payroll.basic || 0;
        document.getElementById('housingAllowance').value = payroll.housing_allowance || 0;
        document.getElementById('transportAllowance').value = payroll.transport_allowance || 0;
        document.getElementById('foodAllowance').value = payroll.food_allowance || 0;
        document.getElementById('phoneAllowance').value = payroll.phone_allowance || 0;
        document.getElementById('otherAllowances').value = payroll.other_allowances || 0;
        document.getElementById('bonus').value = payroll.bonus || 0;
        document.getElementById('commission').value = payroll.commission || 0;
        document.getElementById('incentives').value = payroll.incentives || 0;
        document.getElementById('overtimeHours').value = payroll.overtime_hours || 0;
        document.getElementById('overtimeAmount').value = payroll.overtime_amount || 0;
        document.getElementById('absenceDays').value = payroll.absence_days || 0;
        document.getElementById('absenceDeduction').value = payroll.absence_deduction || 0;
        document.getElementById('lateMinutes').value = payroll.late_minutes || 0;
        document.getElementById('lateDeduction').value = payroll.late_deduction || 0;
        document.getElementById('loanDeduction').value = payroll.loan_deduction || 0;
        document.getElementById('otherDeductions').value = payroll.other_deductions || 0;
        document.getElementById('status').value = payroll.status;
        document.getElementById('notes').value = payroll.notes || '';
        
        calculateNet();
        new bootstrap.Modal(document.getElementById('payrollModal')).show();
    } catch (error) {
        console.error('Error loading payroll:', error);
        showNotification(lang === 'en' ? 'Failed to load payroll' : 'فشل تحميل الراتب', 'error');
    }
}

// View payroll details
async function viewPayroll(id) {
    try {
        const response = await fetch(`/api/payroll/${id}`);
        if (!response.ok) throw new Error('Failed to load payroll');
        
        const p = await response.json();
        const empName = getEmployeeName(p.employee_id);
        
        document.getElementById('viewModalBody').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>${lang === 'en' ? 'Employee Information' : 'معلومات الموظف'}</h6>
                    <table class="table table-sm">
                        <tr><th>${lang === 'en' ? 'Name' : 'الاسم'}:</th><td>${empName}</td></tr>
                        <tr><th>${lang === 'en' ? 'Period' : 'الفترة'}:</th><td>${formatPeriod(p.month, p.year)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Status' : 'الحالة'}:</th><td>${getStatusBadge(p.status)}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>${lang === 'en' ? 'Salary Components' : 'مكونات الراتب'}</h6>
                    <table class="table table-sm">
                        <tr><th>${lang === 'en' ? 'Basic' : 'الأساسي'}:</th><td>${formatCurrency(p.basic)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Housing' : 'السكن'}:</th><td>${formatCurrency(p.housing_allowance || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Transport' : 'المواصلات'}:</th><td>${formatCurrency(p.transport_allowance || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Food' : 'الغذاء'}:</th><td>${formatCurrency(p.food_allowance || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Phone' : 'الهاتف'}:</th><td>${formatCurrency(p.phone_allowance || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Other' : 'أخرى'}:</th><td>${formatCurrency(p.other_allowances || 0)}</td></tr>
                    </table>
                </div>
            </div>
            <hr>
            <div class="row">
                <div class="col-md-6">
                    <h6>${lang === 'en' ? 'Additions' : 'الإضافات'}</h6>
                    <table class="table table-sm">
                        <tr><th>${lang === 'en' ? 'Bonus' : 'المكافآت'}:</th><td>${formatCurrency(p.bonus || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Commission' : 'العمولات'}:</th><td>${formatCurrency(p.commission || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Incentives' : 'الحوافز'}:</th><td>${formatCurrency(p.incentives || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Overtime' : 'ساعات إضافية'}:</th><td>${p.overtime_hours || 0} ${lang === 'en' ? 'hrs' : 'ساعة'} = ${formatCurrency(p.overtime_amount || 0)}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>${lang === 'en' ? 'Deductions' : 'الخصومات'}</h6>
                    <table class="table table-sm">
                        <tr><th>${lang === 'en' ? 'Absence' : 'الغياب'}:</th><td>${p.absence_days || 0} ${lang === 'en' ? 'days' : 'يوم'} = ${formatCurrency(p.absence_deduction || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Late' : 'التأخير'}:</th><td>${p.late_minutes || 0} ${lang === 'en' ? 'min' : 'دقيقة'} = ${formatCurrency(p.late_deduction || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Loan' : 'قرض'}:</th><td>${formatCurrency(p.loan_deduction || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Other' : 'أخرى'}:</th><td>${formatCurrency(p.other_deductions || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Tax' : 'الضريبة'}:</th><td>${formatCurrency(p.tax || 0)}</td></tr>
                        <tr><th>${lang === 'en' ? 'Insurance' : 'التأمينات'}:</th><td>${formatCurrency(p.insurance || 0)}</td></tr>
                    </table>
                </div>
            </div>
            <hr>
            <div class="row bg-light p-3">
                <div class="col-md-4">
                    <strong>${lang === 'en' ? 'Gross Salary' : 'الراتب الإجمالي'}:</strong>
                    <h4 class="text-success">${formatCurrency(p.gross_salary)}</h4>
                </div>
                <div class="col-md-4">
                    <strong>${lang === 'en' ? 'Total Deductions' : 'إجمالي الخصومات'}:</strong>
                    <h4 class="text-danger">${formatCurrency(p.total_deductions)}</h4>
                </div>
                <div class="col-md-4">
                    <strong>${lang === 'en' ? 'Net Salary' : 'صافي الراتب'}:</strong>
                    <h4 class="text-primary">${formatCurrency(p.net)}</h4>
                </div>
            </div>
            ${p.notes ? `<hr><p><strong>${lang === 'en' ? 'Notes' : 'ملاحظات'}:</strong> ${p.notes}</p>` : ''}
        `;
        
        new bootstrap.Modal(document.getElementById('viewModal')).show();
    } catch (error) {
        console.error('Error viewing payroll:', error);
        showNotification(lang === 'en' ? 'Failed to load payroll' : 'فشل تحميل الراتب', 'error');
    }
}

// Approve payroll
async function approvePayroll(id) {
    if (!confirm(lang === 'en' ? 'Approve this payroll?' : 'اعتماد هذا الراتب؟')) return;
    
    try {
        const response = await fetch(`/api/payroll/${id}/approve`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to approve payroll');
        
        showNotification(
            lang === 'en' ? 'Payroll approved successfully' : 'تم اعتماد الراتب بنجاح',
            'success'
        );
        loadPayrolls();
    } catch (error) {
        console.error('Error approving payroll:', error);
        showNotification(lang === 'en' ? 'Failed to approve payroll' : 'فشل اعتماد الراتب', 'error');
    }
}

// Mark as paid
async function markAsPaid(id) {
    if (!confirm(lang === 'en' ? 'Mark this payroll as paid?' : 'تحديد هذا الراتب كمدفوع؟')) return;
    
    try {
        const response = await fetch(`/api/payroll/${id}/pay`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to mark as paid');
        
        showNotification(
            lang === 'en' ? 'Payroll marked as paid' : 'تم تحديد الراتب كمدفوع',
            'success'
        );
        loadPayrolls();
    } catch (error) {
        console.error('Error marking as paid:', error);
        showNotification(lang === 'en' ? 'Failed to mark as paid' : 'فشل تحديد الراتب كمدفوع', 'error');
    }
}

// Delete payroll
async function deletePayroll(id) {
    if (!confirm(lang === 'en' ? 'Delete this payroll?' : 'حذف هذا الراتب؟')) return;
    
    try {
        const response = await fetch(`/api/payroll/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete payroll');
        
        showNotification(
            lang === 'en' ? 'Payroll deleted successfully' : 'تم حذف الراتب بنجاح',
            'success'
        );
        loadPayrolls();
    } catch (error) {
        console.error('Error deleting payroll:', error);
        showNotification(lang === 'en' ? 'Failed to delete payroll' : 'فشل حذف الراتب', 'error');
    }
}

// Download payslip PDF
function downloadPayslip(id) {
    window.open(`/api/payroll/${id}/payslip`, '_blank');
}

// Show generate batch modal
function showGenerateBatch() {
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1;
    document.getElementById('batchYear').value = currentYear;
    document.getElementById('batchMonth').value = currentMonth;
    new bootstrap.Modal(document.getElementById('batchModal')).show();
}

// Generate monthly batch
async function generateBatch() {
    const month = parseInt(document.getElementById('batchMonth').value);
    const year = parseInt(document.getElementById('batchYear').value);
    
    if (!confirm(`${lang === 'en' ? 'Generate payroll for' : 'إنشاء كشف الرواتب لـ'} ${formatPeriod(month, year)}?`)) return;
    
    try {
        const response = await fetch('/api/payroll/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ month, year })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to generate batch');
        }
        
        const result = await response.json();
        showNotification(
            `${lang === 'en' ? 'Generated payroll for' : 'تم إنشاء رواتب لـ'} ${result.count} ${lang === 'en' ? 'employees' : 'موظف'}`,
            'success'
        );
        
        bootstrap.Modal.getInstance(document.getElementById('batchModal')).hide();
        
        // Set filters to show the new batch
        document.getElementById('filterMonth').value = month;
        document.getElementById('filterYear').value = year;
        loadPayrolls();
    } catch (error) {
        console.error('Error generating batch:', error);
        showNotification(error.message, 'error');
    }
}

// Reset filters
function resetFilters() {
    document.getElementById('filterMonth').value = '';
    document.getElementById('filterYear').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('searchEmployee').value = '';
    loadPayrolls();
}

// Helper functions
function getEmployeeName(id) {
    const emp = employeesData.find(e => e.id === id);
    return emp ? emp.full_name : id;
}

function getEmployeeCode(id) {
    const emp = employeesData.find(e => e.id === id);
    return emp ? (emp.employee_code || emp.id) : id;
}

function formatCurrency(amount) {
    return new Intl.NumberFormat(lang === 'en' ? 'en-US' : 'ar-SA', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount || 0);
}

function formatPeriod(month, year) {
    const months = {
        en: ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        ar: ['', 'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
    };
    return `${months[lang][month]} ${year}`;
}

function getStatusBadge(status) {
    const badges = {
        pending: { text: lang === 'en' ? 'Pending' : 'قيد الانتظار', class: 'warning' },
        approved: { text: lang === 'en' ? 'Approved' : 'معتمد', class: 'success' },
        paid: { text: lang === 'en' ? 'Paid' : 'مدفوع', class: 'primary' },
        cancelled: { text: lang === 'en' ? 'Cancelled' : 'ملغي', class: 'danger' }
    };
    const badge = badges[status] || { text: status, class: 'secondary' };
    return `<span class="badge bg-${badge.class}">${badge.text}</span>`;
}

function showNotification(message, type = 'info') {
    const alertClass = {
        success: 'alert-success',
        error: 'alert-danger',
        warning: 'alert-warning',
        info: 'alert-info'
    }[type] || 'alert-info';
    
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}
