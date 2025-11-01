// تحميل وعرض الشكاوى
function loadComplaints() {
    fetch('/api/complaints/list')
        .then(response => response.json())
        .then(complaints => {
            const tableBody = document.getElementById('complaints-table-body');
            tableBody.innerHTML = '';
            complaints.forEach(complaint => {
                const row = `
                    <tr class="status-${complaint.status}">
                        <td>${complaint.customer_phone}</td>
                        <td>${complaint.customer_name || '-'}</td>
                        <td class="issue-cell">${complaint.issue_description.substring(0, 50)}...</td>
                        <td><span class="status-badge ${complaint.status}">${getStatusText(complaint.status)}</span></td>
                        <td>${complaint.referred_to_department || '-'}</td>
                        <td>${complaint.management_response ? 'نعم' : 'لا'}</td>
                        <td>${complaint.created_at}</td>
                        <td>
                            <button class="btn btn-sm btn-chat btn-success me-1" onclick="openWhatsAppChat('${complaint.customer_phone}')">💬 واتساب</button>
                            <button class="btn btn-sm btn-update btn-primary" onclick="openUpdateModal(${complaint.id})">تحديث</button>
                        </td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
            updateStats(complaints);
        });
}

function openUpdateModal(complaintId) {
    fetch(`/api/complaints/get/${complaintId}`)
        .then(response => response.json())
        .then(complaint => {
            document.getElementById('complaint_id').value = complaint.id;
            document.getElementById('update-status').value = complaint.status;
            document.getElementById('update-modal').style.display = 'block';
        });
}

function openWhatsAppChat(phone) {
    window.open(`/whatsapp/chat/${phone}`, '_blank');
}

function updateStats(complaints) {
    const newCount = complaints.filter(c => c.status === 'new').length;
    const referredCount = complaints.filter(c => c.status === 'referred').length;
    const resolvedCount = complaints.filter(c => c.status === 'resolved').length;
    document.getElementById('new-count').textContent = newCount;
    document.getElementById('referred-count').textContent = referredCount;
    document.getElementById('resolved-count').textContent = resolvedCount;
}

function getStatusText(status) {
    const statusMap = {
        'new': 'جديدة',
        'in_progress': 'قيد المعالجة',
        'referred': 'محالة للإدارة',
        'resolved': 'تم الحل',
        'waiting_response': 'بانتظار رد الإدارة'
    };
    return statusMap[status] || status;
}

document.addEventListener('DOMContentLoaded', loadComplaints);
