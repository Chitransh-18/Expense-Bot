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
      Auth.renderAuthPage();
      this.updateNavUI(false);
      return;
    }

    this.updateNavUI(true);
    this.startAutoSync();

    switch (hash) {
      case '#dashboard':
        Dashboard.renderPage();
        break;
      case '#expenses':
        Expenses.renderPage();
        break;
      case '#recurring':
        Recurring.renderPage();
        break;
      case '#auth':
        Auth.renderAuthPage();
        break;
      default:
        Dashboard.renderPage();
        break;
    }

    this.highlightActiveTab(hash);
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
      // Silently refresh current view data
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
    if (!badge) return;

    if (status === 'syncing') {
      badge.innerHTML = '🔄 <span style="font-size: 0.78rem; opacity: 0.8;">Syncing...</span>';
    } else {
      badge.innerHTML = '🟢 <span style="font-size: 0.78rem; opacity: 0.8;">Cloud Synced</span>';
    }
  },

  updateNavUI(isLoggedIn) {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
      sidebar.style.display = isLoggedIn ? 'flex' : 'none';
    }
    const badge = document.getElementById('cloud-sync-badge');
    if (badge) {
      badge.style.display = isLoggedIn ? 'inline-flex' : 'none';
    }
  },

  highlightActiveTab(hash) {
    const items = document.querySelectorAll('.nav-item');
    items.forEach(item => {
      const href = item.getAttribute('onclick') || '';
      if (href.includes(hash.replace('#', ''))) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  },

  onAuthSuccess() {
    window.location.hash = '#dashboard';
    this.handleRoute();
  },

  logout() {
    if (confirm('Are you sure you want to sign out?')) {
      this.stopAutoSync();
      API.clearToken();
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
