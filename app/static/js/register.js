document.addEventListener('DOMContentLoaded', () => {
  const registerForm = document.getElementById('registerForm');
  const submitBtn = document.getElementById('registerSubmitBtn');
  const passwordInput = document.getElementById('regPasswordInput');
  const togglePasswordBtn = document.getElementById('regTogglePasswordBtn');
  const alertToast = document.getElementById('alertToast');
  const alertMessage = document.getElementById('alertMessage');

  // Password Eye Toggle
  if (togglePasswordBtn && passwordInput) {
    togglePasswordBtn.addEventListener('click', () => {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);

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
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
        `;
        togglePasswordBtn.setAttribute('title', 'Show password');
      }
    });
  }

  // Toast Helper
  function showAlert(msg, isSuccess = false) {
    if (!alertToast || !alertMessage) return;
    alertMessage.textContent = msg;
    alertToast.className = 'alert-toast visible ' + (isSuccess ? 'alert-toast-success' : 'alert-toast-error');
  }

  // Email Regex Validation Helper
  function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  // Form Submit Handler
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const fullName = document.getElementById('fullNameInput').value.trim();
      const businessName = document.getElementById('businessNameInput').value.trim();
      const email = document.getElementById('regEmailInput').value.trim();
      const password = passwordInput.value;
      const phoneNumber = document.getElementById('phoneInput').value.trim();
      const businessAddress = document.getElementById('addressInput').value.trim();

      // Validation Checks
      if (!fullName) {
        showAlert('Please enter your Full Name.');
        return;
      }
      if (!businessName) {
        showAlert('Please enter your Business Name.');
        return;
      }
      if (!email || !isValidEmail(email)) {
        showAlert('Please enter a valid Email Address (e.g. email@example.com).');
        return;
      }
      if (!password || password.length < 6) {
        showAlert('Password must be at least 6 characters long.');
        return;
      }

      submitBtn.disabled = true;
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Submitting Registration...';

      try {
        const response = await fetch('/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name: fullName,
            business_name: businessName,
            email: email,
            password: password,
            phone_number: phoneNumber || null,
            business_address: businessAddress || null
          })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          showAlert(data.message || 'Vendor Registration Successful! Redirecting to Login...', true);
          setTimeout(() => {
            window.location.href = '/login';
          }, 1500);
        } else {
          showAlert(data.detail || data.message || 'Registration failed. Please check your inputs.');
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
        }
      } catch (err) {
        showAlert('Server connection error. Please try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });
  }
});
