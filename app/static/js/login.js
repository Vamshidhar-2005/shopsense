document.addEventListener('DOMContentLoaded', () => {
  const vendorRoleBtn = document.getElementById('vendorRoleBtn');
  const adminRoleBtn = document.getElementById('adminRoleBtn');
  const loginSubmitBtn = document.getElementById('loginSubmitBtn');
  const passwordInput = document.getElementById('passwordInput');
  const togglePasswordBtn = document.getElementById('togglePasswordBtn');
  const loginForm = document.getElementById('loginForm');
  const alertToast = document.getElementById('alertToast');
  const alertMessage = document.getElementById('alertMessage');

  let currentRole = 'vendor'; // default role

  // Handle Role Selector Switches
  function setRole(role) {
    currentRole = role;
    if (role === 'vendor') {
      vendorRoleBtn.classList.add('active');
      adminRoleBtn.classList.remove('active');
      loginSubmitBtn.textContent = 'Sign in as Vendor';
    } else {
      adminRoleBtn.classList.add('active');
      vendorRoleBtn.classList.remove('active');
      loginSubmitBtn.textContent = 'Sign in as Admin';
    }
  }

  if (vendorRoleBtn && adminRoleBtn) {
    vendorRoleBtn.addEventListener('click', () => setRole('vendor'));
    adminRoleBtn.addEventListener('click', () => setRole('admin'));
  }

  // Password Eye Icon Show/Hide Toggle
  if (togglePasswordBtn && passwordInput) {
    togglePasswordBtn.addEventListener('click', () => {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);

      // Toggle Eye Icon SVG
      if (type === 'text') {
        togglePasswordBtn.innerHTML = `
          <svg viewBox="0 0 24 24">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
            <line x1="1" y1="1" x2="23" y2="23"></line>
          </svg>
        `;
        togglePasswordBtn.setAttribute('title', 'Hide password');
      } else {
        togglePasswordBtn.innerHTML = `
          <svg viewBox="0 0 24 24">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
        `;
        togglePasswordBtn.setAttribute('title', 'Show password');
      }
    });
  }

  // Toast notification helper
  function showAlert(msg, isSuccess = false) {
    if (!alertToast || !alertMessage) return;
    
    let displayMsg = msg;
    if (typeof msg === 'object') {
      if (Array.isArray(msg)) {
        displayMsg = msg.map(e => e.msg || JSON.stringify(e)).join(', ');
      } else {
        displayMsg = JSON.stringify(msg);
      }
    }

    alertMessage.textContent = displayMsg;
    alertToast.className = 'alert-toast visible ' + (isSuccess ? 'alert-toast-success' : 'alert-toast-error');
  }

  // Form Submit Handler
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const email = document.getElementById('emailInput').value.trim();
      const password = passwordInput.value;

      if (!email || !password) {
        showAlert('Please fill in all required fields.');
        return;
      }

      if (password.length < 6) {
        showAlert('Password must be at least 6 characters long.');
        return;
      }

      loginSubmitBtn.disabled = true;
      const originalText = loginSubmitBtn.textContent;
      loginSubmitBtn.textContent = 'Authenticating...';

      try {
        const response = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, role: currentRole })
        });

        let data = {};
        try {
          data = await response.json();
        } catch (jsonErr) {
          data = { detail: 'Server error. Please check server logs.' };
        }

        if (response.ok && data.success) {
          if (data.vendor_name) {
            sessionStorage.setItem('vendor_name', data.vendor_name);
          }
          if (data.vendor_id) {
            sessionStorage.setItem('vendor_id', data.vendor_id);
          }
          showAlert(data.message || 'Login successful! Redirecting...', true);
          setTimeout(() => {
            window.location.href = data.redirect_url || (currentRole === 'admin' ? '/admin/dashboard' : '/vendor/dashboard');
          }, 800);
        } else {
          const errorDetail = data.detail || data.message || 'Invalid email or password. Please try again.';
          showAlert(errorDetail, false);
          loginSubmitBtn.disabled = false;
          loginSubmitBtn.textContent = originalText;
        }
      } catch (err) {
        console.error('Login request error:', err);
        showAlert('Unable to reach server. Make sure server is running on http://localhost:8000', false);
        loginSubmitBtn.disabled = false;
        loginSubmitBtn.textContent = originalText;
      }
    });
  }
});
