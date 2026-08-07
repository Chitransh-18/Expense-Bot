const Dashboard = {
  async renderPage() {
    const container = document.getElementById('view-container');
    const user = API.getUser();
    
    let analytics = { total_spent: 0, personal_spent: 0, split_spent: 0, categories: {}, payment_modes: {}, total_count: 0 };
    let recurringBills = [];
    let recentExpenses = [];

    try {
      analytics = await API.request('/api/analytics');
      recurringBills = await Recurring.fetchBills();
      recentExpenses = await Expenses.fetchExpenses('all');
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    }

    const alertBanners = Recurring.renderAlertBanners(recurringBills);
    const top5Recent = recentExpenses.slice(0, 5);

    let html = `
      <div class="top-bar">
        <div>
          <h2 class="page-title">👋 Welcome back, ${user ? user.full_name : 'User'}!</h2>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Here is your financial summary & recurring bill alerts</p>
        </div>
        <div style="display: flex; gap: 0.8rem;">
          <button class="btn btn-secondary" id="btn-install-app" style="display: none;" onclick="triggerInstallApp()">
            📱 Install App
          </button>
          <button class="btn btn-primary" onclick="Expenses.openAddModal()">
            ➕ Log Expense
          </button>
        </div>
      </div>

      ${alertBanners}

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="glass-card stat-card">
          <span class="stat-label">Total Expense</span>
          <span class="stat-value">₹${analytics.total_spent.toLocaleString('en-IN')}</span>
          <span style="font-size: 0.8rem; color: var(--text-muted);">${analytics.total_count} transactions logged</span>
        </div>

        <div class="glass-card stat-card">
          <span class="stat-label">Personal Spent</span>
          <span class="stat-value" style="color: var(--primary);">₹${analytics.personal_spent.toLocaleString('en-IN')}</span>
          <span style="font-size: 0.8rem; color: var(--text-muted);">Solo expenses</span>
        </div>

        <div class="glass-card stat-card">
          <span class="stat-label">Split Spent</span>
          <span class="stat-value" style="color: var(--secondary);">₹${analytics.split_spent.toLocaleString('en-IN')}</span>
          <span style="font-size: 0.8rem; color: var(--text-muted);">Shared with friends</span>
        </div>

        <div class="glass-card stat-card">
          <span class="stat-label">Active Recurring</span>
          <span class="stat-value" style="color: var(--accent);">${recurringBills.length}</span>
          <span style="font-size: 0.8rem; color: var(--text-muted);">YouTube, Wi-Fi, Rent, etc.</span>
        </div>
      </div>

      <!-- Content Grid -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; margin-top: 1rem;">
        
        <!-- Recent Transactions -->
        <div class="glass-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem;">
            <h3 style="font-size: 1.1rem; font-weight: 600;">Recent Transactions</h3>
            <a href="#expenses" style="color: var(--primary); font-size: 0.85rem; font-weight: 600; text-decoration: none;">View All →</a>
          </div>

          ${top5Recent.length ? top5Recent.map(e => `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid var(--border-glass);">
              <div style="display: flex; align-items: center; gap: 0.8rem;">
                <div style="width: 38px; height: 38px; border-radius: var(--radius-md); background: rgba(99, 102, 241, 0.15); display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">
                  ${e.expense_type === 'Personal' ? '👤' : '👥'}
                </div>
                <div>
                  <div style="font-weight: 600; font-size: 0.95rem;">${e.category}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${e.date} • ${e.payment_mode} ${e.split_with ? `(Split with ${e.split_with})` : ''}</div>
                </div>
              </div>
              <div style="font-weight: 700; font-size: 1rem; color: var(--text-main);">
                ₹${e.amount.toLocaleString('en-IN')}
              </div>
            </div>
          `).join('') : `
            <div style="text-align: center; color: var(--text-muted); padding: 2rem 0;">
              No transactions recorded yet. Click "Log Expense" to begin!
            </div>
          `}
        </div>

        <!-- Category Breakdown -->
        <div class="glass-card">
          <h3 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 1.2rem;">Top Spending Categories</h3>
          ${Object.keys(analytics.categories).length ? Object.entries(analytics.categories).map(([cat, amt]) => {
            const pct = analytics.total_spent > 0 ? ((amt / analytics.total_spent) * 100).toFixed(0) : 0;
            return `
              <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 0.3rem;">
                  <span><strong>${cat}</strong></span>
                  <span style="color: var(--text-muted);">₹${amt.toLocaleString('en-IN')} (${pct}%)</span>
                </div>
                <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;">
                  <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, var(--primary), var(--accent)); border-radius: 4px;"></div>
                </div>
              </div>
            `;
          }).join('') : `
            <div style="text-align: center; color: var(--text-muted); padding: 2rem 0;">
              No category data available.
            </div>
          `}
        </div>

      </div>
    `;

    container.innerHTML = html;
    
    // Check PWA install button state
    if (typeof deferredPrompt !== 'undefined' && deferredPrompt) {
      const installBtn = document.getElementById('btn-install-app');
      if (installBtn) installBtn.style.display = 'inline-flex';
    }
  }
};
