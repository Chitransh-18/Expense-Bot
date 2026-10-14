const Dashboard = {
  isRecording: false,
  recognition: null,

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
          <div style="font-size: 0.82rem; color: #4f46e5; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.4rem;">
            📅 ${todayFormatted}
          </div>
          <h2 class="page-title">${greeting.emoji} ${greeting.text}, ${name}!</h2>
          <p style="color: var(--text-muted); font-size: 0.98rem; margin-top: 0.2rem;">Here is your financial status & recurring bill overview</p>
        </div>
        <div style="display: flex; gap: 0.8rem; align-items: center; flex-wrap: wrap;">
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

      <!-- ⚡ Core USP: Natural Language AI Quick-Add Bar (English, Hindi & Hinglish) -->
      <div class="ai-magic-card">
        <div class="ai-magic-header">
          <div class="ai-badge">
            <span>✨</span> AI Natural Language Quick Log
          </div>
          <span style="font-size: 0.78rem; color: var(--text-muted);">
            Type or speak in English, Hindi, or Hinglish
          </span>
        </div>

        <div class="ai-input-group">
          <input 
            type="text" 
            id="dashboard-nlp-input" 
            class="ai-magic-input" 
            placeholder="e.g. 'Dinner 540 with Daksh split via UPI' or 'Chai nashta 60 cash kal'..."
            onkeydown="if(event.key === 'Enter') Dashboard.handleQuickAdd()"
            autocomplete="off"
          />
          <button 
            type="button" 
            class="ai-mic-btn" 
            id="btn-dashboard-mic" 
            onclick="Dashboard.toggleSpeechRecognition('dashboard-nlp-input', 'btn-dashboard-mic')"
            title="Voice Speech-to-Text"
          >
            🎙️
          </button>
          <button 
            type="button" 
            class="btn btn-primary" 
            id="btn-dashboard-quick-add"
            onclick="Dashboard.handleQuickAdd()"
          >
            ⚡ Quick Log
          </button>
        </div>

        <div class="ai-suggestions-row">
          <span style="font-size: 0.76rem; color: var(--text-muted); font-weight: 600;">Try:</span>
          <span class="ai-pill" onclick="Dashboard.fillQuickInput('Dinner 540 with Daksh split via UPI')">"Dinner 540 with Daksh split via UPI"</span>
          <span class="ai-pill" onclick="Dashboard.fillQuickInput('Uber cab 250 cash kal')">"Uber cab 250 cash kal"</span>
          <span class="ai-pill" onclick="Dashboard.fillQuickInput('Chai nashta 80 GPay')">"Chai nashta 80 GPay"</span>
          <span class="ai-pill" onclick="Dashboard.fillQuickInput('Bijli ka bill 1500 online bhara')">"Bijli ka bill 1500 online"</span>
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
            <h3 style="font-size: 1.1rem; font-weight: 700;">Recent Transactions</h3>
            <a href="#expenses" style="color: var(--primary); font-size: 0.85rem; font-weight: 700; text-decoration: none;">View All →</a>
          </div>

          ${top5Recent.length ? top5Recent.map(e => `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid var(--border-glass);">
              <div style="display: flex; align-items: center; gap: 0.8rem;">
                <div style="width: 38px; height: 38px; border-radius: var(--radius-md); background: rgba(255, 107, 107, 0.12); display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">
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
            <!-- Checklist Item 11: Illustrated Empty State -->
            <div class="empty-state-card" style="padding: 2.2rem 1rem;">
              <div class="empty-state-icon" style="font-size: 2.5rem;">💸</div>
              <h4 class="empty-state-title" style="font-size: 1.05rem;">No transactions recorded yet</h4>
              <p class="empty-state-desc" style="font-size: 0.85rem;">
                Use the AI Quick Log bar above or click below to record your first expense!
              </p>
              <button class="btn btn-primary btn-sm" onclick="Expenses.openAddModal()">
                ➕ Log First Expense
              </button>
            </div>
          `}
        </div>

        <!-- Category Breakdown -->
        <div class="glass-card">
          <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1.2rem;">Top Spending Categories</h3>
          ${Object.keys(analytics.categories).length ? Object.entries(analytics.categories).map(([cat, amt]) => {
            const pct = analytics.total_spent > 0 ? ((amt / analytics.total_spent) * 100).toFixed(0) : 0;
            return `
              <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 0.3rem;">
                  <span><strong>${cat}</strong></span>
                  <span style="color: var(--text-muted);">₹${amt.toLocaleString('en-IN')} (${pct}%)</span>
                </div>
                <div style="width: 100%; height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden;">
                  <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, #ff6b6b, #ff8e53); border-radius: 4px;"></div>
                </div>
              </div>
            `;
          }).join('') : `
            <!-- Checklist Item 11: Category Empty State -->
            <div class="empty-state-card" style="padding: 2.2rem 1rem;">
              <div class="empty-state-icon" style="font-size: 2.5rem;">📊</div>
              <h4 class="empty-state-title" style="font-size: 1.05rem;">No category data</h4>
              <p class="empty-state-desc" style="font-size: 0.85rem;">
                Category breakdowns will visualize automatically as you record spending.
              </p>
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

  fillQuickInput(text) {
    const input = document.getElementById('dashboard-nlp-input');
    if (input) {
      input.value = text;
      input.focus();
    }
  },

  async handleQuickAdd() {
    const input = document.getElementById('dashboard-nlp-input');
    const btn = document.getElementById('btn-dashboard-quick-add');
    if (!input) return;

    const text = input.value.trim();
    if (!text) {
      Toast.show('Please type an expense like "Dinner 540 with Daksh"', 'error');
      input.focus();
      return;
    }

    if (btn) {
      btn.disabled = true;
      btn.innerText = '⚡ Logging...';
    }

    try {
      const res = await API.request('/api/expenses/quick-add', {
        method: 'POST',
        body: JSON.stringify({ text })
      });

      Toast.show(res.message || '🎉 Expense recorded successfully!', 'success');
      input.value = '';
      this.renderPage();
    } catch (err) {
      Toast.show(err.message || 'Could not parse expense. Please try again.', 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerText = '⚡ Quick Log';
      }
    }
  },

  toggleSpeechRecognition(inputId, btnId) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      Toast.show('Speech recognition is not supported in this browser. Please type your message.', 'error');
      return;
    }

    const input = document.getElementById(inputId);
    const btn = document.getElementById(btnId);

    if (this.isRecording && this.recognition) {
      this.recognition.stop();
      this.isRecording = false;
      if (btn) btn.classList.remove('listening');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.lang = 'en-IN'; // English (India) - handles Indian accents & Hinglish well
    this.recognition.interimResults = false;
    this.recognition.maxAlternatives = 1;

    this.recognition.onstart = () => {
      this.isRecording = true;
      if (btn) btn.classList.add('listening');
      Toast.show('🎙️ Listening... Speak your expense now!', 'info');
    };

    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (input) {
        input.value = transcript;
        Toast.show(`Heard: "${transcript}"`, 'info');
        // Auto trigger quick add
        Dashboard.handleQuickAdd();
      }
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      Toast.show(`Voice input: ${event.error}`, 'error');
      this.isRecording = false;
      if (btn) btn.classList.remove('listening');
    };

    this.recognition.onend = () => {
      this.isRecording = false;
      if (btn) btn.classList.remove('listening');
    };

    this.recognition.start();
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
        <div style="font-size: 0.85rem; color: #4f46e5; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
          Statement Period: ${currentMonthName}
        </div>
        <div style="background: #f8fafc; border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: 1.2rem; margin-bottom: 1.2rem;">
          <div style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.2rem; font-weight: 600;">TOTAL EXPENDITURE</div>
          <div style="font-size: 2rem; font-weight: 800; color: #0f172a;">₹${totalSpent.toLocaleString('en-IN')}</div>
          <div style="display: flex; gap: 1rem; font-size: 0.85rem; margin-top: 0.5rem;">
            <span>👤 Personal: <strong style="color: var(--primary);">₹${personalSpent.toLocaleString('en-IN')}</strong></span>
            <span>👥 Split: <strong style="color: var(--secondary);">₹${splitSpent.toLocaleString('en-IN')}</strong></span>
          </div>
        </div>

        ${topTransaction ? `
          <div style="background: rgba(79, 70, 229, 0.08); border: 1px solid rgba(79, 70, 229, 0.25); border-radius: var(--radius-md); padding: 0.9rem 1.1rem; margin-bottom: 1.2rem;">
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Highest Single Transaction</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.3rem;">
              <div>
                <strong>${topTransaction.category}</strong>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${topTransaction.date} • ${topTransaction.payment_mode}</div>
              </div>
              <div style="font-size: 1.2rem; font-weight: 800; color: #4f46e5;">₹${topTransaction.amount.toLocaleString('en-IN')}</div>
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
              <div style="width: 100%; height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden;">
                <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, #ff6b6b, #ff8e53); border-radius: 3px;"></div>
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
