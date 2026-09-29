document.addEventListener('DOMContentLoaded', () => {
  const navItems = {
    dashboard: document.getElementById('navDashboard'),
    vendors: document.getElementById('navVendorMgmt'),
    reports: document.getElementById('navReports')
  };

  const pageViews = {
    dashboard: document.getElementById('dashboardView'),
    vendors: document.getElementById('vendorMgmtView'),
    reports: document.getElementById('reportsView')
  };

  // Summary Metric elements
  const metricTotal = document.getElementById('metricTotal');
  const metricPending = document.getElementById('metricPending');
  const metricApproved = document.getElementById('metricApproved');
  const metricSuspended = document.getElementById('metricSuspended');

  // Recent Vendors Table body (Dashboard view)
  const recentVendorsTableBody = document.getElementById('recentVendorsTableBody');

  // Vendor Management Table body & Filter elements
  const vendorMgmtTableBody = document.getElementById('vendorMgmtTableBody');
  const vendorSearchInput = document.getElementById('vendorSearchInput');
  const statusFilterSelect = document.getElementById('statusFilterSelect');

  // Modal elements
  const actionModalOverlay = document.getElementById('actionModalOverlay');
  const modalTitle = document.getElementById('modalTitle');
  const modalBodyText = document.getElementById('modalBodyText');
  const modalConfirmBtn = document.getElementById('modalConfirmBtn');
  const modalCancelBtn = document.getElementById('modalCancelBtn');

  // Toast element
  const adminToast = document.getElementById('adminToast');

  let activeVendorTarget = null; // { id, business_name, targetStatus }

  // --- 1. Navigation Controller ---
  function switchAdminTab(targetKey) {
    Object.keys(navItems).forEach(key => {
      if (navItems[key]) navItems[key].classList.remove('active');
      if (pageViews[key]) pageViews[key].classList.remove('active');
    });

    if (navItems[targetKey]) navItems[targetKey].classList.add('active');
    if (pageViews[targetKey]) pageViews[targetKey].classList.add('active');

    if (targetKey === 'dashboard') {
      loadDashboardData();
    } else if (targetKey === 'vendors') {
      loadVendorManagementData();
    }
  }

  window.switchAdminTab = switchAdminTab;

  Object.keys(navItems).forEach(key => {
    if (navItems[key]) {
      navItems[key].addEventListener('click', (e) => {
        e.preventDefault();
        switchAdminTab(key);
      });
    }
  });

  // --- 2. Toast Controller ---
  function showToast(msg) {
    if (!adminToast) return;
    adminToast.textContent = msg;
    adminToast.classList.add('visible');
    setTimeout(() => {
      adminToast.classList.remove('visible');
    }, 3000);
  }

  // --- 3. Format Date Helper ---
  function formatDate(isoStr) {
    if (!isoStr) return 'N/A';
    const date = new Date(isoStr);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  }

  // --- 4. Render Status Badge Helper ---
  function renderStatusBadge(status) {
    const st = (status || 'Pending').toLowerCase();
    let badgeClass = 'badge-pending';
    if (st === 'approved') badgeClass = 'badge-approved';
    if (st === 'suspended') badgeClass = 'badge-suspended';

    const capStatus = st.charAt(0).toUpperCase() + st.slice(1);
    return `<span class="badge-status ${badgeClass}">${capStatus}</span>`;
  }

  // --- 5. Dashboard Data Loader ---
  async function loadDashboardData() {
    try {
      const metricsRes = await fetch('/api/admin/metrics');
      const metricsJson = await metricsRes.json();
      if (metricsRes.ok && metricsJson.success) {
        const m = metricsJson.metrics;
        if (metricTotal) metricTotal.textContent = m.total;
        if (metricPending) metricPending.textContent = m.pending;
        if (metricApproved) metricApproved.textContent = m.approved;
        if (metricSuspended) metricSuspended.textContent = m.suspended;
      }

      const vendorsRes = await fetch('/api/admin/vendors');
      const vendorsJson = await vendorsRes.json();
      if (vendorsRes.ok && vendorsJson.success && recentVendorsTableBody) {
        const list = vendorsJson.vendors.slice(0, 5);
        if (list.length === 0) {
          recentVendorsTableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:1.5rem; color:var(--text-muted);">No vendor accounts registered yet.</td></tr>`;
        } else {
          recentVendorsTableBody.innerHTML = list.map(v => `
            <tr>
              <td><span style="font-weight: 700; color: #ffffff;">${escapeHtml(v.full_name)}</span></td>
              <td>${escapeHtml(v.business_name)}</td>
              <td>${escapeHtml(v.email)}</td>
              <td>${renderStatusBadge(v.status)}</td>
              <td>${formatDate(v.created_at)}</td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.error('Error loading admin dashboard data:', err);
    }
  }

  // --- 6. Vendor Management Data Loader ---
  async function loadVendorManagementData() {
    try {
      const searchVal = vendorSearchInput ? vendorSearchInput.value.trim() : '';
      const statusVal = statusFilterSelect ? statusFilterSelect.value : 'All';

      let queryParams = [];
      if (searchVal) queryParams.push(`search=${encodeURIComponent(searchVal)}`);
      if (statusVal && statusVal !== 'All') queryParams.push(`status=${encodeURIComponent(statusVal)}`);
      const queryString = queryParams.length > 0 ? `?${queryParams.join('&')}` : '';

      const res = await fetch(`/api/admin/vendors${queryString}`);
      const json = await res.json();

      if (res.ok && json.success && vendorMgmtTableBody) {
        const vendors = json.vendors || [];
        if (vendors.length === 0) {
          vendorMgmtTableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:2rem; color:var(--text-muted);">No matching vendors found.</td></tr>`;
        } else {
          vendorMgmtTableBody.innerHTML = vendors.map(v => {
            const isApproved = v.status === 'Approved';
            const isSuspended = v.status === 'Suspended';

            let approveBtn = `<button class="btn-action btn-approve" onclick="openActionModal(${v.id}, '${escapeQuote(v.business_name)}', 'Approved')">Approve</button>`;
            let suspendBtn = `<button class="btn-action btn-suspend" onclick="openActionModal(${v.id}, '${escapeQuote(v.business_name)}', 'Suspended')">Suspend</button>`;

            if (isApproved) {
              approveBtn = `<button class="btn-action btn-approve" disabled style="opacity:0.4; cursor:not-allowed;">Approved</button>`;
            } else if (isSuspended) {
              suspendBtn = `<button class="btn-action btn-suspend" disabled style="opacity:0.4; cursor:not-allowed;">Suspended</button>`;
            }

            return `
              <tr>
                <td><span style="font-weight: 700; color: #ffffff;">${escapeHtml(v.full_name)}</span></td>
                <td>${escapeHtml(v.business_name)}</td>
                <td>${escapeHtml(v.email)}</td>
                <td>${renderStatusBadge(v.status)}</td>
                <td>${formatDate(v.created_at)}</td>
                <td>
                  <div class="action-buttons">
                    ${approveBtn}
                    ${suspendBtn}
                  </div>
                </td>
              </tr>
            `;
          }).join('');
        }
      }
    } catch (err) {
      console.error('Error loading vendor management list:', err);
    }
  }

  let searchTimeout = null;
  if (vendorSearchInput) {
    vendorSearchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(loadVendorManagementData, 300);
    });
  }

  if (statusFilterSelect) {
    statusFilterSelect.addEventListener('change', loadVendorManagementData);
  }

  window.openActionModal = function(id, businessName, targetStatus) {
    activeVendorTarget = { id, businessName, targetStatus };
    const isApprove = targetStatus === 'Approved';

    if (modalTitle) modalTitle.textContent = isApprove ? 'Approve Vendor Account' : 'Suspend Vendor Account';
    if (modalBodyText) {
      modalBodyText.textContent = isApprove
        ? `Are you sure you want to approve '${businessName}'? This will allow them to login and publish products.`
        : `Are you sure you want to suspend '${businessName}'? This will prevent them from accessing their vendor portal.`;
    }

    if (modalConfirmBtn) {
      modalConfirmBtn.textContent = isApprove ? 'Approve Vendor' : 'Suspend Vendor';
      modalConfirmBtn.className = isApprove ? 'btn-modal btn-modal-approve' : 'btn-modal btn-modal-suspend';
    }

    if (actionModalOverlay) actionModalOverlay.style.display = 'flex';
  };

  function closeModal() {
    activeVendorTarget = null;
    if (actionModalOverlay) actionModalOverlay.style.display = 'none';
  }

  if (modalCancelBtn) modalCancelBtn.addEventListener('click', closeModal);

  if (modalConfirmBtn) {
    modalConfirmBtn.addEventListener('click', async () => {
      if (!activeVendorTarget) return;

      const { id, businessName, targetStatus } = activeVendorTarget;
      modalConfirmBtn.disabled = true;

      try {
        const res = await fetch(`/api/admin/vendors/${id}/status`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: targetStatus })
        });

        const json = await res.json();
        modalConfirmBtn.disabled = false;
        closeModal();

        if (res.ok && json.success) {
          showToast(json.message || `Vendor status updated to ${targetStatus}.`);
          loadVendorManagementData();
        } else {
          alert(json.detail || 'Failed to update vendor status.');
        }
      } catch (err) {
        modalConfirmBtn.disabled = false;
        closeModal();
        alert('Server connection error. Please try again.');
      }
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function escapeQuote(str) {
    if (!str) return '';
    return String(str).replace(/'/g, "\\'");
  }

  const initialHash = window.location.hash.replace('#', '');
  if (initialHash === 'vendors') switchAdminTab('vendors');
  else if (initialHash === 'reports') switchAdminTab('reports');
  else switchAdminTab('dashboard');
});
