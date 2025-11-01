/**
 * نظام إدارة تحويل العملاء بين الأقسام
 * Client Transfer Management System
 */

// الأقسام المتاحة (الدعم الفني، المبيعات، الإدارة فقط)
const DEPARTMENTS = {
    'technical_support': { 
        name_ar: 'الدعم الفني', 
        name_en: 'Technical Support', 
        color: 'info',
        icon: 'fa-headset',
        description_ar: 'قسم الدعم الفني لحل المشاكل التقنية'
    },
    'sales': { 
        name_ar: 'المبيعات', 
        name_en: 'Sales', 
        color: 'success',
        icon: 'fa-shopping-cart',
        description_ar: 'قسم المبيعات لخدمة العملاء والطلبات'
    },
    'management': { 
        name_ar: 'الإدارة', 
        name_en: 'Management', 
        color: 'primary',
        icon: 'fa-building',
        description_ar: 'الإدارة العليا للقرارات الاستراتيجية'
    }
};

// حالات التذاكر
const STATUSES = {
    'new': { name_ar: 'جديدة', name_en: 'New', color: 'info' },
    'assigned': { name_ar: 'معينة', name_en: 'Assigned', color: 'primary' },
    'in_progress': { name_ar: 'قيد المعالجة', name_en: 'In Progress', color: 'warning' },
    'transferred': { name_ar: 'محولة', name_en: 'Transferred', color: 'secondary' },
    'resolved': { name_ar: 'محلولة', name_en: 'Resolved', color: 'success' },
    'closed': { name_ar: 'مغلقة', name_en: 'Closed', color: 'dark' }
};

// الأولويات
const PRIORITIES = {
    'low': { name_ar: 'منخفضة', name_en: 'Low', color: 'secondary' },
    'medium': { name_ar: 'متوسطة', name_en: 'Medium', color: 'info' },
    'high': { name_ar: 'عالية', name_en: 'High', color: 'warning' },
    'urgent': { name_ar: 'عاجلة', name_en: 'Urgent', color: 'danger' }
};

/**
 * تحويل تذكرة بين الأقسام
 */
