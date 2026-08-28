const Auth = {
  currentEmail: '',
  currentFullName: '',
  currentOTP: '',
  step: 'email', // 'email', 'password', 'otp', 'set_password'
  devNotice: '',
  debugOTP: '',

  renderAuthPage() {
    const mainContent = document.getElementById('view-container');
    
    if (this.step === 'email') {
      mainContent.innerHTML = `
        <div class="auth-overlay">
          <div class="glass-card" style="width: 100%; max-width: 440px; padding: 2.8rem;">
            <div style="text-align: center; margin-bottom: 2.2rem;">
              <div class="brand-icon" style="width: 56px; height: 56px; margin: 0 auto 1.2rem auto; font-size: 1.8rem;">🔑</div>
              <h2 style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: -0.02em;">Welcome Back</h2>
              <p style="color: var(--text-muted); font-size: 0.95rem;">Enter your email address to sign in or register</p>
            </div>

            <form id="auth-email-form" onsubmit="Auth.handleCheckEmail(event)">
              <div class="form-group">
                <label class="form-label">Email Address</label>
                <input type="email" class="form-input" id="auth-email" placeholder="name@example.com" value="${this.currentEmail}" required autofocus />
              </div>

              <div id="auth-error" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 1rem; display: none;"></div>

              <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem;" id="check-email-btn">
                <span>Continue</span> →
              </button>
            </form>
          </div>
        </div>
      `;
    } else if (this.step === 'password') {
      mainContent.innerHTML = `
        <div class="auth-overlay">
          <div class="glass-card" style="width: 100%; max-width: 440px; padding: 2.8rem;">
            <div style="text-align: center; margin-bottom: 2rem;">
              <div class="brand-icon" style="width: 56px; height: 56px; margin: 0 auto 1.2rem auto; font-size: 1.8rem; background: linear-gradient(135deg, var(--primary), var(--cyan));">🔐</div>
              <h2 style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.3rem;">Welcome Back</h2>
              <p style="color: var(--cyan); font-weight: 600; font-size: 0.95rem; margin-bottom: 0.2rem;">${this.currentFullName || this.currentEmail}</p>
              <p style="color: var(--text-muted); font-size: 0.85rem;">${this.currentEmail}</p>
            </div>

            <form id="auth-password-form" onsubmit="Auth.handlePasswordLogin(event)">
              <div class="form-group">
                <label class="form-label">Password</label>
                <input type="password" class="form-input" id="auth-password" placeholder="Enter your password" required autofocus />
              </div>

              <div id="auth-error" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 1rem; display: none;"></div>

              <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem;" id="login-pwd-btn">
                ✅ Sign In
              </button>
            </form>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1.8rem; font-size: 0.88rem;">
              <a href="#" onclick="Auth.changeEmail(event)" style="color: var(--text-muted); text-decoration: none;">← Change Email</a>
              <a href="#" onclick="Auth.requestOTPForReset(event)" style="color: var(--cyan); text-decoration: none;">Forgot Password? Sign in via OTP</a>
            </div>
          </div>
        </div>
      `;
    } else if (this.step === 'otp') {
      mainContent.innerHTML = `
        <div class="auth-overlay">
          <div class="glass-card" style="width: 100%; max-width: 460px; padding: 2.8rem;">
            <div style="text-align: center; margin-bottom: 1.8rem;">
              <div class="brand-icon" style="width: 56px; height: 56px; margin: 0 auto 1.2rem auto; font-size: 1.8rem; background: linear-gradient(135deg, var(--cyan), var(--primary));">📲</div>
              <h2 style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem;">Enter Verification Code</h2>
              <p style="color: var(--text-muted); font-size: 0.95rem;">We sent a 6-digit OTP code to <strong style="color: var(--cyan);">${this.currentEmail}</strong></p>
            </div>

            ${this.debugOTP ? `
              <div style="background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.4); border-radius: var(--radius-md); padding: 0.9rem; text-align: center; margin-bottom: 1.5rem;">
                <span style="font-size: 0.85rem; color: var(--cyan); font-weight: 600;">Demo Mode OTP Code: <strong style="font-size: 1.2rem; letter-spacing: 3px; color: #fff;">${this.debugOTP}</strong></span>
              </div>
            ` : (this.devNotice ? `
              <div style="background: rgba(6, 182, 212, 0.12); border: 1px dashed rgba(6, 182, 212, 0.4); border-radius: var(--radius-md); padding: 0.8rem; text-align: center; margin-bottom: 1.5rem; font-size: 0.82rem; color: var(--cyan);">
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

              <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem;" id="verify-otp-btn">
                <span>Verify Code</span> →
              </button>
            </form>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1.8rem; font-size: 0.88rem;">
              <a href="#" onclick="Auth.changeEmail(event)" style="color: var(--text-muted); text-decoration: none;">← Change Email</a>
              <a href="#" onclick="Auth.resendOTP(event)" style="color: var(--primary); font-weight: 600; text-decoration: none;">Resend OTP</a>
            </div>
          </div>
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
    } else if (this.step === 'set_password') {
      mainContent.innerHTML = `
        <div class="auth-overlay">
          <div class="glass-card" style="width: 100%; max-width: 440px; padding: 2.8rem;">
            <div style="text-align: center; margin-bottom: 2rem;">
              <div class="brand-icon" style="width: 56px; height: 56px; margin: 0 auto 1.2rem auto; font-size: 1.8rem; background: linear-gradient(135deg, #10b981, var(--cyan));">🛡️</div>
              <h2 style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem;">Create Your Password</h2>
              <p style="color: var(--text-muted); font-size: 0.9rem;">Set a password for future fast logins without needing an OTP</p>
            </div>

            <form id="auth-set-pwd-form" onsubmit="Auth.handleSavePassword(event)">
              <div class="form-group">
                <label class="form-label">Full Name</label>
                <input type="text" class="form-input" id="auth-fullname" placeholder="e.g. Chitransh Saxena" value="${this.currentFullName}" required />
              </div>

              <div class="form-group">
                <label class="form-label">New Password</label>
                <input type="password" class="form-input" id="auth-new-password" placeholder="Min. 4 characters" minlength="4" required autofocus />
              </div>

              <div id="auth-error" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 1rem; display: none;"></div>

              <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem;" id="save-pwd-btn">
                🚀 Complete Registration & Sign In
              </button>
            </form>
          </div>
        </div>
      `;
    }
  },

  async handleCheckEmail(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    errorDiv.style.display = 'none';

    this.currentEmail = document.getElementById('auth-email').value.trim().toLowerCase();
    if (!this.currentEmail) return;

    try {
      const res = await API.request('/api/auth/check-user', {
        method: 'POST',
        body: JSON.stringify({ email: this.currentEmail })
      });

      this.currentFullName = res.full_name || '';

      if (res.exists && res.has_password) {
        // Registered user with password -> Show Password Form
        this.step = 'password';
        this.renderAuthPage();
      } else {
        // New user or missing password -> Send OTP for verification
        await this.sendOTP();
      }
    } catch (err) {
      errorDiv.innerText = err.message || 'Error checking user';
      errorDiv.style.display = 'block';
    }
  },

  async sendOTP() {
    try {
      const res = await API.request('/api/auth/send-otp', {
        method: 'POST',
        body: JSON.stringify({ email: this.currentEmail, full_name: this.currentFullName })
      });

      this.devNotice = res.dev_notice || '';
      this.debugOTP = res.otp_debug || '';
      this.step = 'otp';
      this.renderAuthPage();
    } catch (err) {
      const errorDiv = document.getElementById('auth-error');
      if (errorDiv) {
        errorDiv.innerText = err.message || 'Failed to send OTP code';
        errorDiv.style.display = 'block';
      }
    }
  },

  async handlePasswordLogin(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    errorDiv.style.display = 'none';

    const password = document.getElementById('auth-password').value.trim();
    if (!password) return;

    try {
      const res = await API.request('/api/auth/login-password', {
        method: 'POST',
        body: JSON.stringify({ email: this.currentEmail, password })
      });

      if (res.token) {
        API.setToken(res.token);
        API.setUser(res.user);
        this.step = 'email';
        App.onAuthSuccess();
      }
    } catch (err) {
      errorDiv.innerText = err.message || 'Invalid password';
      errorDiv.style.display = 'block';
    }
  },

  async handleVerifyOTP(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    errorDiv.style.display = 'none';

    const boxes = document.querySelectorAll('.otp-box');
    let otpCode = '';
    boxes.forEach(b => otpCode += b.value.trim());

    if (otpCode.length < 6) {
      errorDiv.innerText = 'Please enter all 6 digits of the OTP code';
      errorDiv.style.display = 'block';
      return;
    }

    this.currentOTP = otpCode;
    // Switch to set password step
    this.step = 'set_password';
    this.renderAuthPage();
  },

  async handleSavePassword(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    errorDiv.style.display = 'none';

    const fullname = document.getElementById('auth-fullname').value.trim();
    const password = document.getElementById('auth-new-password').value.trim();

    if (!password || password.length < 4) {
      errorDiv.innerText = 'Password must be at least 4 characters';
      errorDiv.style.display = 'block';
      return;
    }

    try {
      const res = await API.request('/api/auth/verify-otp-set-password', {
        method: 'POST',
        body: JSON.stringify({
          email: this.currentEmail,
          otp_code: this.currentOTP,
          password: password,
          full_name: fullname || this.currentFullName
        })
      });

      if (res.token) {
        API.setToken(res.token);
        API.setUser(res.user);
        this.step = 'email';
        App.onAuthSuccess();
      }
    } catch (err) {
      errorDiv.innerText = err.message || 'Registration failed. Check OTP code or try again.';
      errorDiv.style.display = 'block';
    }
  },

  requestOTPForReset(e) {
    e.preventDefault();
    this.sendOTP();
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
  },

  changeEmail(e) {
    e.preventDefault();
    this.step = 'email';
    this.renderAuthPage();
  },

  resendOTP(e) {
    e.preventDefault();
    this.sendOTP();
  }
};
