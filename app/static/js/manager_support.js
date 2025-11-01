/**
 * نظام الدعم الفني - واجهة المدير
 */

let allComplaints = [];
let currentComplaintId = null;

// تحميل البيانات عند فتح الصفحة
document.addEventListener('DOMContentLoaded', function() {
    loadComplaints();
    setupEventListeners();
    
    // تحديث تلقائي كل 30 ثانية
    setInterval(loadComplaints, 30000);
});

/**
 * إعداد مستمعي الأحداث
 */
function setupEventListeners() {
    // الفلاتر
    document.getElementById('filterStatus').addEventListener('change', applyFilters);
    document.getElementById('filterPriority').addEventListener('change', applyFilters);
    document.getElementById('filterCategory').addEventListener('change', applyFilters);
    document.getElementById('searchInput').addEventListener('input', applyFilters);
    
    // نموذج الرد
    document.getElementById('managerResponseForm').addEventListener('submit', submitManagerResponse);
}

/**
 * تحميل الشكاوى المحالة للمدير
 */
async function loadComplaints() {
    try {
        const response = await fetch('/api/support/manager/complaints');
        
        if (!response.ok) {
            throw new Error('فشل تحميل الشكاوى');
        }
        
        const data = await response.json();
        allComplaints = data.complaints || [];
        
        updateStatistics(data.statistics || {});
        displayComplaints(allComplaints);
        
    } catch (error) {
        console.error('خطأ:', error);
        showError('فشل تحميل الشكاوى: ' + error.message);
    }
}

/**
 * تحديث الإحصائيات
 */
function updateStatistics(stats) {
    document.getElementById('newCount').textContent = stats.sent_to_manager || 0;
    document.getElementById('reviewCount').textContent = stats.in_progress || 0;
    document.getElementById('respondedCount').textContent = stats.manager_responded || 0;
    document.getElementById('resolvedCount').textContent = stats.resolved || 0;
}

/**
 * عرض الشكاوى في الجدول
 */