async function transferTicket(ticketId, transferData) {
    try {
        const response = await fetch(`/api/client-support/transfer/${ticketId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(transferData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('success', data.message || 'تم التحويل بنجاح');
            return data;
        } else {
            showNotification('error', data.error || 'فشل التحويل');
            return null;
        }
    } catch (error) {
        console.error('Transfer error:', error);
        showNotification('error', 'حدث خطأ أثناء التحويل');
        return null;
    }
}

/**
 * الحصول على تاريخ التحويلات
 */
async function getTransferHistory(ticketId) {
    try {
        const response = await fetch(`/api/client-support/transfer-history/${ticketId}`);
        const data = await response.json();
        
        if (data.success) {
            return data.transfers;
        } else {
            console.error('Failed to load transfer history:', data.error);
            return [];
        }
    } catch (error) {
        console.error('Transfer history error:', error);
        return [];
    }
}

/**
 * تعيين تذكرة لموظف
 */
async function assignTicket(ticketId, userId) {
    try {
        const response = await fetch(`/api/client-support/assign/${ticketId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('success', data.message);
            return data;
        } else {
            showNotification('error', data.error);
            return null;
        }
    } catch (error) {
        console.error('Assignment error:', error);
        showNotification('error', 'حدث خطأ أثناء التعيين');
        return null;
    }
}

/**
 * تحديث حالة التذكرة
 */
async function updateTicketStatus(ticketId, status, resolutionNotes = null) {
    try {
        const response = await fetch(`/api/client-support/update-status/${ticketId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: status,
                resolution_notes: resolutionNotes
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('success', data.message);
            return data;
        } else {
            showNotification('error', data.error);
            return null;
        }
    } catch (error) {
        console.error('Status update error:', error);
        showNotification('error', 'حدث خطأ أثناء تحديث الحالة');
        return null;
    }
}

/**
 * الحصول على موظفي قسم معين
 */
async function getDepartmentUsers(department) {
    try {
        const response = await fetch(`/api/client-support/departments/${department}`);
        const data = await response.json();
        
        if (data.success) {
            return data.users;
        } else {
            console.error('Failed to load department users:', data.error);
            return [];
        }
    } catch (error) {
        console.error('Department users error:', error);
        return [];
    }
}

/**
 * الحصول على إحصائيات الدعم
 */
async function getSupportStats() {
    try {
        const response = await fetch('/api/client-support/stats');
        const data = await response.json();
        
        if (data.success) {
            return data.stats;
        } else {
            console.error('Failed to load stats:', data.error);
            return null;
        }
    } catch (error) {
        console.error('Stats error:', error);
        return null;
    }
}

/**
 * عرض تفاصيل التذكرة
 */
function renderTicketDetails(ticket) {
    const dept = DEPARTMENTS[ticket.department] || { name_ar: ticket.department, color: 'secondary' };
    const status = STATUSES[ticket.status] || { name_ar: ticket.status, color: 'secondary' };
    const priority = PRIORITIES[ticket.priority] || { name_ar: ticket.priority, color: 'secondary' };
    
    return `
        <div class="ticket-details">
            <div class="row">
                <div class="col-md-6">
                    <p><strong>رقم التذكرة:</strong> #${ticket.id}</p>
                    <p><strong>العميل:</strong> ${ticket.client_name}</p>
                    <p><strong>الهاتف:</strong> ${ticket.client_phone}</p>
                    ${ticket.client_email ? `<p><strong>البريد:</strong> ${ticket.client_email}</p>` : ''}
                    ${ticket.client_company ? `<p><strong>الشركة:</strong> ${ticket.client_company}</p>` : ''}
                </div>
                <div class="col-md-6">
                    <p><strong>القسم:</strong> <span class="badge bg-${dept.color}">${dept.name_ar}</span></p>
                    <p><strong>الحالة:</strong> <span class="badge bg-${status.color}">${status.name_ar}</span></p>
                    <p><strong>الأولوية:</strong> <span class="badge bg-${priority.color}">${priority.name_ar}</span></p>
                    <p><strong>التحويلات:</strong> ${ticket.transfer_count || 0}</p>
                </div>
            </div>
            <div class="mt-3">
                <p><strong>المشكلة:</strong></p>
                <p>${ticket.issue}</p>
            </div>
            ${ticket.admin_response ? `
                <div class="mt-3">
                    <p><strong>رد الإدارة:</strong></p>
                    <p>${ticket.admin_response}</p>
                </div>
            ` : ''}
            ${ticket.resolution_notes ? `
                <div class="mt-3">
                    <p><strong>ملاحظات الحل:</strong></p>
                    <p>${ticket.resolution_notes}</p>
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * عرض تاريخ التحويلات
 */
function renderTransferHistory(transfers) {
    if (!transfers || transfers.length === 0) {
        return '<p class="text-center text-muted">لا يوجد تاريخ تحويلات</p>';
    }
    
    let html = '<div class="transfer-timeline">';
    
    transfers.forEach((transfer, index) => {
        const fromDept = DEPARTMENTS[transfer.from_department] || { name_ar: transfer.from_department };
        const toDept = DEPARTMENTS[transfer.to_department] || { name_ar: transfer.to_department };
        
        html += `
            <div class="transfer-item mb-3 ${index === 0 ? 'latest' : ''}">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h6 class="mb-2">
                                    <span class="badge bg-info">${fromDept.name_ar}</span>
                                    <i class="fas fa-arrow-right mx-2"></i>
                                    <span class="badge bg-success">${toDept.name_ar}</span>
                                </h6>
                                <p class="mb-1"><strong>السبب:</strong> ${transfer.transfer_reason}</p>
                                ${transfer.transfer_notes ? `<p class="mb-1"><strong>ملاحظات:</strong> ${transfer.transfer_notes}</p>` : ''}
                                <small class="text-muted">
                                    بواسطة: ${transfer.transferred_by_name}
                                    ${transfer.to_user_name ? ` | إلى: ${transfer.to_user_name}` : ''}
                                </small>
                            </div>
                            <div class="text-end">
                                <small class="text-muted">${formatDateTime(transfer.created_at)}</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

/**
 * تنسيق التاريخ والوقت
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ar-EG', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * عرض إشعار
 */
function showNotification(type, message) {
    // يمكن استخدام toast أو alert حسب التفضيل
    const alertClass = type === 'success' ? 'alert-success' : 
                      type === 'error' ? 'alert-danger' : 
                      type === 'warning' ? 'alert-warning' : 'alert-info';
    
    const notification = `
        <div class="alert ${alertClass} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" 
             style="z-index: 9999; min-width: 300px;" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', notification);
    
    // إزالة الإشعار تلقائياً بعد 5 ثوانٍ
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (alert.parentElement === document.body) {
                alert.remove();
            }
        });
    }, 5000);
}

/**
 * تصدير الإحصائيات إلى Excel
 */
async function exportStatsToExcel() {
    const stats = await getSupportStats();
    if (!stats) return;
    
    // يمكن استخدام مكتبة مثل SheetJS للتصدير
    console.log('Stats to export:', stats);
    showNotification('info', 'جاري العمل على ميزة التصدير...');
}

/**
 * طباعة تذكرة
 */
function printTicket(ticketId) {
    window.open(`/client-support/print/${ticketId}`, '_blank');
}

// تصدير الدوال للاستخدام العام
window.ClientTransfer = {
    transferTicket,
    getTransferHistory,
    assignTicket,
    updateTicketStatus,
    getDepartmentUsers,
    getSupportStats,
    renderTicketDetails,
    renderTransferHistory,
    showNotification,
    exportStatsToExcel,
    printTicket,
    DEPARTMENTS,
    STATUSES,
    PRIORITIES
};
