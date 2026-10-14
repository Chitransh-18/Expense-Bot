// Checklist Items 13 & 14: Modern Toast Notification System
const Toast = {
  show(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => toast.classList.add('toast-show'), 10);

    setTimeout(() => {
      toast.classList.remove('toast-show');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
};

const App = {
  syncTimer: null,
  isSyncing: false,

  init() {
    window.addEventListener('hashchange', () => this.handleRoute());
    
    // Auto-sync triggers when window regains focus or tab becomes visible
    window.addEventListener('focus', () => this.triggerAutoSync());
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        this.triggerAutoSync();
      }
    });

    this.handleRoute();
  },

  handleRoute() {
    const hash = window.location.hash || '#dashboard';
    const user = API.getUser();
    const token = API.getToken();

    if (!token || !user) {
      this.stopAutoSync();
      document.title = 'Sign In | ExpenseTracker Pro';
      Auth.renderAuthPage();
      this.updateNavUI(false);
      return;
    }

    this.updateNavUI(true);
    this.startAutoSync();

    switch (hash) {
      case '#dashboard':
      case '':
        document.title = 'Dashboard | ExpenseTracker Pro';
        Dashboard.renderPage();
        break;
      case '#expenses':
        document.title = 'Expenses | ExpenseTracker Pro';
        Expenses.renderPage();
        break;
      case '#recurring':
        document.title = 'Recurring Bills | ExpenseTracker Pro';
        Recurring.renderPage();
        break;
      case '#support':
        this.openSupportModal();
        break;
      case '#auth':
        document.title = 'Sign In | ExpenseTracker Pro';
        Auth.renderAuthPage();
        break;
      default:
        // Checklist Item 15: Clean 404 fallback page
        document.title = '404 - Page Not Found | ExpenseTracker Pro';
        this.render404Page();
        break;
    }

    this.highlightActiveTab(hash);
  },

  render404Page() {
    const container = document.getElementById('view-container');
    if (!container) return;

    container.innerHTML = `
      <div class="glass-card empty-state-card" style="margin-top: 3rem;">
        <div class="empty-state-icon">🧭</div>
        <h2 class="empty-state-title">404 - Page Not Found</h2>
        <p class="empty-state-desc">
          Oops! The financial view or page you are looking for doesn't exist or has moved.
        </p>
        <button class="btn btn-primary" onclick="window.location.hash='#dashboard'">
          📊 Back to Dashboard
        </button>
      </div>
    `;
  },

  startAutoSync() {
    if (this.syncTimer) return;
    // Auto background sync every 12 seconds
    this.syncTimer = setInterval(() => {
      this.triggerAutoSync();
    }, 12000);
  },

  stopAutoSync() {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
  },

  async triggerAutoSync() {
    const token = API.getToken();
    if (!token || this.isSyncing) return;

    this.isSyncing = true;
    this.setSyncBadgeStatus('syncing');

    try {
      const hash = window.location.hash || '#dashboard';
      if (hash === '#dashboard' || hash === '') {
        await Dashboard.renderPage();
      } else if (hash === '#expenses') {
        await Expenses.renderPage();
      } else if (hash === '#recurring') {
        await Recurring.renderPage();
      }
      this.setSyncBadgeStatus('synced');
    } catch (err) {
      console.warn('Background sync warning:', err);
      this.setSyncBadgeStatus('synced');
    } finally {
      this.isSyncing = false;
    }
  },

  setSyncBadgeStatus(status) {
    const badge = document.getElementById('cloud-sync-badge');
    const mobileBadge = document.getElementById('mobile-cloud-sync');

    if (badge) {
      badge.innerHTML = status === 'syncing'
        ? '🔄 <span style="font-size: 0.78rem; opacity: 0.8;">Syncing...</span>'
        : '🟢 <span style="font-size: 0.78rem; opacity: 0.8; font-weight: 600;">Cloud Synced</span>';
    }

    if (mobileBadge) {
      mobileBadge.innerHTML = status === 'syncing' ? '🔄 Syncing' : '🟢 Live';
    }
  },

  updateNavUI(isLoggedIn) {
    const sidebar = document.querySelector('.sidebar');
    const mobileTopBar = document.getElementById('mobile-top-bar');
    const mobileBottomNav = document.getElementById('mobile-bottom-nav');
    const badge = document.getElementById('cloud-sync-badge');

    if (sidebar) sidebar.style.display = isLoggedIn ? 'flex' : 'none';
    if (mobileTopBar) mobileTopBar.style.display = isLoggedIn ? 'flex' : 'none';
    if (mobileBottomNav) mobileBottomNav.style.display = isLoggedIn ? 'flex' : 'none';
    if (badge) badge.style.display = isLoggedIn ? 'inline-flex' : 'none';
  },

  highlightActiveTab(hash) {
    const cleanHash = (hash || '#dashboard').replace('#', '');
    
    // Desktop sidebar
    const items = document.querySelectorAll('.nav-item');
    items.forEach(item => {
      const href = item.getAttribute('onclick') || '';
      if (href.includes(cleanHash)) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    // Mobile bottom bar
    const bottomItems = document.querySelectorAll('.bottom-nav-item');
    bottomItems.forEach(item => {
      if (item.id === `mob-nav-${cleanHash}`) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  },

  // Checklist Items 6 & 16: Clickable Email and Phone Support Modal
  openSupportModal() {
    document.getElementById('modal-title').innerText = '💬 Help & Contact Support';
    document.getElementById('modal-body').innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1.2rem;">
        <div>
          <h4 style="font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-bottom: 0.3rem;">We are here to help!</h4>
          <p style="color: var(--text-muted); font-size: 0.9rem; line-height: 1.5;">
            Need help splitting a bill, configuring your cloud database, or reporting an issue? Reach out directly:
          </p>
        </div>

        <div class="support-contact-grid">
          <!-- Clickable Email (Checklist Item 6) -->
          <a href="mailto:chitranshsaxena85@gmail.com?subject=ExpenseTracker%20Support%20Inquiry" class="support-contact-card">
            <span style="font-size: 1.5rem;">📧</span>
            <strong style="font-size: 0.9rem;">Email Support</strong>
            <span style="font-size: 0.78rem; color: var(--cyan); word-break: break-all;">chitranshsaxena85@gmail.com</span>
          </a>

          <!-- Clickable WhatsApp (Checklist Item 16) -->
          <a href="https://wa.me/919876543210?text=Hi%20Chitransh,%20I%20have%20a%20question%20about%20ExpenseTracker%20Pro" target="_blank" class="support-contact-card">
            <span style="font-size: 1.5rem;">📲</span>
            <strong style="font-size: 0.9rem;">WhatsApp Chat</strong>
            <span style="font-size: 0.78rem; color: #10b981;">Chat with Developer</span>
          </a>

          <!-- Clickable Phone Call (Checklist Item 16) -->
          <a href="tel:+919876543210" class="support-contact-card">
            <span style="font-size: 1.5rem;">📞</span>
            <strong style="font-size: 0.9rem;">Direct Phone</strong>
            <span style="font-size: 0.78rem; color: var(--text-muted);">+91 98765 43210</span>
          </a>

          <!-- Mobile App Guide -->
          <div class="support-contact-card" onclick="App.openInstallHelpModal();" style="cursor: pointer;">
            <span style="font-size: 1.5rem;">📱</span>
            <strong style="font-size: 0.9rem;">Install on Phone</strong>
            <span style="font-size: 0.78rem; color: var(--secondary);">iOS & Android PWA</span>
          </div>
        </div>

        <div style="background: rgba(15, 23, 42, 0.03); border-radius: var(--radius-sm); padding: 0.8rem; font-size: 0.8rem; color: var(--text-muted); text-align: center;">
          ExpenseTracker Pro v2.5 • Developed by Chitransh Saxena
        </div>

        <button class="btn btn-secondary" onclick="App.closeModal()" style="width: 100%;">
          Close
        </button>
      </div>
    `;
    this.openModal();
  },

  openInstallHelpModal() {
    document.getElementById('modal-title').innerText = '📱 Install App on Your Phone';
    document.getElementById('modal-body').innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1.4rem;">
        
        <!-- Android Chrome Guide -->
        <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: var(--radius-md); padding: 1.2rem;">
          <h4 style="color: #10b981; margin-bottom: 0.6rem; display: flex; align-items: center; gap: 0.5rem;">
            <span>🤖</span> Android (Google Chrome)
          </h4>
          <ol style="color: var(--text-main); font-size: 0.9rem; line-height: 1.6; padding-left: 1.2rem; margin: 0;">
            <li>Open <strong>https://expense-bot-1-jyl4.onrender.com</strong> in Chrome.</li>
            <li>Tap the <strong>"📱 Install App"</strong> button inside the menu.</li>
            <li>Or tap Chrome's top-right <strong>⋮ (Three Dots)</strong> ➔ Select <strong>Add to Home screen</strong>.</li>
          </ol>
        </div>

        <!-- iPhone Safari Guide -->
        <div style="background: rgba(79, 70, 229, 0.08); border: 1px solid rgba(79, 70, 229, 0.25); border-radius: var(--radius-md); padding: 1.2rem;">
          <h4 style="color: #4f46e5; margin-bottom: 0.6rem; display: flex; align-items: center; gap: 0.5rem;">
            <span>🍏</span> iPhone / iPad (Apple Safari)
          </h4>
          <ol style="color: var(--text-main); font-size: 0.9rem; line-height: 1.6; padding-left: 1.2rem; margin: 0;">
            <li>Open <strong>https://expense-bot-1-jyl4.onrender.com</strong> in Apple Safari.</li>
            <li>Tap the <strong>Share icon</strong> at the bottom bar (box with up arrow ⎋).</li>
            <li>Scroll down and tap <strong>Add to Home Screen (+)</strong>.</li>
            <li>Tap <strong>Add</strong> in the top-right corner.</li>
          </ol>
        </div>

        <button class="btn btn-primary" onclick="App.closeModal()" style="width: 100%;">
          Got It!
        </button>
      </div>
    `;
    this.openModal();
  },

  onAuthSuccess() {
    Toast.show('🎉 Welcome to ExpenseTracker Pro!', 'success');
    window.location.hash = '#dashboard';
    this.handleRoute();
  },

  logout() {
    if (confirm('Are you sure you want to sign out?')) {
      this.stopAutoSync();
      API.clearToken();
      Toast.show('You have been signed out.', 'info');
      window.location.hash = '#auth';
      this.handleRoute();
    }
  },

  openModal() {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) overlay.classList.add('active');
  },

  closeModal() {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) overlay.classList.remove('active');
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
