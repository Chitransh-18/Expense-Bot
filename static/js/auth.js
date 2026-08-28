const Auth = {
  activeTab: 'login', // 'login', 'register', 'otp'
  regFullName: '',
  regUsername: '',
  regEmail: '',
  regPassword: '',
  devNotice: '',
  debugOTP: '',

  renderAuthPage() {
    const mainContent = document.getElementById('view-container');
    let formHTML = '';

    const tabHeaderHTML = `
      <div class="auth-tabs-header">
        <button class="auth-tab-btn ${this.activeTab === 'login' ? 'active' : ''}" onclick="Auth.switchTab('login')">
          👤 Sign In
        </button>
        <button class="auth-tab-btn ${this.activeTab === 'register' ? 'active' : ''}" onclick="Auth.switchTab('register')">
          ✨ Register
        </button>
      </div>
    `;

    if (this.activeTab === 'login') {
      formHTML = `
        ${tabHeaderHTML}

        <div style="text-align: left; margin-bottom: 1.5rem;">
          <h2 style="font-size: 1.7rem; font-weight: 800; margin-bottom: 0.4rem; color: #0f172a;">Sign In to Account</h2>
          <p style="color: var(--text-muted); font-size: 0.9rem;">Enter your Username (or Email) and Password</p>
        </div>

        <form id="auth-login-form" onsubmit="Auth.handleLogin(event)">
          <div class="form-group">
            <label class="form-label">Username or Email</label>
            <input type="text" class="form-input" id="login-identifier" placeholder="e.g. chitransh_18 or name@example.com" required autofocus />
          </div>

          <div class="form-group">
            <label class="form-label">Password</label>
            <input type="password" class="form-input" id="login-password" placeholder="Enter your password" required />
          </div>

          <div id="auth-error" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 1rem; display: none;"></div>

          <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.4rem; padding: 0.9rem;" id="btn-login-submit">
            ✅ Sign In
          </button>
        </form>

        <div style="text-align: center; margin-top: 1.8rem; font-size: 0.88rem; color: var(--text-muted);">
          New user? <a href="#" onclick="Auth.switchTab('register'); return false;" style="color: var(--cyan); font-weight: 700; text-decoration: none;">Create an account →</a>
        </div>
      `;
    } else if (this.activeTab === 'register') {
      formHTML = `
        ${tabHeaderHTML}

        <div style="text-align: left; margin-bottom: 1.4rem;">
          <h2 style="font-size: 1.7rem; font-weight: 800; margin-bottom: 0.4rem; color: #0f172a;">Create New Account</h2>
          <p style="color: var(--text-muted); font-size: 0.9rem;">Fill in your details to get started</p>
        </div>

        <form id="auth-register-form" onsubmit="Auth.handleRegisterSubmit(event)">
          <div class="form-group">
            <label class="form-label">Full Name</label>
            <input type="text" class="form-input" id="reg-fullname" placeholder="e.g. Chitransh Saxena" value="${this.regFullName}" required autofocus />
          </div>

          <div class="form-group">
            <label class="form-label">Choose Username</label>
            <input type="text" class="form-input" id="reg-username" placeholder="e.g. chitransh_18" value="${this.regUsername}" required />
            <span style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.2rem; display: block;">Letters, numbers, and '_' allowed</span>
          </div>

          <div class="form-group">
            <label class="form-label">Email Address</label>
            <input type="email" class="form-input" id="reg-email" placeholder="name@example.com" value="${this.regEmail}" required />
          </div>

          <div class="form-group">
            <label class="form-label">Password</label>
            <input type="password" class="form-input" id="reg-password" placeholder="Min. 4 characters" minlength="4" required />
          </div>

          <div id="auth-error" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 1rem; display: none;"></div>

          <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.4rem; padding: 0.9rem;" id="btn-register-submit">
            📩 Create Account & Send OTP
          </button>
        </form>

        <div style="text-align: center; margin-top: 1.5rem; font-size: 0.88rem; color: var(--text-muted);">
          Already have an account? <a href="#" onclick="Auth.switchTab('login'); return false;" style="color: var(--primary); font-weight: 700; text-decoration: none;">Sign In →</a>
        </div>
      `;
    } else if (this.activeTab === 'otp') {
      formHTML = `
        <div style="text-align: left; margin-bottom: 1.5rem;">
          <h2 style="font-size: 1.7rem; font-weight: 800; margin-bottom: 0.4rem; color: #0f172a;">Verify Email OTP</h2>
          <p style="color: var(--text-muted); font-size: 0.9rem;">Enter 6-digit OTP code sent to <strong style="color: #4f46e5;">${this.regEmail}</strong></p>
        </div>

        ${this.debugOTP ? `
          <div style="background: rgba(79, 70, 229, 0.08); border: 1px solid rgba(79, 70, 229, 0.25); border-radius: var(--radius-md); padding: 0.9rem; text-align: center; margin-bottom: 1.4rem;">
            <span style="font-size: 0.85rem; color: #4f46e5; font-weight: 600;">Demo Mode OTP Code: <strong style="font-size: 1.25rem; letter-spacing: 3px; color: #0f172a;">${this.debugOTP}</strong></span>
          </div>
        ` : (this.devNotice ? `
          <div style="background: rgba(79, 70, 229, 0.08); border: 1px dashed rgba(79, 70, 229, 0.3); border-radius: var(--radius-md); padding: 0.8rem; text-align: center; margin-bottom: 1.4rem; font-size: 0.82rem; color: #4f46e5;">
            💡 ${this.devNotice}
          </div>
        ` : '')}

        <form id="auth-otp-form" onsubmit="Auth.handleVerifyOTP(event)">
          <div class="otp-container" id="otp-inputs">
            <input type="text" maxlength="1" class="otp-box" autofocus oninput="Auth.handleDigitInput(this, 0)" onkeydown="Auth.handleKeyDown(event, 0)" />
            <input type="text" maxlength="1" class="otp-box" oninput="Auth.handleDigitInput(this, 1)" onkeydown="Auth.handleKeyDown(event, 1)" />
            <input type="text" maxlength="1" class="otp-box" oninput="Auth.handleDigitInput(this, 2)" onkeydown="Auth.handleKeyDown(event, 2)" />
            <input type="text" maxlength="1" class="otp-box" oninput="Auth.handleDigitInput(this, 3)" onkeydown="Auth.handleKeyDown(event, 3)" />
            <input type="text" maxlength="1" class="otp-box" oninput="Auth.handleDigitInput(this, 4)" onkeydown="Auth.handleKeyDown(event, 4)" />
            <input type="text" maxlength="1" class="otp-box" oninput="Auth.handleDigitInput(this, 5)" onkeydown="Auth.handleKeyDown(event, 5)" />
          </div>

          <div id="auth-error" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 1rem; text-align: center; display: none;"></div>

          <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem; padding: 0.95rem;" id="btn-verify-otp">
            🚀 Complete Registration & Sign In
          </button>
        </form>

        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1.8rem; font-size: 0.88rem;">
          <a href="#" onclick="Auth.switchTab('register'); return false;" style="color: var(--text-muted); text-decoration: none;">← Back to Form</a>
          <a href="#" onclick="Auth.resendOTP(event); return false;" style="color: var(--primary); font-weight: 700; text-decoration: none;">Resend OTP</a>
        </div>
      `;

      if (this.debugOTP) {
        setTimeout(() => {
          const boxes = document.querySelectorAll('.otp-box');
          for (let i = 0; i < 6 && i < this.debugOTP.length; i++) {
            if (boxes[i]) boxes[i].value = this.debugOTP[i];
          }
        }, 100);
      }
    }

    mainContent.innerHTML = `
      <div class="auth-overlay">
        <div class="auth-split-wrapper">
          
          <!-- Left Panel: Hero Showcase -->
          <div class="auth-hero-panel">
            <div>
              <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 3rem;">
                <div class="brand-icon" style="width: 48px; height: 48px; font-size: 1.6rem;">💰</div>
                <span style="font-size: 1.6rem; font-weight: 800; color: #0f172a; letter-spacing: -0.03em;">ExpenseTracker</span>
              </div>

              <h1 style="font-size: 2.2rem; font-weight: 800; line-height: 1.25; margin-bottom: 1.2rem; color: #0f172a; letter-spacing: -0.03em;">
                Smart Expense Tracking & <span style="background: linear-gradient(135deg, #ff6b6b, #ff8e53); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Split Manager</span>
              </h1>
              <p style="color: var(--text-muted); font-size: 0.98rem; line-height: 1.6; margin-bottom: 2.2rem;">
                Log personal expenses, split recurring monthly bills (YouTube Premium, Wi-Fi, Rent), and sync real-time across your Phone and Laptop.
              </p>

              <div style="display: flex; flex-direction: column; gap: 1.1rem;">
                <div style="display: flex; align-items: center; gap: 0.9rem;">
                  <span style="font-size: 1.2rem; background: rgba(16,185,129,0.12); padding: 0.4rem; border-radius: 8px;">👤</span>
                  <div>
                    <strong style="color: #0f172a; font-size: 0.92rem; display: block;">Unique Usernames</strong>
                    <span style="color: var(--text-muted); font-size: 0.82rem;">Sign in instantly with Username & Password</span>
                  </div>
                </div>
                <div style="display: flex; align-items: center; gap: 0.9rem;">
                  <span style="font-size: 1.2rem; background: rgba(79,70,229,0.12); padding: 0.4rem; border-radius: 8px;">📱</span>
                  <div>
                    <strong style="color: #0f172a; font-size: 0.92rem; display: block;">Installable PWA App</strong>
                    <span style="color: var(--text-muted); font-size: 0.82rem;">Install on iOS & Android in 1 tap</span>
                  </div>
                </div>
                <div style="display: flex; align-items: center; gap: 0.9rem;">
                  <span style="font-size: 1.2rem; background: rgba(255,107,107,0.12); padding: 0.4rem; border-radius: 8px;">🔄</span>
                  <div>
                    <strong style="color: #0f172a; font-size: 0.92rem; display: block;">Real-Time Cloud Sync</strong>
                    <span style="color: var(--text-muted); font-size: 0.82rem;">Phone entries instantly sync to laptop</span>
                  </div>
                </div>
              </div>
            </div>

            <div style="color: var(--text-dim); font-size: 0.82rem; border-top: 1px solid var(--border-glass); padding-top: 1.2rem; margin-top: 2rem;">
              Protected by 256-bit Encryption • ExpenseTracker Pro 2.0
            </div>
          </div>

          <!-- Right Panel: Form Card -->
          <div class="auth-form-panel">
            ${formHTML}
          </div>

        </div>
      </div>
    `;
  },

  switchTab(tab) {
    this.activeTab = tab;
    this.renderAuthPage();
  },

  async handleLogin(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    if (errorDiv) errorDiv.style.display = 'none';

    const username_or_email = document.getElementById('login-identifier').value.trim();
    const password = document.getElementById('login-password').value.trim();

    if (!username_or_email || !password) return;

    try {
      const res = await API.request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username_or_email, password })
      });

      if (res.token) {
        API.setToken(res.token);
        API.setUser(res.user);
        App.onAuthSuccess();
      }
    } catch (err) {
      if (errorDiv) {
        errorDiv.innerText = err.message || 'Invalid username/email or password';
        errorDiv.style.display = 'block';
      }
    }
  },

  async handleRegisterSubmit(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    if (errorDiv) errorDiv.style.display = 'none';

    this.regFullName = document.getElementById('reg-fullname').value.trim();
    this.regUsername = document.getElementById('reg-username').value.trim();
    this.regEmail = document.getElementById('reg-email').value.trim().toLowerCase();
    this.regPassword = document.getElementById('reg-password').value.trim();

    if (!this.regFullName || !this.regUsername || !this.regEmail || !this.regPassword) return;

    try {
      const res = await API.request('/api/auth/register-send-otp', {
        method: 'POST',
        body: JSON.stringify({
          full_name: this.regFullName,
          username: this.regUsername,
          email: this.regEmail,
          password: this.regPassword
        })
      });

      this.devNotice = res.dev_notice || '';
      this.debugOTP = res.otp_debug || '';
      this.activeTab = 'otp';
      this.renderAuthPage();
    } catch (err) {
      if (errorDiv) {
        errorDiv.innerText = err.message || 'Registration failed';
        errorDiv.style.display = 'block';
      }
    }
  },

  async handleVerifyOTP(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    if (errorDiv) errorDiv.style.display = 'none';

    const boxes = document.querySelectorAll('.otp-box');
    let otpCode = '';
    boxes.forEach(b => otpCode += b.value.trim());

    if (otpCode.length < 6) {
      if (errorDiv) {
        errorDiv.innerText = 'Please enter all 6 digits of the OTP code';
        errorDiv.style.display = 'block';
      }
      return;
    }

    try {
      const res = await API.request('/api/auth/register-verify-otp', {
        method: 'POST',
        body: JSON.stringify({
          full_name: this.regFullName,
          username: this.regUsername,
          email: this.regEmail,
          password: this.regPassword,
          otp_code: otpCode
        })
      });

      if (res.token) {
        API.setToken(res.token);
        API.setUser(res.user);
        App.onAuthSuccess();
      }
    } catch (err) {
      if (errorDiv) {
        errorDiv.innerText = err.message || 'Invalid or expired OTP code';
        errorDiv.style.display = 'block';
      }
    }
  },

  async resendOTP(e) {
    if (e) e.preventDefault();
    try {
      const res = await API.request('/api/auth/register-send-otp', {
        method: 'POST',
        body: JSON.stringify({
          full_name: this.regFullName,
          username: this.regUsername,
          email: this.regEmail,
          password: this.regPassword
        })
      });

      this.devNotice = res.dev_notice || '';
      this.debugOTP = res.otp_debug || '';
      alert(`OTP resent to ${this.regEmail}`);
      this.renderAuthPage();
    } catch (err) {
      alert(err.message || 'Failed to resend OTP');
    }
  },

  handleDigitInput(input, index) {
    if (input.value.length === 1 && index < 5) {
      const nextInput = document.querySelectorAll('.otp-box')[index + 1];
      if (nextInput) nextInput.focus();
    }
  },

  handleKeyDown(e, index) {
    if (e.key === 'Backspace' && !e.target.value && index > 0) {
      const prevInput = document.querySelectorAll('.otp-box')[index - 1];
      if (prevInput) {
        prevInput.focus();
        prevInput.value = '';
      }
    }
  }
};
