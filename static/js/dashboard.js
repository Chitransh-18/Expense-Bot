const Dashboard = {
  getTimeGreeting() {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return { text: 'Good morning', emoji: '🌅' };
    if (hour >= 12 && hour < 17) return { text: 'Good afternoon', emoji: '☀️' };
    if (hour >= 17 && hour < 21) return { text: 'Good evening', emoji: '🌇' };
    return { text: 'Good night', emoji: '🌙' };
  },

  async renderPage() {
    const container = document.getElementById('view-container');
    const user = API.getUser();
    const name = user ? user.full_name : 'Tracker';
    const greeting = this.getTimeGreeting();
    
    const todayFormatted = new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });

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
          <div style="font-size: 0.85rem; color: var(--cyan); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.2rem;">
            📅 ${todayFormatted}
          </div>
          <h2 class="page-title">${greeting.emoji} ${greeting.text}, ${name}!</h2>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Here is your financial status & recurring bill overview</p>
        </div>
        <div style="display: flex; gap: 0.8rem; flex-wrap: wrap;">
          <button class="btn btn-secondary" onclick="Dashboard.openMonthlyReportModal()">
            📊 Monthly Report
          </button>
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
                  <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, var(--primary), var(--cyan)); border-radius: 4px;"></div>
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
    
    if (typeof deferredPrompt !== 'undefined' && deferredPrompt) {
      const installBtn = document.getElementById('btn-install-app');
      if (installBtn) installBtn.style.display = 'inline-flex';
    }
  },

  async openMonthlyReportModal() {
    let monthExpenses = [];
    try {
      monthExpenses = await Expenses.fetchExpenses('this_month');
    } catch (err) {
      console.error('Error fetching monthly report:', err);
    }

    const currentMonthName = new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    const totalSpent = monthExpenses.reduce((sum, e) => sum + e.amount, 0);
    const personalSpent = monthExpenses.filter(e => e.expense_type === 'Personal').reduce((sum, e) => sum + e.amount, 0);
    const splitSpent = monthExpenses.filter(e => e.expense_type === 'Split').reduce((sum, e) => sum + e.amount, 0);

    const categories = {};
    monthExpenses.forEach(e => categories[e.category] = (categories[e.category] || 0) + e.amount);

    const topTransaction = monthExpenses.length ? monthExpenses.reduce((prev, current) => (prev.amount > current.amount) ? prev : current) : null;

    document.getElementById('modal-title').innerText = `📊 Monthly Expenditure Report`;
    document.getElementById('modal-body').innerHTML = `
      <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 0.85rem; color: var(--cyan); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
          Statement Period: ${currentMonthName}
        </div>
        <div style="background: rgba(10, 14, 26, 0.7); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: 1.2rem; margin-bottom: 1.2rem;">
          <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.2rem;">TOTAL EXPENDITURE</div>
          <div style="font-size: 2rem; font-weight: 800; color: var(--text-main);">₹${totalSpent.toLocaleString('en-IN')}</div>
          <div style="display: flex; gap: 1rem; font-size: 0.85rem; margin-top: 0.5rem;">
            <span>👤 Personal: <strong style="color: var(--primary);">₹${personalSpent.toLocaleString('en-IN')}</strong></span>
            <span>👥 Split: <strong style="color: var(--secondary);">₹${splitSpent.toLocaleString('en-IN')}</strong></span>
          </div>
        </div>

        ${topTransaction ? `
          <div style="background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: var(--radius-md); padding: 0.9rem 1.1rem; margin-bottom: 1.2rem;">
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Highest Single Transaction</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.3rem;">
              <div>
                <strong>${topTransaction.category}</strong>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${topTransaction.date} • ${topTransaction.payment_mode}</div>
              </div>
              <div style="font-size: 1.2rem; font-weight: 800; color: var(--cyan);">₹${topTransaction.amount.toLocaleString('en-IN')}</div>
            </div>
          </div>
        ` : ''}

        <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Monthly Category Breakdown</h4>
        ${Object.keys(categories).length ? Object.entries(categories).map(([cat, amt]) => {
          const pct = totalSpent > 0 ? ((amt / totalSpent) * 100).toFixed(0) : 0;
          return `
            <div style="margin-bottom: 0.8rem;">
              <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.2rem;">
                <span><strong>${cat}</strong></span>
                <span>₹${amt.toLocaleString('en-IN')} (${pct}%)</span>
              </div>
              <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden;">
                <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, var(--primary), var(--cyan)); border-radius: 3px;"></div>
              </div>
            </div>
          `;
        }).join('') : `<p style="color: var(--text-muted); font-size: 0.9rem;">No transactions recorded this month.</p>`}
      </div>

      <div style="display: flex; gap: 0.8rem;">
        <a href="/api/export/csv" class="btn btn-primary" style="flex: 1; text-align: center;" target="_blank" download>
          📄 Download Full CSV Statement
        </a>
      </div>
    `;
    App.openModal();
  }
};
