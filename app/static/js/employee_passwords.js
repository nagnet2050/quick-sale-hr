// employee_passwords.js - إدارة كلمات مرور الموظفين

let allEmployees = [];
const lang = document.documentElement.lang || 'ar';

// التحميل التلقائي
document.addEventListener('DOMContentLoaded', function() {
    loadEmployees();
    setupEventListeners();
});

// إعداد Event Listeners
function setupEventListeners() {
    document.getElementById('searchEmployee').addEventListener('input', filterEmployees);
    document.getElementById('filterDepartment').addEventListener('change', filterEmployees);
    document.getElementById('filterStatus').addEventListener('change', filterEmployees);
    
    // إظهار/إخفاء كلمة المرور
    document.getElementById('showPassword').addEventListener('change', function() {
        const newPass = document.getElementById('newPassword');
        const confirmPass = document.getElementById('confirmPassword');
        const type = this.checked ? 'text' : 'password';
        newPass.type = type;
        confirmPass.type = type;
    });
}

// تحميل الموظفين
async function loadEmployees() {
    try {
        const response = await fetch('/api/employees');
        const data = await response.json();
        
        allEmployees = data;
        displayEmployees(allEmployees);
        updateStatistics(allEmployees);
        loadDepartments(allEmployees);
    } catch (error) {
        console.error('Error loading employees:', error);
        showError(lang === 'ar' ? 'خطأ في تحميل البيانات' : 'Error loading data');
    }
}

