document.addEventListener('DOMContentLoaded', () => {
  // Navigation elements
  const navItems = {
    dashboard: document.getElementById('navDashboard'),
    catalog: document.getElementById('navCatalog'),
    addProduct: document.getElementById('navAddProduct'),
    m2Intelligence: document.getElementById('navM2Intelligence'),
    insights: document.getElementById('navInsights'),
    profile: document.getElementById('navProfile')
  };

  const pageViews = {
    dashboard: document.getElementById('dashboardView'),
    catalog: document.getElementById('catalogView'),
    addProduct: document.getElementById('addProductView'),
    m2Intelligence: document.getElementById('m2IntelligenceView'),
    insights: document.getElementById('insightsView'),
    profile: document.getElementById('profileView')
  };

  // Welcome heading element
  const vendorWelcomeName = document.getElementById('vendorWelcomeName');

  // Summary Metric elements
  const metricSales = document.getElementById('metricSales');
  const metricRevenue = document.getElementById('metricRevenue');
  const metricTransactions = document.getElementById('metricTransactions');
  const metricProducts = document.getElementById('metricProducts');

  // Dashboard Recent Products elements
  const recentProductsTableBody = document.getElementById('recentProductsTableBody');
  const productsTableSection = document.getElementById('productsTableSection');
  const emptyStateContainer = document.getElementById('emptyStateContainer');
  const emptyStateAddProductBtn = document.getElementById('emptyStateAddProductBtn');

  // Catalog View elements
  const catalogSearchInput = document.getElementById('catalogSearchInput');
  const catalogTableSection = document.getElementById('catalogTableSection');
  const catalogTableBody = document.getElementById('catalogTableBody');
  const catalogEmptyStateContainer = document.getElementById('catalogEmptyStateContainer');
  const catalogEmptyAddProductBtn = document.getElementById('catalogEmptyAddProductBtn');

  // Add Product Form elements
  const addProductForm = document.getElementById('addProductForm');
  const prodNameInput = document.getElementById('prodNameInput');
  const prodPriceInput = document.getElementById('prodPriceInput');
  const prodCategorySelect = document.getElementById('prodCategorySelect');
  const prodStockInput = document.getElementById('prodStockInput');
  const prodImageUrlInput = document.getElementById('prodImageUrlInput');
  const prodDescInput = document.getElementById('prodDescInput');
  const btnGenerateAiDesc = document.getElementById('btnGenerateAiDesc');
  const btnCancelAddProduct = document.getElementById('btnCancelAddProduct');

  // Insights View elements
  const statTotalOrders = document.getElementById('statTotalOrders');
  const statCompletedOrders = document.getElementById('statCompletedOrders');
  const statPendingOrders = document.getElementById('statPendingOrders');
  const statCancelledOrders = document.getElementById('statCancelledOrders');

  const btnTrendDaily = document.getElementById('btnTrendDaily');
  const btnTrendWeekly = document.getElementById('btnTrendWeekly');
  const btnTrendMonthly = document.getElementById('btnTrendMonthly');
  const salesTrendsBarsContainer = document.getElementById('salesTrendsBarsContainer');

  const bestSellingTableSection = document.getElementById('bestSellingTableSection');
  const bestSellingTableBody = document.getElementById('bestSellingTableBody');
  const bestSellingEmptyState = document.getElementById('bestSellingEmptyState');

  // Profile View elements
  const vendorProfileForm = document.getElementById('vendorProfileForm');
  const profileFullName = document.getElementById('profileFullName');
  const profileBusinessName = document.getElementById('profileBusinessName');
  const profileEmail = document.getElementById('profileEmail');
  const profilePhone = document.getElementById('profilePhone');
  const profileAddress = document.getElementById('profileAddress');
  const profileStatusBadge = document.getElementById('profileStatusBadge');

  const vendorPasswordForm = document.getElementById('vendorPasswordForm');
  const pwdCurrent = document.getElementById('pwdCurrent');
  const pwdNew = document.getElementById('pwdNew');
  const pwdConfirm = document.getElementById('pwdConfirm');

  // Retrieve stored vendor ID / session name
  const storedVendorId = sessionStorage.getItem('vendor_id') || 1;
  const storedVendorName = sessionStorage.getItem('vendor_name');

  if (storedVendorName && vendorWelcomeName) {
    vendorWelcomeName.textContent = storedVendorName;
  }

  // Active trend tab tracking
  let currentTrendPeriod = 'daily';
  let cachedInsightsData = null;

  // Navigation controller
  function switchTab(targetKey) {
    Object.keys(navItems).forEach(key => {
      if (navItems[key]) navItems[key].classList.remove('active');
      if (pageViews[key]) pageViews[key].classList.remove('active');
    });

    if (navItems[targetKey]) navItems[targetKey].classList.add('active');
    if (pageViews[targetKey]) pageViews[targetKey].classList.add('active');

    if (targetKey === 'dashboard') {
      loadVendorDashboardData();
    } else if (targetKey === 'catalog') {
      loadCatalogData();
    } else if (targetKey === 'm2Intelligence') {
      loadInsightsData();
      if (typeof window.loadMlForecasting === 'function') window.loadMlForecasting(30);
      if (typeof window.testReviewSentiment === 'function') window.testReviewSentiment();
      if (typeof window.testVectorSearch === 'function') window.testVectorSearch();
    } else if (targetKey === 'insights') {
      loadInsightsData();
    } else if (targetKey === 'profile') {
      loadVendorProfileData();
    }
  }

  window.switchTab = switchTab;

  Object.keys(navItems).forEach(key => {
    if (navItems[key]) {
      navItems[key].addEventListener('click', (e) => {
        e.preventDefault();
        switchTab(key);
      });
    }
  });

  if (emptyStateAddProductBtn) {
    emptyStateAddProductBtn.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab('addProduct');
    });
  }

  if (catalogEmptyAddProductBtn) {
    catalogEmptyAddProductBtn.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab('addProduct');
    });
  }

  // Load Vendor Profile Data from API
  async function loadVendorProfileData() {
    try {
      const res = await fetch(`/api/vendor/profile?vendor_id=${storedVendorId}`);
      const json = await res.json();

      if (res.ok && json.success) {
        const v = json.vendor;
        if (profileFullName) profileFullName.value = v.full_name || '';
        if (profileBusinessName) profileBusinessName.value = v.business_name || '';
        if (profileEmail) profileEmail.value = v.email || '';
        if (profilePhone) profilePhone.value = v.phone_number || '';
        if (profileAddress) profileAddress.value = v.business_address || '';

        if (profileStatusBadge) {
          profileStatusBadge.textContent = `Account Status: ${v.status}`;
          profileStatusBadge.className = `badge-stock ${v.status === 'Approved' ? 'badge-active' : 'badge-out-of-stock'}`;
        }
      }
    } catch (err) {
      console.error('Error loading vendor profile:', err);
    }
  }

  // Submit Vendor Profile Form
  if (vendorProfileForm) {
    vendorProfileForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const fullName = profileFullName.value.trim();
      const businessName = profileBusinessName.value.trim();
      const phone = profilePhone.value.trim();
      const address = profileAddress.value.trim();

      if (!fullName || !businessName) {
        alert('Full Name and Business Name are required.');
        return;
      }

      try {
        const res = await fetch(`/api/vendor/profile?vendor_id=${storedVendorId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name: fullName,
            business_name: businessName,
            phone_number: phone || null,
            business_address: address || null
          })
        });

        const json = await res.json();
        if (res.ok && json.success) {
          alert(json.message || 'Profile updated successfully!');
          sessionStorage.setItem('vendor_name', fullName);
          if (vendorWelcomeName) vendorWelcomeName.textContent = fullName;
        } else {
          alert(json.detail || 'Failed to update profile.');
        }
      } catch (err) {
        alert('Server connection error. Please try again.');
      }
    });
  }

  // Submit Vendor Password Form
  if (vendorPasswordForm) {
    vendorPasswordForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const currentPass = pwdCurrent.value;
      const newPass = pwdNew.value;
      const confirmPass = pwdConfirm.value;

      if (!currentPass || !newPass || !confirmPass) {
        alert('Please fill in all password fields.');
        return;
      }

      if (newPass.length < 6) {
        alert('New password must be at least 6 characters long.');
        return;
      }

      if (newPass !== confirmPass) {
        alert('New password and confirm password do not match.');
        return;
      }

      try {
        const res = await fetch(`/api/vendor/profile/password?vendor_id=${storedVendorId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            current_password: currentPass,
            new_password: newPass
          })
        });

        const json = await res.json();
        if (res.ok && json.success) {
          alert(json.message || 'Password updated successfully!');
          vendorPasswordForm.reset();
        } else {
          alert(json.detail || 'Failed to update password.');
        }
      } catch (err) {
        alert('Server connection error. Please try again.');
      }
    });
  }

  // Load Insights Data from Database API
  async function loadInsightsData() {
    try {
      const res = await fetch(`/api/vendor/insights?vendor_id=${storedVendorId}`);
      const json = await res.json();

      if (res.ok && json.success) {
        cachedInsightsData = json.insights;
        renderInsightsView(cachedInsightsData);
      }

      // Fetch Milestone 2 Inventory Analytics
      fetchMilestone2InventoryData();
      // Fetch Milestone 2 Customer Segmentation Analytics
      fetchMilestone2CustomerSegmentationData();
      // Fetch Milestone 2 Rule-Based Recommendations
      fetchMilestone2RecommendationsData();
    } catch (err) {
      console.error('Error loading insights data:', err);
    }
  }

  async function fetchMilestone2InventoryData() {
    try {
      const res = await fetch(`/api/vendor/inventory?vendor_id=${storedVendorId}&threshold=5`);
      const json = await res.json();
      if (res.ok && json.success) {
        const d = json.data;
        const sum = d.summary || {};
        const alerts = d.alerts || {};

        const invUnits = document.getElementById('m2InventoryUnits');
        const stockVal = document.getElementById('m2StockValuation');
        const lowAlerts = document.getElementById('m2LowStockAlerts');
        const outAlerts = document.getElementById('m2OutOfStockCount');
        const alertBoxContainer = document.getElementById('m2LowStockItemsContainer');

        if (invUnits) invUnits.textContent = sum.total_inventory_units || 0;
        if (stockVal) stockVal.textContent = '$' + Number(sum.total_inventory_value || 0).toFixed(2);
        if (lowAlerts) lowAlerts.textContent = sum.low_stock_count || 0;
        if (outAlerts) outAlerts.textContent = sum.out_of_stock_count || 0;

        const actionItems = [...(alerts.out_of_stock_items || []), ...(alerts.low_stock_items || [])];

        if (alertBoxContainer) {
          if (actionItems.length === 0) {
            alertBoxContainer.innerHTML = `
              <div style="padding: 1rem; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; color: #34d399; font-size: 0.9rem; font-weight: 700;">
                ✅ All inventory levels are healthy! No immediate restock required.
              </div>
            `;
          } else {
            alertBoxContainer.innerHTML = `
              <div class="table-responsive">
                <table class="custom-table">
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Category</th>
                      <th>Price</th>
                      <th>Current Stock</th>
                      <th>Alert Status</th>
                      <th>Suggested Reorder</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${actionItems.map(item => `
                      <tr>
                        <td>
                          <div class="product-cell">
                            <img src="${item.image_url}" alt="${escapeHtml(item.name)}" class="product-img" onerror="this.src='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=150';" />
                            <span class="product-title">${escapeHtml(item.name)}</span>
                          </div>
                        </td>
                        <td><span class="category-badge">${escapeHtml(item.category)}</span></td>
                        <td><span class="price-text">$${Number(item.price).toFixed(2)}</span></td>
                        <td style="font-weight: 800; color: ${item.is_out_of_stock ? '#f87171' : '#fbbf24'};">${item.stock} units</td>
                        <td>
                          <span class="badge-stock ${item.is_out_of_stock ? 'badge-out-of-stock' : 'badge-active'}" style="background: ${item.is_out_of_stock ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.2)'}; color: ${item.is_out_of_stock ? '#f87171' : '#fbbf24'};">
                            ${item.status}
                          </span>
                        </td>
                        <td style="font-weight: 800; color: #38bdf8;">+${item.suggested_reorder_qty} units</td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            `;
          }
        }
      }
    } catch (err) {
      console.error('Error fetching Milestone 2 inventory tracking:', err);
    }
  }

  async function fetchMilestone2CustomerSegmentationData() {
    try {
      const res = await fetch(`/api/vendor/customer-segmentation?vendor_id=${storedVendorId}`);
      const json = await res.json();
      if (res.ok && json.success) {
        const customers = (json.data || {}).all_customers || [];
        const tableBody = document.getElementById('customerOverviewTableBody');

        if (tableBody) {
          if (customers.length === 0) {
            tableBody.innerHTML = `
              <tr>
                <td colspan="3" style="padding: 1.5rem; text-align: center; color: #94a3b8;">No customer purchase records available yet.</td>
              </tr>
            `;
          } else {
            tableBody.innerHTML = customers.map(c => {
              let badgeColor = '#34d399';
              let badgeBg = 'rgba(16, 185, 129, 0.15)';
              let badgeBorder = '#10b981';
              let tierText = c.tier || 'New Customer';

              if (tierText.includes('Regular')) {
                badgeColor = '#38bdf8';
                badgeBg = 'rgba(56, 189, 248, 0.15)';
                badgeBorder = '#0284c7';
              } else if (tierText.includes('New') || tierText.includes('Bronze')) {
                badgeColor = '#fbbf24';
                badgeBg = 'rgba(245, 158, 11, 0.15)';
                badgeBorder = '#d97706';
              }

              return `
                <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05); transition: background 0.2s ease;">
                  <td style="padding: 1.15rem 1.25rem; font-weight: 700; color: #ffffff; font-size: 0.95rem;">${escapeHtml(c.name || 'Verified Buyer')}</td>
                  <td style="padding: 1.15rem 1.25rem; font-weight: 800; color: #ffffff; font-size: 0.95rem;">$${Number(c.total_spend || 0).toFixed(2)}</td>
                  <td style="padding: 1.15rem 1.25rem; text-align: right;">
                    <span style="display: inline-block; padding: 4px 14px; border-radius: 99px; font-size: 0.8rem; font-weight: 700; background: ${badgeBg}; border: 1px solid ${badgeBorder}; color: ${badgeColor};">
                      ${escapeHtml(tierText)}
                    </span>
                  </td>
                </tr>
              `;
            }).join('');
          }
        }

        if (vipCount) vipCount.textContent = sum.vip_count || 0;
        if (vipRev) vipRev.textContent = `Revenue: $${Number(sum.vip_revenue || 0).toFixed(2)}`;
        if (regCount) regCount.textContent = sum.regular_count || 0;
        if (regRev) regRev.textContent = `Revenue: $${Number(sum.regular_revenue || 0).toFixed(2)}`;
        if (broCount) broCount.textContent = sum.bronze_count || 0;
        if (broRev) broRev.textContent = `Revenue: $${Number(sum.bronze_revenue || 0).toFixed(2)}`;
      }
    } catch (err) {
      console.error('Error fetching customer segmentation:', err);
    }
  }

  async function fetchMilestone2RecommendationsData() {
    try {
      const res = await fetch(`/api/vendor/recommendations?vendor_id=${storedVendorId}`);
      const json = await res.json();
      if (res.ok && json.success) {
        const recs = (json.data || {}).recommendations || [];
        const container = document.getElementById('m2RecommendationsContainer');

        if (container) {
          if (recs.length === 0) {
            container.innerHTML = `
              <p style="color: #94a3b8; font-size: 0.9rem;">Add items to your catalog to generate rule-based cross-sell recommendations.</p>
            `;
          } else {
            container.innerHTML = `
              <div class="stats-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
                ${recs.map(r => `
                  <div class="stat-card" style="flex-direction: column; align-items: flex-start; gap: 0.85rem;">
                    <div style="display: flex; align-items: center; gap: 0.85rem;">
                      <img src="${r.image_url}" alt="${escapeHtml(r.product)}" style="width: 44px; height: 44px; border-radius: 8px; object-fit: cover;" onerror="this.src='https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=150';" />
                      <div>
                        <h4 style="font-size: 1rem; font-weight: 800; color: #ffffff;">${escapeHtml(r.product)}</h4>
                        <span class="category-badge">${escapeHtml(r.category)}</span>
                      </div>
                    </div>
                    <div style="font-size: 0.85rem; color: #38bdf8; font-weight: 600;">💡 ${escapeHtml(r.recommendation_reason)}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">🛍️ ${escapeHtml(r.suggested_bundle)}</div>
                    <div style="font-size: 1.05rem; font-weight: 800; color: #34d399;">$${Number(r.price).toFixed(2)}</div>
                  </div>
                `).join('')}
              </div>
            `;
          }
        }
      }
    } catch (err) {
      console.error('Error fetching recommendations:', err);
    }
  }

  function renderInsightsView(insights) {
    if (!insights) return;

    // 1. Render Customer Order Statistics from DB
    const stats = insights.order_stats || {};
    if (statTotalOrders) statTotalOrders.textContent = stats.total_orders || 0;
    if (statCompletedOrders) statCompletedOrders.textContent = stats.completed_orders || 0;
    if (statPendingOrders) statPendingOrders.textContent = stats.pending_orders || 0;
    if (statCancelledOrders) statCancelledOrders.textContent = stats.cancelled_orders || 0;

    // 2. Render Sales Trends Chart (Empty state if no DB trend data exists)
    renderSalesTrendsChart(insights.sales_trends || []);

    // 3. Render Best Selling Products (Empty state if no DB sold products exist)
    const bestSellers = insights.best_selling_products || [];
    if (bestSellers.length === 0) {
      if (bestSellingTableSection) bestSellingTableSection.style.display = 'none';
      if (bestSellingEmptyState) bestSellingEmptyState.style.display = 'flex';
    } else {
      if (bestSellingTableSection) bestSellingTableSection.style.display = 'block';
      if (bestSellingEmptyState) bestSellingEmptyState.style.display = 'none';

      if (bestSellingTableBody) {
        bestSellingTableBody.innerHTML = bestSellers.map((p, idx) => `
          <tr>
            <td><span class="rank-badge ${getRankClass(idx + 1)}">#${idx + 1}</span></td>
            <td>
              <div class="product-cell">
                <img 
                  src="${p.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=150'}" 
                  alt="${escapeHtml(p.name)}" 
                  class="product-img"
                  onerror="this.src='https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=150';"
                />
                <div class="product-info-text">
                  <span class="product-title">${escapeHtml(p.name)}</span>
                  <span class="product-ai-desc">${escapeHtml(p.ai_description || 'Catalog Item')}</span>
                </div>
              </div>
            </td>
            <td><span class="category-badge">${escapeHtml(p.category)}</span></td>
            <td style="font-weight: 700; color: var(--text-main);">${p.units_sold} units</td>
            <td><span class="price-text">$${Number(p.total_revenue).toFixed(2)}</span></td>
          </tr>
        `).join('');
      }
    }
  }

  function getRankClass(rank) {
    if (rank === 1) return 'rank-1';
    if (rank === 2) return 'rank-2';
    if (rank === 3) return 'rank-3';
    return 'rank-other';
  }

  function renderSalesTrendsChart(trendsData) {
    if (!salesTrendsBarsContainer) return;

    if (btnTrendDaily) btnTrendDaily.classList.toggle('active', currentTrendPeriod === 'daily');
    if (btnTrendWeekly) btnTrendWeekly.classList.toggle('active', currentTrendPeriod === 'weekly');
    if (btnTrendMonthly) btnTrendMonthly.classList.toggle('active', currentTrendPeriod === 'monthly');

    if (!trendsData || trendsData.length === 0) {
      salesTrendsBarsContainer.innerHTML = `
        <div class="empty-chart-notice">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="20" x2="18" y2="10"></line>
            <line x1="12" y1="20" x2="12" y2="4"></line>
            <line x1="6" y1="20" x2="6" y2="14"></line>
          </svg>
          <span>No sales trend data available yet.</span>
        </div>
      `;
      return;
    }

    salesTrendsBarsContainer.innerHTML = trendsData.map(item => `
      <div class="chart-bar-col">
        <div class="bar-fill" style="height: ${item.height};" data-val="${item.val}"></div>
        <span class="bar-label">${item.label}</span>
      </div>
    `).join('');
  }

  if (btnTrendDaily) btnTrendDaily.addEventListener('click', () => { currentTrendPeriod = 'daily'; loadInsightsData(); });
  if (btnTrendWeekly) btnTrendWeekly.addEventListener('click', () => { currentTrendPeriod = 'weekly'; loadInsightsData(); });
  if (btnTrendMonthly) btnTrendMonthly.addEventListener('click', () => { currentTrendPeriod = 'monthly'; loadInsightsData(); });

  // Dashboard Data Loader
  async function loadVendorDashboardData() {
    try {
      const res = await fetch(`/api/vendor/dashboard-data?vendor_id=${storedVendorId}`);
      const json = await res.json();

      if (res.ok && json.success) {
        const d = json.data;

        if (vendorWelcomeName) {
          vendorWelcomeName.textContent = d.vendor_name || 'Vendor';
        }

        if (metricSales) metricSales.textContent = d.total_sales;
        if (metricRevenue) metricRevenue.textContent = '$' + Number(d.total_revenue).toFixed(2);
        if (metricTransactions) metricTransactions.textContent = d.total_transactions;
        if (metricProducts) metricProducts.textContent = d.products_listed;

        const products = d.recent_products || [];

        if (products.length === 0) {
          if (productsTableSection) productsTableSection.style.display = 'none';
          if (emptyStateContainer) emptyStateContainer.style.display = 'flex';
        } else {
          if (productsTableSection) productsTableSection.style.display = 'block';
          if (emptyStateContainer) emptyStateContainer.style.display = 'none';

          if (recentProductsTableBody) {
            recentProductsTableBody.innerHTML = products.map(p => `
              <tr>
                <td>
                  <div class="product-cell">
                    <img 
                      src="${getProductImageUrl(p)}" 
                      alt="${escapeHtml(p.name)}" 
                      class="product-img"
                      onerror="this.src='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=150&auto=format&fit=crop';"
                    />
                    <div class="product-info-text">
                      <span class="product-title">${escapeHtml(p.name)}</span>
                      <span class="product-ai-desc">${escapeHtml(p.ai_description || 'AI Description generated upon catalog submission.')}</span>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="category-badge">${escapeHtml(p.category)}</span>
                </td>
                <td>
                  <span class="price-text">$${Number(p.price).toFixed(2)}</span>
                </td>
                <td>
                  <span class="stock-pill">${Number(p.stock) || 0}</span>
                </td>
              </tr>
            `).join('');
          }
        }
      }
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    }
  }

  // My Catalog Data Loader
  async function loadCatalogData() {
    try {
      const searchVal = catalogSearchInput ? catalogSearchInput.value.trim() : '';
      const res = await fetch(`/api/vendor/products?vendor_id=${storedVendorId}&search=${encodeURIComponent(searchVal)}`);
      const json = await res.json();

      if (res.ok && json.success) {
        const products = json.products || [];

        if (products.length === 0) {
          if (catalogTableSection) catalogTableSection.style.display = 'none';
          if (catalogEmptyStateContainer) catalogEmptyStateContainer.style.display = 'flex';
        } else {
          if (catalogTableSection) catalogTableSection.style.display = 'block';
          if (catalogEmptyStateContainer) catalogEmptyStateContainer.style.display = 'none';

          catalogTableBody.innerHTML = products.map(p => {
            const stockNum = Number(p.stock) || 0;
            const statusBadge = stockNum > 0
              ? `<span class="badge-stock badge-active">Active</span>`
              : `<span class="badge-stock badge-out-of-stock">Out of Stock</span>`;

            return `
              <tr>
                <td>
                  <div class="product-cell">
                    <img 
                      src="${getProductImageUrl(p)}" 
                      alt="${escapeHtml(p.name)}" 
                      class="product-img"
                      onerror="this.src='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=150&auto=format&fit=crop';"
                    />
                    <div class="product-info-text">
                      <span class="product-title">${escapeHtml(p.name)}</span>
                      <span class="product-ai-desc">${escapeHtml(p.ai_description || 'AI Description generated upon catalog submission.')}</span>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="category-badge">${escapeHtml(p.category)}</span>
                </td>
                <td>
                  <span class="price-text">$${Number(p.price).toFixed(2)}</span>
                </td>
                <td>
                  <span class="stock-pill">${stockNum}</span>
                </td>
                <td>
                  ${statusBadge}
                </td>
                <td>
                  <div class="action-group">
                    <button class="btn-action btn-view" onclick="viewProduct(${p.id})">View</button>
                    <button class="btn-action btn-edit" onclick="editProduct(${p.id})">Edit</button>
                    <button class="btn-action btn-delete" onclick="deleteProduct(${p.id}, '${escapeQuote(p.name)}')">Delete</button>
                  </div>
                </td>
              </tr>
            `;
          }).join('');
        }
      }
    } catch (err) {
      console.error('Error loading catalog products:', err);
    }
  }

  // Catalog search input listener
  let searchTimeout = null;
  if (catalogSearchInput) {
    catalogSearchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(loadCatalogData, 300);
    });
  }

  // AI Description Generator Handler
  if (btnGenerateAiDesc) {
    btnGenerateAiDesc.addEventListener('click', async () => {
      const name = prodNameInput ? prodNameInput.value.trim() : '';
      const category = prodCategorySelect ? prodCategorySelect.value : '';
      const rawDesc = prodDescInput ? prodDescInput.value.trim() : '';

      if (!name) {
        alert('Please enter a Product Name first to generate AI description.');
        return;
      }

      btnGenerateAiDesc.disabled = true;
      const origText = btnGenerateAiDesc.innerHTML;
      btnGenerateAiDesc.innerHTML = 'Generating AI Description...';

      try {
        const res = await fetch('/api/vendor/generate-ai-description', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, category, raw_description: rawDesc })
        });
        const json = await res.json();
        btnGenerateAiDesc.disabled = false;
        btnGenerateAiDesc.innerHTML = origText;

        if (res.ok && json.success) {
          if (prodDescInput) prodDescInput.value = json.ai_description;
        } else {
          alert('Failed to generate AI description.');
        }
      } catch (err) {
        btnGenerateAiDesc.disabled = false;
        btnGenerateAiDesc.innerHTML = origText;
        alert('Server connection error while generating AI description.');
      }
    });
  }

  // Add Product Form Submit Handler
  if (addProductForm) {
    addProductForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const name = prodNameInput.value.trim();
      const price = parseFloat(prodPriceInput.value);
      const category = prodCategorySelect.value;
      const stock = parseInt(prodStockInput.value, 10);
      const imageUrl = prodImageUrlInput.value.trim();
      const aiDescription = prodDescInput.value.trim();

      if (!name || isNaN(price) || price <= 0 || !category || isNaN(stock) || stock < 0) {
        alert('Please fill in all required fields accurately.');
        return;
      }

      try {
        const res = await fetch(`/api/vendor/products?vendor_id=${storedVendorId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name,
            category,
            price,
            stock,
            image_url: imageUrl || null,
            ai_description: aiDescription || null
          })
        });

        const json = await res.json();

        if (res.ok && json.success) {
          alert(json.message || 'Product saved successfully!');
          addProductForm.reset();
          switchTab('catalog');
        } else {
          alert(json.detail || 'Failed to save product.');
        }
      } catch (err) {
        alert('Server connection error. Please try again.');
      }
    });
  }

  if (btnCancelAddProduct) {
    btnCancelAddProduct.addEventListener('click', () => {
      if (addProductForm) addProductForm.reset();
      switchTab('catalog');
    });
  }

  // Delete product action handler
  window.deleteProduct = async function(id, name) {
    if (!confirm(`Are you sure you want to delete '${name}' from your catalog?`)) return;

    try {
      const res = await fetch(`/api/vendor/products/${id}?vendor_id=${storedVendorId}`, {
        method: 'DELETE'
      });
      const json = await res.json();

      if (res.ok && json.success) {
        alert(json.message || 'Product removed successfully.');
        loadCatalogData();
      } else {
        alert(json.detail || 'Failed to delete product.');
      }
    } catch (err) {
      alert('Server connection error. Please try again.');
    }
  };

  window.viewProduct = async function(id) {
    try {
      const res = await fetch(`/api/vendor/products/${id}?vendor_id=${storedVendorId}`);
      const json = await res.json();
      if (res.ok && json.success) {
        const p = json.product;
        document.getElementById('viewProdTitle').textContent = p.name;
        document.getElementById('viewProdCategory').textContent = p.category;
        document.getElementById('viewProdPrice').textContent = '$' + Number(p.price).toFixed(2);
        document.getElementById('viewProdStock').textContent = p.stock + ' units';
        document.getElementById('viewProdDesc').textContent = p.ai_description || 'No description available.';
        document.getElementById('viewProdImage').src = p.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=150';
        document.getElementById('viewProductModal').style.display = 'flex';
      }
    } catch (err) {
      alert('Failed to load product details.');
    }
  };

  window.closeViewProductModal = function() {
    document.getElementById('viewProductModal').style.display = 'none';
  };

  window.editProduct = async function(id) {
    try {
      const res = await fetch(`/api/vendor/products/${id}?vendor_id=${storedVendorId}`);
      const json = await res.json();
      if (res.ok && json.success) {
        const p = json.product;
        document.getElementById('editProdId').value = p.id;
        document.getElementById('editProdName').value = p.name;
        document.getElementById('editProdPrice').value = p.price;
        document.getElementById('editProdCategory').value = p.category;
        document.getElementById('editProdStock').value = p.stock;
        document.getElementById('editProdImageUrl').value = p.image_url || '';
        document.getElementById('editProdDesc').value = p.ai_description || '';
        document.getElementById('editProductModal').style.display = 'flex';
      }
    } catch (err) {
      alert('Failed to load product details for editing.');
    }
  };

  window.closeEditProductModal = function() {
    document.getElementById('editProductModal').style.display = 'none';
  };

  const editProductForm = document.getElementById('editProductForm');
  if (editProductForm) {
    editProductForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = document.getElementById('editProdId').value;
      const name = document.getElementById('editProdName').value.trim();
      const price = parseFloat(document.getElementById('editProdPrice').value);
      const category = document.getElementById('editProdCategory').value;
      const stock = parseInt(document.getElementById('editProdStock').value, 10);
      const imageUrl = document.getElementById('editProdImageUrl').value.trim();
      const aiDescription = document.getElementById('editProdDesc').value.trim();

      try {
        const res = await fetch(`/api/vendor/products/${id}?vendor_id=${storedVendorId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name,
            category,
            price,
            stock,
            image_url: imageUrl || null,
            ai_description: aiDescription || null
          })
        });
        const json = await res.json();
        if (res.ok && json.success) {
          alert(json.message || 'Product updated successfully!');
          closeEditProductModal();
          loadCatalogData();
        } else {
          alert(json.detail || 'Failed to update product.');
        }
      } catch (err) {
        alert('Server connection error. Please try again.');
      }
    });
  }

  // Simulate Customer Order Handlers
  window.openSimulateOrderModal = async function() {
    const modal = document.getElementById('simulateOrderModal');
    const selectEl = document.getElementById('simSelectProduct');

    if (!modal) return;

    // Show modal immediately for instant UI feedback
    modal.style.display = 'flex';
    if (selectEl) selectEl.innerHTML = '<option value="">Loading products...</option>';

    try {
      const res = await fetch(`/api/vendor/products?vendor_id=${storedVendorId}`);
      const json = await res.json();

      if (res.ok && json.success) {
        const products = json.products || [];
        if (products.length === 0) {
          alert('Please add at least one product to your catalog first before simulating sales.');
          modal.style.display = 'none';
          switchTab('addProduct');
          return;
        }

        if (selectEl) {
          selectEl.innerHTML = products.map(p => 
            `<option value="${p.id}">${escapeHtml(p.name)} - $${Number(p.price).toFixed(2)} (Stock: ${p.stock})</option>`
          ).join('');
        }
      } else {
        alert(json.detail || 'Failed to fetch catalog products.');
      }
    } catch (err) {
      console.error('Error fetching products for simulation:', err);
      alert('Could not load products. Please check if your server is running.');
    }
  };

  const btnOpenSimulateOrderModal = document.getElementById('btnOpenSimulateOrderModal');
  if (btnOpenSimulateOrderModal) {
    btnOpenSimulateOrderModal.addEventListener('click', window.openSimulateOrderModal);
  }

  window.closeSimulateOrderModal = function() {
    const modal = document.getElementById('simulateOrderModal');
    if (modal) modal.style.display = 'none';
  };

  if (simulateOrderForm) {
    simulateOrderForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const selectEl = document.getElementById('simSelectProduct');
      const productId = selectEl ? selectEl.value : null;
      const unitsInput = document.getElementById('simUnitsInput');
      const units = unitsInput ? (parseInt(unitsInput.value, 10) || 1) : 1;

      if (!productId) {
        alert('Please select a product first.');
        return;
      }

      try {
        const res = await fetch(`/api/vendor/simulate-order?vendor_id=${storedVendorId}&product_id=${productId}&units=${units}`, {
          method: 'POST'
        });
        const json = await res.json();

        if (res.ok && json.success) {
          alert(json.message || 'Sale recorded successfully!');
          closeSimulateOrderModal();
          loadVendorDashboardData();
        } else {
          alert(json.detail || 'Failed to simulate sale.');
        }
      } catch (err) {
        alert('Server connection error while processing sale simulation.');
      }
    });
  }

  function getProductImageUrl(p) {
    if (!p) return 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200&auto=format&fit=crop';

    const rawUrl = (p.image_url || '').trim();
    const isDefaultFallback = rawUrl.includes('photo-1523275335684-37898b6baf30') || rawUrl.includes('photo-1505740420928-5e560c06d30e');

    // Use custom URL if provided and not an automatic default fallback
    if (rawUrl && !isDefaultFallback) {
      return rawUrl;
    }

    const name = (p.name || '').toLowerCase();
    const category = (p.category || '').toLowerCase();

    if (name.includes('volley') || name.includes('ball') || name.includes('football') || name.includes('soccer') || name.includes('basketball') || name.includes('tennis')) {
      return 'https://images.unsplash.com/photo-1612872087720-bb876e2e67d1?w=200&auto=format&fit=crop';
    }
    if (name.includes('watch') || name.includes('clock') || name.includes('smartwatch')) {
      return 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=200&auto=format&fit=crop';
    }
    if (name.includes('shoe') || name.includes('sneaker') || name.includes('boot') || name.includes('footwear') || name.includes('slipper')) {
      return 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200&auto=format&fit=crop';
    }
    if (name.includes('phone') || name.includes('mobile') || name.includes('iphone') || name.includes('android') || name.includes('smartphone')) {
      return 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=200&auto=format&fit=crop';
    }
    if (name.includes('laptop') || name.includes('computer') || name.includes('macbook') || name.includes('pc') || name.includes('notebook')) {
      return 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=200&auto=format&fit=crop';
    }
    if (name.includes('headphone') || name.includes('audio') || name.includes('earbud') || name.includes('speaker') || name.includes('headset')) {
      return 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200&auto=format&fit=crop';
    }
    if (name.includes('shirt') || name.includes('cloth') || name.includes('jacket') || name.includes('dress') || name.includes('pant') || name.includes('jean') || name.includes('t-shirt') || name.includes('apparel')) {
      return 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=200&auto=format&fit=crop';
    }
    if (name.includes('bag') || name.includes('backpack') || name.includes('wallet') || name.includes('purse')) {
      return 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=200&auto=format&fit=crop';
    }
    if (name.includes('perfume') || name.includes('cream') || name.includes('beauty') || name.includes('lotion') || name.includes('makeup') || name.includes('lipstick')) {
      return 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=200&auto=format&fit=crop';
    }
    if (name.includes('coffee') || name.includes('cup') || name.includes('mug') || name.includes('blender') || name.includes('kitchen') || name.includes('food')) {
      return 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=200&auto=format&fit=crop';
    }
    if (name.includes('book') || name.includes('novel') || name.includes('read')) {
      return 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=200&auto=format&fit=crop';
    }
    if (name.includes('toy') || name.includes('game') || name.includes('lego') || name.includes('puzzle')) {
      return 'https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?w=200&auto=format&fit=crop';
    }

    if (category.includes('sports') || category.includes('outdoors')) {
      return 'https://images.unsplash.com/photo-1517649763962-0c623266010b?w=200&auto=format&fit=crop';
    }
    if (category.includes('clothing') || category.includes('apparel')) {
      return 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=200&auto=format&fit=crop';
    }
    if (category.includes('home') || category.includes('kitchen')) {
      return 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=200&auto=format&fit=crop';
    }
    if (category.includes('beauty') || category.includes('personal')) {
      return 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=200&auto=format&fit=crop';
    }
    if (category.includes('food') || category.includes('beverage')) {
      return 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=200&auto=format&fit=crop';
    }
    if (category.includes('book') || category.includes('media')) {
      return 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=200&auto=format&fit=crop';
    }
    if (category.includes('toy') || category.includes('game')) {
      return 'https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?w=200&auto=format&fit=crop';
    }
    if (category.includes('electronics')) {
      return 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=200&auto=format&fit=crop';
    }

    return 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200&auto=format&fit=crop';
  }

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

  // Milestone 2 Interactive AI Hub Handlers
  window.loadMlForecasting = async function(days = 30) {
    ['btnFc30', 'btnFc60', 'btnFc90'].forEach(id => {
      const btn = document.getElementById(id);
      if (btn) btn.classList.remove('active');
    });
    const activeBtn = document.getElementById(`btnFc${days}`);
    if (activeBtn) activeBtn.classList.add('active');

    try {
      const res = await fetch(`/api/vendor/forecasting?vendor_id=${storedVendorId}&days=${days}`);
      const json = await res.json();
      if (res.ok && json.success) {
        const d = json.data;
        const vEl = document.getElementById('fcDailyVelocity');
        const pEl = document.getElementById('fcPredictedDemand');
        const sEl = document.getElementById('fcDaysToStockout');
        const rEl = document.getElementById('fcReorderQty');
        const mEl = document.getElementById('fcMessageNotice');

        if (vEl) vEl.textContent = `${d.daily_sales_velocity} units/day`;
        if (pEl) pEl.textContent = `${d.predicted_demand_units} units`;
        if (sEl) sEl.textContent = `${d.days_until_stockout} days`;
        if (rEl) rEl.textContent = `${d.recommended_reorder_qty} units`;
        if (mEl) mEl.textContent = `🤖 AI Prediction (${days} Days): ${d.message}`;
      }
    } catch (err) {
      console.error('Error loading ML forecasting:', err);
    }
  };

  window.testReviewSentiment = async function() {
    const inputEl = document.getElementById('reviewTestInput');
    const boxEl = document.getElementById('sentimentResultsBox');
    const text = inputEl ? inputEl.value.trim() : '';

    if (!text) {
      alert('Please enter review text to analyze.');
      return;
    }

    if (boxEl) boxEl.innerHTML = '<p style="color: #38bdf8;">Running LLM Sentiment Analysis pipeline...</p>';

    try {
      const res = await fetch(`/api/vendor/reviews/sentiment?reviews=${encodeURIComponent(text)}`, {
        method: 'POST'
      });
      const json = await res.json();
      if (res.ok && json.success) {
        const d = json.data;
        const overall = d.overall_sentiment || 'Neutral';
        const scorePct = Math.round((d.average_score || 0) * 100);
        const pros = d.top_pros || [];
        const cons = d.top_cons || [];

        boxEl.innerHTML = `
          <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; align-items: center; background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 12px;">
            <div>
              <div style="font-size: 0.8rem; color: #94a3b8;">Overall Sentiment</div>
              <div style="font-size: 1.3rem; font-weight: 800; color: ${overall === 'Positive' ? '#34d399' : (overall === 'Negative' ? '#f87171' : '#fbbf24')};">${overall}</div>
            </div>
            <div>
              <div style="font-size: 0.8rem; color: #94a3b8;">Satisfaction Score</div>
              <div style="font-size: 1.3rem; font-weight: 800; color: #38bdf8;">${scorePct}% Confidence</div>
            </div>
            <div>
              <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 4px;">Top Pros</div>
              <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                ${pros.map(p => `<span style="background: rgba(16,185,129,0.2); color: #34d399; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700;">+ ${escapeHtml(p)}</span>`).join('')}
              </div>
            </div>
            <div>
              <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 4px;">Top Cons</div>
              <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                ${cons.map(c => `<span style="background: rgba(239,68,68,0.2); color: #f87171; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700;">- ${escapeHtml(c)}</span>`).join('')}
              </div>
            </div>
          </div>
        `;
      }
    } catch (err) {
      if (boxEl) boxEl.innerHTML = '<p style="color: #f87171;">Failed to perform sentiment analysis.</p>';
    }
  };

  window.testVectorSearch = async function() {
    const inputEl = document.getElementById('vecQueryInput');
    const boxEl = document.getElementById('vectorSearchResultsBox');
    const query = inputEl ? inputEl.value.trim() : '';

    if (!query) {
      alert('Please enter a search term.');
      return;
    }

    if (boxEl) boxEl.innerHTML = '<p style="color: #a855f7;">Calculating text vector embeddings & cosine similarity...</p>';

    try {
      const res = await fetch(`/api/vendor/semantic-search?vendor_id=${storedVendorId}&query=${encodeURIComponent(query)}`);
      const json = await res.json();
      if (res.ok && json.success) {
        const results = json.results || [];
        if (results.length === 0) {
          boxEl.innerHTML = '<p style="color: #94a3b8;">No matching products found in vector space.</p>';
        } else {
          boxEl.innerHTML = `
            <div class="stats-grid" style="grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));">
              ${results.map(r => `
                <div class="stat-card" style="flex-direction: column; align-items: flex-start; gap: 0.75rem; border: 1px solid rgba(168, 85, 247, 0.3);">
                  <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                    <span class="category-badge">${escapeHtml(r.category)}</span>
                    <span style="background: rgba(168, 85, 247, 0.25); color: #c084fc; font-weight: 800; font-size: 0.75rem; padding: 2px 8px; border-radius: 99px;">
                      🎯 ${r.match_confidence} Cosine Match
                    </span>
                  </div>
                  <div style="display: flex; gap: 0.75rem; align-items: center;">
                    <img src="${r.image_url}" alt="${escapeHtml(r.name)}" style="width: 44px; height: 44px; border-radius: 8px; object-fit: cover;" onerror="this.src='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=150';" />
                    <div>
                      <h4 style="font-size: 0.95rem; font-weight: 800; color: #ffffff;">${escapeHtml(r.name)}</h4>
                      <span style="font-size: 0.85rem; font-weight: 800; color: #34d399;">$${Number(r.price).toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              `).join('')}
            </div>
          `;
        }
      }
    } catch (err) {
      if (boxEl) boxEl.innerHTML = '<p style="color: #f87171;">Failed to perform vector search.</p>';
    }
  };

  // Initial load
  const initialHash = window.location.hash.replace('#', '');
  if (initialHash === 'catalog') switchTab('catalog');
  else if (initialHash === 'add-product') switchTab('addProduct');
  else if (initialHash === 'm2-intelligence') switchTab('m2Intelligence');
  else if (initialHash === 'insights') switchTab('insights');
  else if (initialHash === 'profile') switchTab('profile');
  else switchTab('dashboard');
});
