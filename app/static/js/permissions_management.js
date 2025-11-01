// permissions_management.js - نظام إدارة الصلاحيات المتقدم

const lang = document.documentElement.lang || 'ar';
let allPermissions = [];
let allRoles = [];
// Permissions filters state
let selectedModules = new Set();
let permissionSearchTerm = '';

// Pagination variables
let currentPageUserRoles = 1;
let currentPageUsers = 1;
const perPage = 50;

// التحميل التلقائي
document.addEventListener('DOMContentLoaded', function() {
    loadRoles();
    loadPermissions();
    loadUserRoles();
    loadUsers(); // لتعبئة dropdown في modal
    
    // Add search event listeners
    setupSearchListeners();
});

// =============== Search Setup ===============

function setupSearchListeners() {
    // User Roles search
    let userRolesSearchTimeout;
    const userRolesSearchInput = document.getElementById('searchUserRoles');
    if (userRolesSearchInput) {
        userRolesSearchInput.addEventListener('input', function() {
            clearTimeout(userRolesSearchTimeout);
            userRolesSearchTimeout = setTimeout(() => {
                currentPageUserRoles = 1;
                loadUserRoles();
            }, 300);
        });
    }

    // Permissions search
    let permSearchTimeout;
    const permSearchInput = document.getElementById('searchPermissions');
    if (permSearchInput) {
        permSearchInput.addEventListener('input', function() {
            clearTimeout(permSearchTimeout);
            permSearchTimeout = setTimeout(() => {
                permissionSearchTerm = (permSearchInput.value || '').trim().toLowerCase();
                filterPermissions();
            }, 250);
        });
    }

    // Reset filters
    const resetBtn = document.getElementById('resetPermFilters');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            selectedModules.clear();
            permissionSearchTerm = '';
            const permSearchInputEl = document.getElementById('searchPermissions');
            if (permSearchInputEl) permSearchInputEl.value = '';
            const selectEl = document.getElementById('filterModule');
            if (selectEl) selectEl.value = '';
            renderModuleChips([...new Set(allPermissions.map(p => p.module))]);
            displayPermissions(allPermissions);
        });
    }
}

// =============== Roles Management ===============

async function loadRoles() {
    try {
        const response = await fetch('/api/roles');
        const data = await response.json();
        allRoles = data;
        displayRoles(data);
    } catch (error) {
        console.error('Error loading roles:', error);
        showError(lang === 'ar' ? 'خطأ في تحميل الأدوار' : 'Error loading roles');
    }
}

