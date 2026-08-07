const Auth = {
  currentEmail: '',
  currentFullName: '',
  step: 'email', // 'email' or 'otp'
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
              <h2 style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: -0.02em;">OTP Verified Sign In</h2>
              <p style="color: var(--text-muted); font-size: 0.95rem;">Enter your email to receive a 6-digit OTP code</p>
            </div>

            <form id="auth-email-form" onsubmit="Auth.handleSendOTP(event)">
              <div class="form-group">
                <label class="form-label">Full Name (Optional for new users)</label>
                <input type="text" class="form-input" id="auth-fullname" placeholder="e.g. Chitransh Saxena" />
              </div>
              
              <div class="form-group">
                <label class="form-label">Email Address</label>
                <input type="email" class="form-input" id="auth-email" placeholder="name@example.com" value="${this.currentEmail}" required />
              </div>

              <div id="auth-error" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 1rem; display: none;"></div>

              <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem;" id="send-otp-btn">
                <span>Request OTP Code</span> →
              </button>
            </form>
          </div>
        </div>
      `;
    } else {
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
                ✅ Verify & Sign In
              </button>
            </form>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1.8rem; font-size: 0.88rem;">
              <a href="#" onclick="Auth.changeEmail(event)" style="color: var(--text-muted); text-decoration: none;">← Change Email</a>
              <a href="#" onclick="Auth.resendOTP(event)" style="color: var(--primary); font-weight: 600; text-decoration: none;">Resend OTP</a>
            </div>
          </div>
        </div>
      `;

      // Auto fill debug code if present for demo/testing convenience
      if (this.debugOTP) {
        setTimeout(() => {
          const boxes = document.querySelectorAll('.otp-box');
          for (let i = 0; i < 6 && i < this.debugOTP.length; i++) {
            if (boxes[i]) boxes[i].value = this.debugOTP[i];
          }
        }, 100);
      }
    }
  },

  async handleSendOTP(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    errorDiv.style.display = 'none';

    this.currentEmail = document.getElementById('auth-email').value.trim();
    this.currentFullName = document.getElementById('auth-fullname').value.trim();

    if (!this.currentEmail) return;

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
      errorDiv.innerText = err.message || 'Failed to send OTP code';
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

    try {
      const res = await API.request('/api/auth/verify-otp', {
        method: 'POST',
        body: JSON.stringify({
          email: this.currentEmail,
          otp_code: otpCode,
          full_name: this.currentFullName
        })
      });

      if (res.token) {
        API.setToken(res.token);
        API.setUser(res.user);
        this.step = 'email';
        App.onAuthSuccess();
      }
    } catch (err) {
      errorDiv.innerText = err.message || 'Verification failed. Check OTP code.';
      errorDiv.style.display = 'block';
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
  },

  changeEmail(e) {
    e.preventDefault();
    this.step = 'email';
    this.renderAuthPage();
  },

  resendOTP(e) {
    e.preventDefault();
    this.handleSendOTP(e);
  }
};