function displayComplaints(complaints) {
    const tbody = document.getElementById('complaintsBody');
    
    if (!complaints || complaints.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-muted">
                    <i class="bi bi-inbox fs-1"></i>
                    <p>لا توجد شكاوى محالة حالياً</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = complaints.map(complaint => {
        const priorityBadge = getPriorityBadge(complaint.priority);
        const statusBadge = getStatusBadge(complaint.status);
        const categoryBadge = getCategoryBadge(complaint.category);
        
        return `
            <tr>
                <td><strong>#${complaint.id}</strong></td>
                <td>${escapeHtml(complaint.customer_name || 'غير محدد')}</td>
                <td><i class="bi bi-phone"></i> ${escapeHtml(complaint.customer_phone)}</td>
                <td>
                    <div class="text-truncate" style="max-width: 200px;" 
                         title="${escapeHtml(complaint.issue_description)}">
                        ${escapeHtml(complaint.issue_description.substring(0, 50))}...
                    </div>
                </td>
                <td>${priorityBadge}</td>
                <td>${categoryBadge}</td>
                <td><small>${formatDate(complaint.created_at)}</small></td>
                <td>${statusBadge}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-primary" onclick="viewComplaint(${complaint.id})" 
                                title="عرض وإضافة حل">
                            <i class="bi bi-eye"></i>
                        </button>
                        ${complaint.employee_action ? `
                            <button class="btn btn-info" onclick="viewExecution(${complaint.id})" 
                                    title="عرض التنفيذ">
                                <i class="bi bi-clipboard-check"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * تطبيق الفلاتر
 */
function applyFilters() {
    const status = document.getElementById('filterStatus').value;
    const priority = document.getElementById('filterPriority').value;
    const category = document.getElementById('filterCategory').value;
    const search = document.getElementById('searchInput').value.toLowerCase();
    
    let filtered = allComplaints;
    
    if (status) {
        filtered = filtered.filter(c => c.status === status);
    }
    
    if (priority) {
        filtered = filtered.filter(c => c.priority === priority);
    }
    
    if (category) {
        filtered = filtered.filter(c => c.category === category);
    }
    
    if (search) {
        filtered = filtered.filter(c => 
            (c.customer_name && c.customer_name.toLowerCase().includes(search)) ||
            (c.customer_phone && c.customer_phone.includes(search)) ||
            (c.issue_description && c.issue_description.toLowerCase().includes(search))
        );
    }
    
    displayComplaints(filtered);
}

/**
 * عرض تفاصيل الشكوى
 */
async function viewComplaint(complaintId) {
    currentComplaintId = complaintId;
    
    try {
        const response = await fetch(`/api/support/complaints/${complaintId}`);
        
        if (!response.ok) {
            throw new Error('فشل تحميل التفاصيل');
        }
        
        const complaint = await response.json();
        
        // ملء معلومات الشكوى
        document.getElementById('modalComplaintId').textContent = '#' + complaint.id;
        document.getElementById('modalCustomerName').textContent = complaint.customer_name || 'غير محدد';
        document.getElementById('modalCustomerPhone').textContent = complaint.customer_phone;
        document.getElementById('modalIssueDescription').textContent = complaint.issue_description;
        
        const priorityBadge = document.getElementById('modalPriority');
        priorityBadge.textContent = getPriorityText(complaint.priority);
        priorityBadge.className = 'badge ' + getPriorityClass(complaint.priority);
        
        document.getElementById('modalCategory').textContent = getCategoryText(complaint.category);
        document.getElementById('modalCreatedAt').textContent = formatDateTime(complaint.created_at);
        
        // ملء النموذج
        document.getElementById('responseComplaintId').value = complaint.id;
        document.getElementById('managerSolution').value = complaint.manager_solution || '';
        document.getElementById('managerInstructions').value = complaint.manager_instructions || '';
        document.getElementById('updatePriority').value = complaint.priority || 'medium';
        
        if (complaint.assigned_to) {
            document.getElementById('assignToEmployee').value = complaint.assigned_to;
        }
        
        // عرض الحل السابق إذا كان موجود
        if (complaint.manager_solution) {
            document.getElementById('prevSolution').textContent = complaint.manager_solution;
            document.getElementById('prevInstructions').textContent = complaint.manager_instructions || 'لا توجد';
            document.getElementById('prevResponseDate').textContent = formatDateTime(complaint.manager_response_date);
            document.getElementById('previousSolutionSection').style.display = 'block';
        } else {
            document.getElementById('previousSolutionSection').style.display = 'none';
        }
        
        // فتح النافذة
        const modal = new bootstrap.Modal(document.getElementById('complaintModal'));
        modal.show();
        
    } catch (error) {
        console.error('خطأ:', error);
        showError('فشل تحميل التفاصيل: ' + error.message);
    }
}

/**
 * إرسال رد المدير
 */
async function submitManagerResponse(e) {
    e.preventDefault();
    
    const complaintId = document.getElementById('responseComplaintId').value;
    const solution = document.getElementById('managerSolution').value.trim();
    const instructions = document.getElementById('managerInstructions').value.trim();
    const assignTo = document.getElementById('assignToEmployee').value;
    const priority = document.getElementById('updatePriority').value;
    
    if (!solution || !instructions) {
        showError('يرجى ملء جميع الحقول المطلوبة');
        return;
    }
    
    try {
        const response = await fetch(`/api/support/manager/respond/${complaintId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                manager_solution: solution,
                manager_instructions: instructions,
                assigned_to: assignTo || null,
                priority: priority
            })
        });
        
        if (!response.ok) {
            throw new Error('فشل إرسال الرد');
        }
        
        const result = await response.json();
        
        showSuccess('تم إرسال الحل بنجاح للموظف المختص');
        
        // إغلاق النافذة وتحديث القائمة
        bootstrap.Modal.getInstance(document.getElementById('complaintModal')).hide();
        loadComplaints();
        
        // إرسال إشعار للموظف
        if (assignTo) {
            notifyEmployee(assignTo, complaintId);
        }
        
    } catch (error) {
        console.error('خطأ:', error);
        showError('فشل إرسال الرد: ' + error.message);
    }
}

/**
 * عرض تفاصيل تنفيذ الموظف
 */
async function viewExecution(complaintId) {
    try {
        const response = await fetch(`/api/support/complaints/${complaintId}`);
        
        if (!response.ok) {
            throw new Error('فشل تحميل التفاصيل');
        }
        
        const complaint = await response.json();
        
        document.getElementById('execEmployeeAction').textContent = complaint.employee_action || 'لا يوجد';
        document.getElementById('execContactMethod').textContent = getContactMethodText(complaint.customer_contact_method);
        document.getElementById('execCustomerResponse').textContent = complaint.customer_response || 'لا يوجد';
        document.getElementById('execResolutionDetails').textContent = complaint.resolution_details || 'لا يوجد';
        document.getElementById('execResolvedAt').textContent = formatDateTime(complaint.resolved_at);
        
        const modal = new bootstrap.Modal(document.getElementById('executionModal'));
        modal.show();
        
    } catch (error) {
        console.error('خطأ:', error);
        showError('فشل تحميل التفاصيل: ' + error.message);
    }
}

/**
 * تحديث البيانات
 */
function refreshComplaints() {
    loadComplaints();
    showSuccess('تم تحديث البيانات');
}

/**
 * إرسال إشعار للموظف
 */
async function notifyEmployee(employeeId, complaintId) {
    try {
        await fetch('/api/notifications/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: employeeId,
                type: 'manager_solution',
                message: `تم إرسال حل من المدير للشكوى #${complaintId}`,
                link: `/support/employee?complaint=${complaintId}`
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

function getStatusBadge(status) {
    const badges = {
        'sent_to_manager': '<span class="badge bg-warning">محولة للمدير</span>',
        'manager_responded': '<span class="badge bg-primary">تم الرد</span>',
        'in_progress': '<span class="badge bg-info">قيد التنفيذ</span>',
        'resolved': '<span class="badge bg-success">محلولة</span>',
        'closed': '<span class="badge bg-dark">مغلقة</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">جديد</span>';
}

function getCategoryBadge(category) {
    const badges = {
        'billing': '<span class="badge bg-success">فواتير</span>',
        'technical': '<span class="badge bg-danger">دعم فني</span>',
        'training': '<span class="badge bg-info">تدريب</span>',
        'other': '<span class="badge bg-secondary">أخرى</span>'
    };
    return badges[category] || badges['other'];
}

function getPriorityText(priority) {
    const texts = {
        'urgent': 'عاجل',
        'high': 'عالي',
        'medium': 'متوسط',
        'low': 'منخفض'
    };
    return texts[priority] || 'متوسط';
}

function getPriorityClass(priority) {
    const classes = {
        'urgent': 'bg-danger',
        'high': 'bg-warning',
        'medium': 'bg-info',
        'low': 'bg-secondary'
    };
    return classes[priority] || 'bg-info';
}

function getCategoryText(category) {
    const texts = {
        'billing': 'فواتير',
        'technical': 'دعم فني',
        'training': 'تدريب',
        'other': 'أخرى'
    };
    return texts[category] || 'أخرى';
}

function getContactMethodText(method) {
    const texts = {
        'phone': 'اتصال هاتفي',
        'whatsapp': 'واتساب',
        'email': 'بريد إلكتروني',
        'visit': 'زيارة ميدانية'
    };
    return texts[method] || 'غير محدد';
}

function formatDate(dateString) {
    if (!dateString) return 'غير محدد';
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-EG');
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
    // يمكنك استخدام مكتبة Toast أو Alert
    alert('✓ ' + message);
}

function showError(message) {
    alert('✗ ' + message);
}
