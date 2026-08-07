const App = {
  init() {
    window.addEventListener('hashchange', () => this.handleRoute());
    this.handleRoute();
  },

  handleRoute() {
    const hash = window.location.hash || '#dashboard';
    const user = API.getUser();
    const token = API.getToken();

    if (!token || !user) {
      Auth.renderAuthPage();
      this.updateNavUI(false);
      return;
    }

    this.updateNavUI(true);

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

  updateNavUI(isLoggedIn) {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
      sidebar.style.display = isLoggedIn ? 'flex' : 'none';
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