// عرض الموظفين
function displayEmployees(employees) {
    const tbody = document.getElementById('employeesTableBody');
    
    if (employees.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted">
                    <i class="fas fa-inbox"></i>
                    ${lang === 'ar' ? 'لا توجد بيانات' : 'No data available'}
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = employees.map(emp => `
        <tr>
            <td>${emp.code}</td>
            <td>${emp.name}</td>
            <td>${emp.department || '-'}</td>
            <td>${emp.job_title || '-'}</td>
            <td>
                ${emp.has_password ? 
                    `<span class="badge bg-success">
                        <i class="fas fa-check"></i> ${lang === 'ar' ? 'محددة' : 'Set'}
                    </span>` : 
                    `<span class="badge bg-warning">
                        <i class="fas fa-exclamation"></i> ${lang === 'ar' ? 'غير محددة' : 'Not Set'}
                    </span>`
                }
            </td>
            <td>
                ${emp.active ? 
                    `<span class="badge bg-success">${lang === 'ar' ? 'نشط' : 'Active'}</span>` : 
                    `<span class="badge bg-secondary">${lang === 'ar' ? 'غير نشط' : 'Inactive'}</span>`
                }
            </td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="openPasswordModal(${emp.id}, '${emp.name}', '${emp.code}', ${emp.has_password})" 
                        ${!emp.active ? 'disabled' : ''}>
                    <i class="fas fa-key"></i>
                    ${emp.has_password ? 
                        (lang === 'ar' ? 'تغيير' : 'Change') : 
                        (lang === 'ar' ? 'تعيين' : 'Set')
                    }
                </button>
                ${emp.has_password ? `
                    <button class="btn btn-sm btn-danger" onclick="removePassword(${emp.id}, '${emp.name}')"
                            ${!emp.active ? 'disabled' : ''}>
                        <i class="fas fa-trash"></i>
                        ${lang === 'ar' ? 'حذف' : 'Remove'}
                    </button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

// تحديث الإحصائيات
function updateStatistics(employees) {
    const total = employees.length;
    const withPassword = employees.filter(e => e.has_password).length;
    const withoutPassword = total - withPassword;
    const active = employees.filter(e => e.active).length;
    
    document.getElementById('totalEmployees').textContent = total;
    document.getElementById('withPassword').textContent = withPassword;
    document.getElementById('withoutPassword').textContent = withoutPassword;
    document.getElementById('activeEmployees').textContent = active;
}

// تحميل الأقسام للفلتر
function loadDepartments(employees) {
    const departments = [...new Set(employees.map(e => e.department).filter(d => d))];
    const select = document.getElementById('filterDepartment');
    
    departments.forEach(dept => {
        const option = document.createElement('option');
        option.value = dept;
        option.textContent = dept;
        select.appendChild(option);
    });
}

// فلترة الموظفين
function filterEmployees() {
    const search = document.getElementById('searchEmployee').value.toLowerCase();
    const department = document.getElementById('filterDepartment').value;
    const status = document.getElementById('filterStatus').value;
    
    let filtered = allEmployees;
    
    // فلترة بالبحث
    if (search) {
        filtered = filtered.filter(e => 
            e.name.toLowerCase().includes(search) || 
            e.code.toLowerCase().includes(search)
        );
    }
    
    // فلترة بالقسم
    if (department) {
        filtered = filtered.filter(e => e.department === department);
    }
    
    // فلترة بحالة كلمة المرور
    if (status === 'with_password') {
        filtered = filtered.filter(e => e.has_password);
    } else if (status === 'without_password') {
        filtered = filtered.filter(e => !e.has_password);
    }
    
    displayEmployees(filtered);
}

// إعادة تعيين الفلاتر
function resetFilters() {
    document.getElementById('searchEmployee').value = '';
    document.getElementById('filterDepartment').value = '';
    document.getElementById('filterStatus').value = '';
    displayEmployees(allEmployees);
}

// فتح نافذة كلمة المرور
function openPasswordModal(empId, empName, empCode, hasPassword) {
    document.getElementById('employeeId').value = empId;
    document.getElementById('employeeInfo').textContent = `${empName} (${empCode})`;
    document.getElementById('modalTitle').innerHTML = hasPassword ?
        `<i class="fas fa-edit"></i> ${lang === 'ar' ? 'تغيير كلمة المرور' : 'Change Password'}` :
        `<i class="fas fa-key"></i> ${lang === 'ar' ? 'تعيين كلمة المرور' : 'Set Password'}`;
    
    // إعادة تعيين النموذج
    document.getElementById('passwordForm').reset();
    document.getElementById('employeeId').value = empId;
    
    const modal = new bootstrap.Modal(document.getElementById('passwordModal'));
    modal.show();
}

// حفظ كلمة المرور
async function savePassword() {
    const employeeId = document.getElementById('employeeId').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // التحقق من البيانات
    if (!newPassword || newPassword.length < 4) {
        showError(lang === 'ar' ? 'كلمة المرور يجب أن تكون 4 أحرف على الأقل' : 'Password must be at least 4 characters');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showError(lang === 'ar' ? 'كلمة المرور غير متطابقة' : 'Passwords do not match');
        return;
    }
    
    try {
        const response = await fetch(`/api/employee/${employeeId}/password`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password: newPassword })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess(lang === 'ar' ? 'تم حفظ كلمة المرور بنجاح' : 'Password saved successfully');
            bootstrap.Modal.getInstance(document.getElementById('passwordModal')).hide();
            loadEmployees(); // إعادة تحميل البيانات
        } else {
            showError(data.error || (lang === 'ar' ? 'حدث خطأ' : 'An error occurred'));
        }
    } catch (error) {
        console.error('Error saving password:', error);
        showError(lang === 'ar' ? 'خطأ في حفظ كلمة المرور' : 'Error saving password');
    }
}

// حذف كلمة المرور
async function removePassword(empId, empName) {
    if (!confirm(`${lang === 'ar' ? 'هل تريد حذف كلمة مرور' : 'Remove password for'} ${empName}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/employee/${empId}/password`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess(lang === 'ar' ? 'تم حذف كلمة المرور' : 'Password removed');
            loadEmployees();
        } else {
            showError(data.error || (lang === 'ar' ? 'حدث خطأ' : 'An error occurred'));
        }
    } catch (error) {
        console.error('Error removing password:', error);
        showError(lang === 'ar' ? 'خطأ في حذف كلمة المرور' : 'Error removing password');
    }
}

// عرض رسالة نجاح
function showSuccess(message) {
    // يمكن استخدام مكتبة notifications أو alert بسيط
    alert(message);
}

// عرض رسالة خطأ
function showError(message) {
    alert(message);
}
