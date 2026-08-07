const Auth = {
  renderAuthPage() {
    const mainContent = document.getElementById('view-container');
    mainContent.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: center; min-height: 80vh;">
        <div class="glass-card" style="width: 100%; max-width: 420px; padding: 2.5rem;">
          <div style="text-align: center; margin-bottom: 2rem;">
            <div class="brand-icon" style="width: 50px; height: 50px; margin: 0 auto 1rem auto; font-size: 1.8rem;">💰</div>
            <h2 style="font-size: 1.7rem; font-weight: 700; margin-bottom: 0.5rem;" id="auth-title">Welcome Back</h2>
            <p style="color: var(--text-muted); font-size: 0.95rem;" id="auth-subtitle">Sign in to manage your expenses & split bills</p>
          </div>

          <form id="auth-form" onsubmit="Auth.handleSubmit(event)">
            <div class="form-group" id="group-fullname" style="display: none;">
              <label class="form-label">Full Name</label>
              <input type="text" class="form-input" id="auth-fullname" placeholder="e.g. Chitransh Saxena" />
            </div>
            
            <div class="form-group">
              <label class="form-label">Email Address</label>
              <input type="email" class="form-input" id="auth-email" placeholder="name@example.com" required />
            </div>

            <div class="form-group">
              <label class="form-label">Password</label>
              <input type="password" class="form-input" id="auth-password" placeholder="••••••••" required />
            </div>

            <div id="auth-error" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 1rem; display: none;"></div>

            <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem;" id="auth-submit-btn">
              Sign In
            </button>
          </form>

          <div style="text-align: center; margin-top: 1.5rem; font-size: 0.9rem; color: var(--text-muted);">
            <span id="auth-toggle-text">Don't have an account?</span>
            <a href="#" onclick="Auth.toggleMode(event)" id="auth-toggle-link" style="color: var(--primary); font-weight: 600; text-decoration: none; margin-left: 0.3rem;">Sign Up</a>
          </div>
        </div>
      </div>
    `;
  },

  isRegistering: false,

  toggleMode(e) {
    if (e) e.preventDefault();
    this.isRegistering = !this.isRegistering;
    
    document.getElementById('auth-title').innerText = this.isRegistering ? 'Create Account' : 'Welcome Back';
    document.getElementById('auth-subtitle').innerText = this.isRegistering ? 'Sign up to start tracking expenses' : 'Sign in to manage your expenses & split bills';
    document.getElementById('group-fullname').style.display = this.isRegistering ? 'block' : 'none';
    document.getElementById('auth-submit-btn').innerText = this.isRegistering ? 'Sign Up' : 'Sign In';
    document.getElementById('auth-toggle-text').innerText = this.isRegistering ? 'Already have an account?' : "Don't have an account?";
    document.getElementById('auth-toggle-link').innerText = this.isRegistering ? 'Sign In' : 'Sign Up';
    document.getElementById('auth-error').style.display = 'none';
  },

  async handleSubmit(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    errorDiv.style.display = 'none';

    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    const fullName = document.getElementById('auth-fullname').value;

    const endpoint = this.isRegistering ? '/api/auth/register' : '/api/auth/login';
    const payload = this.isRegistering 
      ? { email, password, full_name: fullName }
      : { email, password };

    try {
      const res = await API.request(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (res.token) {
        API.setToken(res.token);
        API.setUser(res.user);
        App.onAuthSuccess();
      }
    } catch (err) {
      errorDiv.innerText = err.message || 'Authentication failed';
      errorDiv.style.display = 'block';
    }
  }
};
