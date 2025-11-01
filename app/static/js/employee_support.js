/**
 * نظام الدعم الفني - واجهة الموظف
 */

let currentComplaintId = null;
let allTasks = {
    new: [],
    progress: [],
    completed: []
};

// تحميل البيانات عند فتح الصفحة
document.addEventListener('DOMContentLoaded', function() {
    loadEmployeeTasks();
    setupEventListeners();
    
    // تحديث تلقائي كل 20 ثانية
    setInterval(loadEmployeeTasks, 20000);
    
    // التحقق من وجود شكوى محددة في الرابط
    const urlParams = new URLSearchParams(window.location.search);
    const complaintId = urlParams.get('complaint');
    if (complaintId) {
        setTimeout(() => viewSolution(parseInt(complaintId)), 500);
    }
});

/**
 * إعداد مستمعي الأحداث
 */
function setupEventListeners() {
    document.getElementById('executionForm').addEventListener('submit', submitExecution);
}

/**
 * تحميل مهام الموظف
 */
async function loadEmployeeTasks() {
    try {
        const response = await fetch('/api/support/employee/tasks');
        
        if (!response.ok) {
            throw new Error('فشل تحميل المهام');
        }
        
        const data = await response.json();
        
        allTasks.new = data.new || [];
        allTasks.progress = data.progress || [];
        allTasks.completed = data.completed || [];
        
        updateStatistics();
        displayTasks();
        
    } catch (error) {
        console.error('خطأ:', error);
        showError('فشل تحميل المهام: ' + error.message);
    }
}

/**
 * تحديث الإحصائيات
 */
function updateStatistics() {
    document.getElementById('newTasksCount').textContent = allTasks.new.length;
    document.getElementById('inProgressCount').textContent = allTasks.progress.length;
    document.getElementById('completedCount').textContent = allTasks.completed.length;
    
    document.getElementById('newBadge').textContent = allTasks.new.length;
    document.getElementById('progressBadge').textContent = allTasks.progress.length;
}

/**
 * عرض المهام
 */
function displayTasks() {
    displayNewTasks();
    displayProgressTasks();
    displayCompletedTasks();
}

/**
 * عرض المهام الجديدة
 */
