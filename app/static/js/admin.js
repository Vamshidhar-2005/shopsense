document.addEventListener('DOMContentLoaded', () => {
  // Navigation elements
  const navDashboard = document.getElementById('navDashboard');
  const navVendorMgmt = document.getElementById('navVendorMgmt');
  const dashboardView = document.getElementById('dashboardView');
  const vendorMgmtView = document.getElementById('vendorMgmtView');

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

  // Toast Toast element
  const adminToast = document.getElementById('adminToast');

  let activeVendorTarget = null; // { id, business_name, targetStatus }

  // --- 1. Navigation Controller ---
  function switchTab(target) {
    if (target === 'dashboard') {
      navDashboard.classList.add('active');
      navVendorMgmt.classList.remove('active');
      dashboardView.classList.add('active');
      vendorMgmtView.classList.remove('active');
      loadDashboardData();
    } else if (target === 'vendors') {
      navVendorMgmt.classList.add('active');
      navDashboard.classList.remove('active');
      vendorMgmtView.classList.add('active');
      dashboardView.classList.remove('active');
      loadVendorManagementData();
    }
  }

  if (navDashboard) navDashboard.addEventListener('click', (e) => { e.preventDefault(); switchTab('dashboard'); });
  if (navVendorMgmt) navVendorMgmt.addEventListener('click', (e) => { e.preventDefault(); switchTab('vendors'); });

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
      // Load Summary Cards
      const metricsRes = await fetch('/api/admin/metrics');
      const metricsJson = await metricsRes.json();
      if (metricsRes.ok && metricsJson.success) {
        const m = metricsJson.metrics;
        if (metricTotal) metricTotal.textContent = m.total;
        if (metricPending) metricPending.textContent = m.pending;
        if (metricApproved) metricApproved.textContent = m.approved;
        if (metricSuspended) metricSuspended.textContent = m.suspended;
      }

      // Load Recent Vendors (up to 5)
      const vendorsRes = await fetch('/api/admin/vendors');
      const vendorsJson = await vendorsRes.json();
      if (vendorsRes.ok && vendorsJson.success && recentVendorsTableBody) {
        const list = vendorsJson.vendors.slice(0, 5);
        if (list.length === 0) {
          recentVendorsTableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color: var(--text-muted); padding: 2rem;">No registered vendors found yet.</td></tr>`;
          return;
        }

        recentVendorsTableBody.innerHTML = list.map(v => `
          <tr>
            <td style="font-weight: 600;">${escapeHtml(v.full_name)}</td>
            <td>${escapeHtml(v.business_name)}</td>
            <td style="color: var(--text-muted);">${escapeHtml(v.email)}</td>
            <td>${renderStatusBadge(v.status)}</td>
            <td>${formatDate(v.created_at)}</td>
          </tr>
        `).join('');
      }
    } catch (err) {
      console.error('Error loading admin dashboard data:', err);
    }
  }

  // --- 6. Vendor Management Data Loader ---
  async function loadVendorManagementData() {
    if (!vendorMgmtTableBody) return;

    const searchTerm = vendorSearchInput ? vendorSearchInput.value.trim() : '';
    const statusVal = statusFilterSelect ? statusFilterSelect.value : 'All';

    try {
      const url = `/api/admin/vendors?search=${encodeURIComponent(searchTerm)}&status=${encodeURIComponent(statusVal)}`;
      const res = await fetch(url);
      const json = await res.json();

      if (res.ok && json.success) {
        const vendors = json.vendors;
        if (vendors.length === 0) {
          vendorMgmtTableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted); padding: 2rem;">No matching vendors found.</td></tr>`;
          return;
        }

        vendorMgmtTableBody.innerHTML = vendors.map(v => {
          const st = (v.status || 'Pending').toLowerCase();
          let actionsHtml = '';

          if (st === 'pending') {
            actionsHtml = `
              <div class="action-group">
                <button class="btn-action btn-approve" onclick="openConfirmModal(${v.id}, '${escapeQuote(v.business_name)}', 'Approved')">Approve</button>
                <button class="btn-action btn-suspend" onclick="openConfirmModal(${v.id}, '${escapeQuote(v.business_name)}', 'Suspended')">Suspend</button>
              </div>
            `;
          } else if (st === 'approved') {
            actionsHtml = `
              <div class="action-group">
                <button class="btn-action btn-suspend" onclick="openConfirmModal(${v.id}, '${escapeQuote(v.business_name)}', 'Suspended')">Suspend</button>
              </div>
            `;
          } else if (st === 'suspended') {
            actionsHtml = `
              <div class="action-group">
                <button class="btn-action btn-approve" onclick="openConfirmModal(${v.id}, '${escapeQuote(v.business_name)}', 'Approved')">Approve</button>
              </div>
            `;
          }

          return `
            <tr>
              <td style="font-weight: 600;">${escapeHtml(v.full_name)}</td>
              <td>${escapeHtml(v.business_name)}</td>
              <td style="color: var(--text-muted);">${escapeHtml(v.email)}</td>
              <td>${renderStatusBadge(v.status)}</td>
              <td>${formatDate(v.created_at)}</td>
              <td>${actionsHtml}</td>
            </tr>
          `;
        }).join('');
      }
    } catch (err) {
      console.error('Error loading vendor management list:', err);
    }
  }

  // --- 7. Search & Filter Listeners ---
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

  // --- 8. Confirmation Modal Controller ---
  window.openConfirmModal = function(id, businessName, targetStatus) {
    activeVendorTarget = { id, businessName, targetStatus };

    if (targetStatus === 'Approved') {
      modalTitle.textContent = 'Approve Vendor';
      modalBodyText.innerHTML = `Are you sure you want to approve '<strong>${escapeHtml(businessName)}</strong>'?`;
      modalConfirmBtn.textContent = 'Approve Vendor';
      modalConfirmBtn.className = 'btn-modal btn-modal-approve';
    } else {
      modalTitle.textContent = 'Suspend Vendor';
      modalBodyText.innerHTML = `Are you sure you want to suspend '<strong>${escapeHtml(businessName)}</strong>'?`;
      modalConfirmBtn.textContent = 'Suspend Vendor';
      modalConfirmBtn.className = 'btn-modal btn-modal-suspend';
    }

    actionModalOverlay.classList.add('visible');
  };

  function closeModal() {
    actionModalOverlay.classList.remove('visible');
    activeVendorTarget = null;
  }

  if (modalCancelBtn) modalCancelBtn.addEventListener('click', closeModal);

  if (modalConfirmBtn) {
    modalConfirmBtn.addEventListener('click', async () => {
      if (!activeVendorTarget) return;

      const { id, targetStatus } = activeVendorTarget;
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
          showToast(json.message);
          loadVendorManagementData();
          loadDashboardData();
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

  // Utility Escapes
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function escapeQuote(str) {
    if (!str) return '';
    return String(str).replace(/'/g, "\\'");
  }

  // Initial Load: Default to Dashboard view
  switchTab('dashboard');
});