function displayRoles(roles) {
    const tbody = document.getElementById('rolesTableBody');
    
    if (roles.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    <i class="fas fa-inbox"></i>
                    ${lang === 'ar' ? 'لا توجد أدوار' : 'No roles available'}
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = roles.map(role => `
        <tr>
            <td><strong>${role.name}</strong></td>
            <td>${role.display_name_ar || '-'}</td>
            <td>${role.description || '-'}</td>
            <td><span class="badge bg-info">${role.permissions_count || 0}</span></td>
            <td>
                ${role.is_active ? 
                    `<span class="badge bg-success">${lang === 'ar' ? 'نشط' : 'Active'}</span>` : 
                    `<span class="badge bg-secondary">${lang === 'ar' ? 'معطل' : 'Inactive'}</span>`
                }
            </td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editRole(${role.id})">
                    <i class="fas fa-edit"></i> ${lang === 'ar' ? 'تعديل' : 'Edit'}
                </button>
                <button class="btn btn-sm btn-info" onclick="viewRolePermissions(${role.id})">
                    <i class="fas fa-key"></i> ${lang === 'ar' ? 'الصلاحيات' : 'Permissions'}
                </button>
                ${role.name !== 'admin' ? `
                    <button class="btn btn-sm btn-danger" onclick="deleteRole(${role.id})">
                        <i class="fas fa-trash"></i> ${lang === 'ar' ? 'حذف' : 'Delete'}
                    </button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

async function openRoleModal(roleId = null) {
    document.getElementById('roleId').value = roleId || '';
    document.getElementById('roleModalTitle').textContent = roleId ?
        (lang === 'ar' ? 'تعديل دور' : 'Edit Role') :
        (lang === 'ar' ? 'إضافة دور جديد' : 'Add New Role');
    
    // Load permissions checkboxes
    await loadPermissionsCheckboxes();
    
    if (roleId) {
        // Load role data
        const response = await fetch(`/api/roles/${roleId}`);
        const role = await response.json();
        
        document.getElementById('roleName').value = role.name;
        document.getElementById('roleNameAr').value = role.display_name_ar || '';
        document.getElementById('roleNameEn').value = role.display_name_en || '';
        document.getElementById('roleDescription').value = role.description || '';
        const isActiveEl = document.getElementById('roleIsActive');
        if (isActiveEl) isActiveEl.checked = !!role.is_active;
        
        // Check assigned permissions
        role.permissions.forEach(permId => {
            const checkbox = document.querySelector(`input[name="perm_${permId}"]`);
            if (checkbox) checkbox.checked = true;
        });
    } else {
        document.getElementById('roleForm').reset();
        const isActiveEl = document.getElementById('roleIsActive');
        if (isActiveEl) isActiveEl.checked = true;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('roleModal'));
    modal.show();
}

async function loadPermissionsCheckboxes() {
    const container = document.getElementById('permissionsCheckboxes');
    
    try {
        if (allPermissions.length === 0) {
            const response = await fetch('/api/permissions');
            allPermissions = await response.json();
        }
        
        // Group by module
        const grouped = {};
        allPermissions.forEach(perm => {
            if (!grouped[perm.module]) {
                grouped[perm.module] = [];
            }
            grouped[perm.module].push(perm);
        });
        
        container.innerHTML = Object.keys(grouped).map(module => `
            <div class="mb-3">
                <h6 class="text-primary"><i class="fas fa-folder"></i> ${module}</h6>
                <div class="row">
                    ${grouped[module].map(perm => `
                        <div class="col-md-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" 
                                       name="perm_${perm.id}" id="perm_${perm.id}">
                                <label class="form-check-label small" for="perm_${perm.id}">
                                    ${lang === 'ar' ? perm.display_name_ar : perm.display_name_en}
                                    <br><small class="text-muted">${perm.action}</small>
                                </label>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading permissions:', error);
        container.innerHTML = `<div class="alert alert-danger">${lang === 'ar' ? 'خطأ في تحميل الصلاحيات' : 'Error loading permissions'}</div>`;
    }
}

async function saveRole() {
    const roleId = document.getElementById('roleId').value;
    const name = document.getElementById('roleName').value.trim();
    const nameAr = document.getElementById('roleNameAr').value.trim();
    const nameEn = document.getElementById('roleNameEn').value.trim();
    const description = document.getElementById('roleDescription').value.trim();
    const isActive = document.getElementById('roleIsActive') ? document.getElementById('roleIsActive').checked : true;
    
    if (!name || !nameAr || !nameEn) {
        showError(lang === 'ar' ? 'يرجى ملء جميع الحقول المطلوبة' : 'Please fill all required fields');
        return;
    }
    
    // Get selected permissions
    const permissions = [];
    document.querySelectorAll('#permissionsCheckboxes input[type="checkbox"]:checked').forEach(checkbox => {
        const permId = checkbox.name.replace('perm_', '');
        permissions.push(parseInt(permId));
    });
    
    const data = {
        name,
        display_name_ar: nameAr,
        display_name_en: nameEn,
        description,
        is_active: isActive,
        permissions
    };
    
    try {
        const url = roleId ? `/api/roles/${roleId}` : '/api/roles';
        const method = roleId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(lang === 'ar' ? 'تم الحفظ بنجاح' : 'Saved successfully');
            bootstrap.Modal.getInstance(document.getElementById('roleModal')).hide();
            loadRoles();
        } else {
            showError(result.error || (lang === 'ar' ? 'حدث خطأ' : 'An error occurred'));
        }
    } catch (error) {
        console.error('Error saving role:', error);
        showError(lang === 'ar' ? 'خطأ في الحفظ' : 'Error saving');
    }
}

async function editRole(roleId) {
    await openRoleModal(roleId);
}

async function deleteRole(roleId) {
    if (!confirm(lang === 'ar' ? 'هل تريد حذف هذا الدور؟' : 'Delete this role?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/roles/${roleId}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(lang === 'ar' ? 'تم الحذف بنجاح' : 'Deleted successfully');
            loadRoles();
        } else {
            showError(result.error || (lang === 'ar' ? 'حدث خطأ' : 'An error occurred'));
        }
    } catch (error) {
        console.error('Error deleting role:', error);
        showError(lang === 'ar' ? 'خطأ في الحذف' : 'Error deleting');
    }
}

// =============== Permissions Management ===============

async function loadPermissions() {
    try {
        const response = await fetch('/api/permissions');
        allPermissions = await response.json();
        displayPermissions(allPermissions);
        populateModuleFilter(allPermissions);
        renderModuleChips([...new Set(allPermissions.map(p => p.module))]);
    } catch (error) {
        console.error('Error loading permissions:', error);
        showError(lang === 'ar' ? 'خطأ في تحميل الصلاحيات' : 'Error loading permissions');
    }
}

function displayPermissions(permissions) {
    const tbody = document.getElementById('permissionsTableBody');
    
    if (permissions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted">
                    <i class="fas fa-inbox"></i>
                    ${lang === 'ar' ? 'لا توجد صلاحيات' : 'No permissions available'}
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = permissions.map(perm => `
        <tr>
            <td><span class="badge bg-primary">${perm.module}</span></td>
            <td><span class="badge bg-secondary">${perm.action}</span></td>
            <td>${perm.display_name_ar}</td>
            <td>${perm.display_name_en}</td>
        </tr>
    `).join('');
}

function populateModuleFilter(permissions) {
    const modules = [...new Set(permissions.map(p => p.module))];
    const select = document.getElementById('filterModule');
    
    modules.forEach(module => {
        const option = document.createElement('option');
        option.value = module;
        option.textContent = module;
        select.appendChild(option);
    });
}

function filterPermissions() {
    const selectModule = document.getElementById('filterModule') ? document.getElementById('filterModule').value : '';
    const activeModules = selectedModules.size > 0 ? Array.from(selectedModules) : (selectModule ? [selectModule] : []);

    let filtered = allPermissions.slice();

    // Module filter (multi-select via chips or single-select fallback)
    if (activeModules.length > 0) {
        const set = new Set(activeModules);
        filtered = filtered.filter(p => set.has(p.module));
    }

    // Text search filter across module, action, and localized display names
    if (permissionSearchTerm) {
        const term = permissionSearchTerm;
        filtered = filtered.filter(p => {
            const ar = (p.display_name_ar || '').toLowerCase();
            const en = (p.display_name_en || '').toLowerCase();
            const mod = (p.module || '').toLowerCase();
            const act = (p.action || '').toLowerCase();
            return ar.includes(term) || en.includes(term) || mod.includes(term) || act.includes(term);
        });
    }

    displayPermissions(filtered);
}

// Render module chips (toggleable)
function renderModuleChips(modules) {
    const container = document.getElementById('moduleChips');
    if (!container) return;
    const anySelected = selectedModules.size > 0;
    container.innerHTML = modules.map(m => {
        const isActive = selectedModules.has(m);
        const btnClass = isActive ? 'btn btn-sm btn-primary chip me-1 mb-1 rounded-pill active' : 'btn btn-sm btn-outline-primary chip me-1 mb-1 rounded-pill inactive';
        return `<button type="button" class="${btnClass}" data-module="${m}"><i class="fas fa-folder me-1"></i>${m}</button>`;
    }).join('');
    // Attach handlers
    container.querySelectorAll('button[data-module]').forEach(btn => {
        btn.addEventListener('click', () => {
            const m = btn.getAttribute('data-module');
            if (selectedModules.has(m)) {
                selectedModules.delete(m);
            } else {
                selectedModules.add(m);
            }
            // Rerender chips to reflect active/inactive
            renderModuleChips(modules);
            filterPermissions();
        });
    });
}

// =============== User Roles Management ===============

async function loadUserRoles(page = 1) {
    currentPageUserRoles = page;
    const searchInput = document.getElementById('searchUserRoles');
    const search = searchInput ? searchInput.value.trim() : '';
    
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: perPage
        });
        
        if (search) {
            params.append('search', search);
        }
        
        const response = await fetch(`/api/user-roles?${params}`);
        const data = await response.json();
        
        displayUserRoles(data.user_roles || []);
        displayUserRolesPagination(data);
    } catch (error) {
        console.error('Error loading user roles:', error);
        showError(lang === 'ar' ? 'خطأ في تحميل أدوار المستخدمين' : 'Error loading user roles');
    }
}

function displayUserRoles(userRoles) {
    const tbody = document.getElementById('userRolesTableBody');
    
    if (userRoles.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted">
                    <i class="fas fa-inbox"></i>
                    ${lang === 'ar' ? 'لا توجد بيانات' : 'No data available'}
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = userRoles.map(ur => `
        <tr>
            <td><strong>${ur.username}</strong></td>
            <td>
                ${ur.roles.map(role => `
                    <span class="badge bg-info me-1">${lang === 'ar' ? role.name_ar : role.name_en}</span>
                `).join('')}
            </td>
            <td>
                ${ur.primary_role ? 
                    `<span class="badge bg-success">${lang === 'ar' ? ur.primary_role.name_ar : ur.primary_role.name_en}</span>` : 
                    '-'
                }
            </td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="manageUserRoles(${ur.user_id})">
                    <i class="fas fa-edit"></i> ${lang === 'ar' ? 'إدارة' : 'Manage'}
                </button>
            </td>
        </tr>
    `).join('');
}

function displayUserRolesPagination(data) {
    const paginationDiv = document.getElementById('userRolesPagination');
    if (!paginationDiv) return;
    
    const { total, pages, current_page } = data;
    
    if (pages <= 1) {
        paginationDiv.innerHTML = '';
        return;
    }
    
    let html = '<nav><ul class="pagination justify-content-center">';
    
    // Previous button
    html += `
        <li class="page-item ${current_page === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="event.preventDefault(); loadUserRoles(${current_page - 1})">
                ${lang === 'ar' ? 'السابق' : 'Previous'}
            </a>
        </li>
    `;
    
    // Page numbers (show max 5 pages)
    let startPage = Math.max(1, current_page - 2);
    let endPage = Math.min(pages, current_page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === current_page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadUserRoles(${i})">${i}</a>
            </li>
        `;
    }
    
    // Next button
    html += `
        <li class="page-item ${current_page === pages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="event.preventDefault(); loadUserRoles(${current_page + 1})">
                ${lang === 'ar' ? 'التالي' : 'Next'}
            </a>
        </li>
    `;
    
    html += '</ul></nav>';
    
    // Add total count
    html += `<div class="text-center text-muted small mt-2">
        ${lang === 'ar' ? 'إجمالي' : 'Total'}: ${total} ${lang === 'ar' ? 'مستخدم' : 'users'}
    </div>`;
    
    paginationDiv.innerHTML = html;
}

async function loadUsers(page = 1) {
    currentPageUsers = page;
    
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 100 // Load more for dropdown
        });
        
        const response = await fetch(`/api/users?${params}`);
        const data = await response.json();
        const users = data.users || [];
        
        const select = document.getElementById('assignUserId');
        if (select) {
            select.innerHTML = '<option value="">' + (lang === 'ar' ? 'اختر مستخدم...' : 'Select User...') + '</option>';
            
            users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = user.username;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function openAssignRoleModal() {
    // Load roles for dropdown
    if (allRoles.length === 0) {
        await loadRoles();
    }
    
    const select = document.getElementById('assignRoleId');
    select.innerHTML = '<option value="">' + (lang === 'ar' ? 'اختر دور...' : 'Select Role...') + '</option>';
    
    allRoles.forEach(role => {
        const option = document.createElement('option');
        option.value = role.id;
        option.textContent = lang === 'ar' ? role.display_name_ar : role.display_name_en;
        select.appendChild(option);
    });
    
    document.getElementById('assignRoleForm').reset();
    const modal = new bootstrap.Modal(document.getElementById('assignRoleModal'));
    modal.show();
}

async function assignRole() {
    const userId = document.getElementById('assignUserId').value;
    const roleId = document.getElementById('assignRoleId').value;
    const isPrimary = document.getElementById('assignPrimary').checked;
    
    if (!userId || !roleId) {
        showError(lang === 'ar' ? 'يرجى اختيار المستخدم والدور' : 'Please select user and role');
        return;
    }
    
    try {
        const response = await fetch('/api/user-roles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, role_id: roleId, is_primary: isPrimary })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(lang === 'ar' ? 'تم التعيين بنجاح' : 'Assigned successfully');
            bootstrap.Modal.getInstance(document.getElementById('assignRoleModal')).hide();
            loadUserRoles();
        } else {
            showError(result.error || (lang === 'ar' ? 'حدث خطأ' : 'An error occurred'));
        }
    } catch (error) {
        console.error('Error assigning role:', error);
        showError(lang === 'ar' ? 'خطأ في التعيين' : 'Error assigning');
    }
}

// =============== Utility Functions ===============

function showSuccess(message) {
    alert(message); // يمكن استبدالها بنظام إشعارات أفضل
}

function showError(message) {
    alert(message);
}