function displayNewTasks() {
    const container = document.getElementById('newTasksList');
    
    if (allTasks.new.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> لا توجد مهام جديدة حالياً
            </div>
        `;
        return;
    }
    
    container.innerHTML = allTasks.new.map(task => `
        <div class="list-group-item list-group-item-action">
            <div class="d-flex w-100 justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <h5 class="mb-2">
                        <span class="badge bg-primary">#${task.id}</span>
                        ${escapeHtml(task.customer_name || 'عميل')}
                        ${getPriorityBadge(task.priority)}
                    </h5>
                    <p class="mb-2"><i class="bi bi-phone"></i> ${escapeHtml(task.customer_phone)}</p>
                    <p class="mb-2"><strong>المشكلة:</strong> ${escapeHtml(task.issue_description.substring(0, 100))}...</p>
                    <p class="mb-1 text-success">
                        <i class="bi bi-lightbulb"></i> <strong>حل المدير متاح</strong>
                    </p>
                    <small class="text-muted">
                        <i class="bi bi-clock"></i> وردت منذ ${getTimeAgo(task.manager_response_date)}
                    </small>
                </div>
                <div class="ms-3">
                    <button class="btn btn-primary" onclick="viewSolution(${task.id})">
                        <i class="bi bi-eye"></i> عرض الحل والتنفيذ
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * عرض المهام قيد التنفيذ
 */
function displayProgressTasks() {
    const container = document.getElementById('progressTasksList');
    
    if (allTasks.progress.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> لا توجد مهام قيد التنفيذ
            </div>
        `;
        return;
    }
    
    container.innerHTML = allTasks.progress.map(task => `
        <div class="list-group-item">
            <div class="d-flex w-100 justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <h5 class="mb-2">
                        <span class="badge bg-warning">#${task.id}</span>
                        ${escapeHtml(task.customer_name || 'عميل')}
                    </h5>
                    <p class="mb-2"><i class="bi bi-phone"></i> ${escapeHtml(task.customer_phone)}</p>
                    ${task.employee_action ? `
                        <div class="alert alert-warning mb-2">
                            <strong>آخر إجراء:</strong> ${escapeHtml(task.employee_action.substring(0, 100))}...
                        </div>
                    ` : ''}
                    <small class="text-muted">
                        <i class="bi bi-clock"></i> بدأت منذ ${getTimeAgo(task.updated_at)}
                    </small>
                </div>
                <div class="ms-3">
                    <button class="btn btn-success" onclick="viewSolution(${task.id})">
                        <i class="bi bi-check-circle"></i> إكمال التنفيذ
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * عرض المهام المنجزة
 */
function displayCompletedTasks() {
    const container = document.getElementById('completedTasksList');
    
    if (allTasks.completed.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> لا توجد مهام منجزة
            </div>
        `;
        return;
    }
    
    container.innerHTML = allTasks.completed.map(task => `
        <div class="list-group-item">
            <div class="d-flex w-100 justify-content-between">
                <div>
                    <h6>
                        <span class="badge bg-success">#${task.id}</span>
                        ${escapeHtml(task.customer_name || 'عميل')}
                    </h6>
                    <p class="mb-1"><i class="bi bi-check-circle text-success"></i> ${escapeHtml(task.resolution_details)}</p>
                    <small class="text-muted">
                        <i class="bi bi-calendar-check"></i> تم الحل في ${formatDateTime(task.resolved_at)}
                    </small>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * عرض حل المدير
 */
async function viewSolution(complaintId) {
    currentComplaintId = complaintId;
    
    try {
        const response = await fetch(`/api/support/complaints/${complaintId}`);
        
        if (!response.ok) {
            throw new Error('فشل تحميل التفاصيل');
        }
        
        const complaint = await response.json();
        
        // ملء معلومات المشكلة
        document.getElementById('solComplaintId').textContent = '#' + complaint.id;
        document.getElementById('solCustomerName').textContent = complaint.customer_name || 'غير محدد';
        document.getElementById('solCustomerPhone').textContent = complaint.customer_phone;
        
        const prioritySpan = document.getElementById('solPriority');
        prioritySpan.innerHTML = getPriorityBadge(complaint.priority);
        
        document.getElementById('solIssueDesc').textContent = complaint.issue_description;
        
        // ملء حل المدير
        document.getElementById('solManagerSolution').textContent = complaint.manager_solution || 'لا يوجد حل بعد';
        document.getElementById('solManagerInstructions').textContent = complaint.manager_instructions || 'لا توجد تعليمات';
        document.getElementById('solResponseDate').textContent = formatDateTime(complaint.manager_response_date);
        
        // ملء النموذج بالبيانات السابقة إذا كانت موجودة
        document.getElementById('execComplaintId').value = complaint.id;
        document.getElementById('employeeAction').value = complaint.employee_action || '';
        document.getElementById('contactMethod').value = complaint.customer_contact_method || '';
        document.getElementById('customerResponse').value = complaint.customer_response || '';
        document.getElementById('resolutionDetails').value = complaint.resolution_details || '';
        
        // فتح النافذة
        const modal = new bootstrap.Modal(document.getElementById('solutionModal'));
        modal.show();
        
    } catch (error) {
        console.error('خطأ:', error);
        showError('فشل تحميل التفاصيل: ' + error.message);
    }
}

/**
 * تعليم كـ "قيد التنفيذ"
 */
async function markInProgress() {
    const complaintId = document.getElementById('execComplaintId').value;
    const employeeAction = document.getElementById('employeeAction').value.trim();
    
    if (!employeeAction) {
        showError('يرجى كتابة الإجراء المتخذ');
        return;
    }
    
    try {
        const response = await fetch(`/api/support/employee/mark-progress/${complaintId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                employee_action: employeeAction,
                customer_contact_method: document.getElementById('contactMethod').value,
                customer_response: document.getElementById('customerResponse').value
            })
        });
        
        if (!response.ok) {
            throw new Error('فشل حفظ التقدم');
        }
        
        showSuccess('تم حفظ التقدم بنجاح');
        loadEmployeeTasks();
        
    } catch (error) {
        console.error('خطأ:', error);
        showError('فشل حفظ التقدم: ' + error.message);
    }
}

/**
 * إرسال تقرير التنفيذ النهائي
 */
async function submitExecution(e) {
    e.preventDefault();
    
    const complaintId = document.getElementById('execComplaintId').value;
    const employeeAction = document.getElementById('employeeAction').value.trim();
    const contactMethod = document.getElementById('contactMethod').value;
    const customerResponse = document.getElementById('customerResponse').value.trim();
    const resolutionDetails = document.getElementById('resolutionDetails').value.trim();
    const confirmed = document.getElementById('confirmResolved').checked;
    
    if (!employeeAction || !contactMethod || !customerResponse || !resolutionDetails) {
        showError('يرجى ملء جميع الحقول المطلوبة');
        return;
    }
    
    if (!confirmed) {
        showError('يرجى تأكيد حل المشكلة');
        return;
    }
    
    try {
        const response = await fetch(`/api/support/employee/resolve/${complaintId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                employee_action: employeeAction,
                customer_contact_method: contactMethod,
                customer_response: customerResponse,
                resolution_details: resolutionDetails
            })
        });
        
        if (!response.ok) {
            throw new Error('فشل تسجيل الحل');
        }
        
        const result = await response.json();
        
        showSuccess('✓ تم تسجيل الحل النهائي بنجاح!');
        
        // إغلاق النافذة وتحديث القائمة
        bootstrap.Modal.getInstance(document.getElementById('solutionModal')).hide();
        
        // إعادة تعيين النموذج
        document.getElementById('executionForm').reset();
        
        // تحديث القوائم
        loadEmployeeTasks();
        
        // إرسال إشعار للمدير
        notifyManager(complaintId);
        
    } catch (error) {
        console.error('خطأ:', error);
        showError('فشل تسجيل الحل: ' + error.message);
    }
}

/**
 * إرسال إشعار للمدير
 */
async function notifyManager(complaintId) {
    try {
        await fetch('/api/notifications/send-to-manager', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: 'complaint_resolved',
                complaint_id: complaintId,
                message: `تم حل الشكوى #${complaintId} من قبل الموظف`
            })
        });
    } catch (error) {
        console.error('فشل إرسال الإشعار:', error);
    }
}

// ================== دوال مساعدة ==================

function getPriorityBadge(priority) {
    const badges = {
        'urgent': '<span class="badge bg-danger"><i class="bi bi-exclamation-triangle-fill"></i> عاجل</span>',
        'high': '<span class="badge bg-warning"><i class="bi bi-exclamation-circle"></i> عالي</span>',
        'medium': '<span class="badge bg-info">متوسط</span>',
        'low': '<span class="badge bg-secondary">منخفض</span>'
    };
    return badges[priority] || badges['medium'];
}

function getTimeAgo(dateString) {
    if (!dateString) return 'غير معروف';
    
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 60) return `${diffMins} دقيقة`;
    if (diffHours < 24) return `${diffHours} ساعة`;
    return `${diffDays} يوم`;
}

function formatDateTime(dateString) {
    if (!dateString) return 'غير محدد';
    const date = new Date(dateString);
    return date.toLocaleString('ar-EG');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showSuccess(message) {
    // يمكن استبداله بـ Toast notification
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 end-0 m-3';
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        <i class="bi bi-check-circle"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}

function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 end-0 m-3';
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}
