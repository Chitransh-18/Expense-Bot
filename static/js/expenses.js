const Expenses = {
  async fetchExpenses(filter = 'all', category = '') {
    try {
      let url = `/api/expenses?filter=${filter}`;
      if (category) url += `&category=${encodeURIComponent(category)}`;
      const data = await API.request(url);
      return data.expenses || [];
    } catch (err) {
      console.error('Error fetching expenses:', err);
      return [];
    }
  },

  async renderPage(filter = 'all') {
    const container = document.getElementById('view-container');
    const expenses = await this.fetchExpenses(filter);

    const total = expenses.reduce((sum, e) => sum + e.amount, 0);
    const personalTotal = expenses.filter(e => e.expense_type === 'Personal').reduce((sum, e) => sum + e.amount, 0);
    const splitTotal = expenses.filter(e => e.expense_type === 'Split').reduce((sum, e) => sum + e.amount, 0);

    let html = `
      <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2rem; flex-wrap: wrap; gap: 1rem;">
        <div>
          <h2 class="page-title">💰 Expense Tracker</h2>
          <p style="color: var(--text-muted); font-size: 0.95rem; margin-top: 0.2rem;">Manage personal spending and shared split expenses</p>
        </div>
        <div style="display: flex; gap: 0.8rem; flex-wrap: wrap;">
          <a href="/api/export/csv" class="btn btn-secondary" target="_blank" download>
            📄 Export CSV
          </a>
          <button class="btn btn-primary" onclick="Expenses.openAddModal()">
            ➕ Add Expense
          </button>
        </div>
      </div>

      <!-- ⚡ Core USP: Natural Language AI Quick-Add Bar on Expenses Page -->
      <div class="ai-magic-card">
        <div class="ai-magic-header">
          <div class="ai-badge">
            <span>✨</span> AI Quick-Add
          </div>
          <span style="font-size: 0.78rem; color: var(--text-muted);">
            Natural Language (English, Hindi & Hinglish)
          </span>
        </div>

        <div class="ai-input-group">
          <input 
            type="text" 
            id="expenses-nlp-input" 
            class="ai-magic-input" 
            placeholder="e.g. 'Coffee 180 cash' or 'Dinner 600 with Rohit split via UPI'..."
            onkeydown="if(event.key === 'Enter') Expenses.handleQuickAdd()"
            autocomplete="off"
          />
          <button 
            type="button" 
            class="btn btn-primary" 
            id="btn-expenses-quick-add"
            onclick="Expenses.handleQuickAdd()"
          >
            ⚡ Quick Log
          </button>
        </div>
      </div>

      <!-- Filters & Summary -->
      <div class="stats-grid">
        <div class="glass-card stat-card">
          <span class="stat-label">Total Filtered</span>
          <span class="stat-value">₹${total.toLocaleString('en-IN')}</span>
        </div>
        <div class="glass-card stat-card">
          <span class="stat-label">Personal Spent</span>
          <span class="stat-value" style="color: var(--primary);">₹${personalTotal.toLocaleString('en-IN')}</span>
        </div>
        <div class="glass-card stat-card">
          <span class="stat-label">Split Spent</span>
          <span class="stat-value" style="color: var(--secondary);">₹${splitTotal.toLocaleString('en-IN')}</span>
        </div>
      </div>

      <div class="glass-card" style="margin-bottom: 1.5rem; padding: 1rem 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <button class="btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}" onclick="Expenses.renderPage('all')">All Time</button>
            <button class="btn btn-sm ${filter === 'this_month' ? 'btn-primary' : 'btn-secondary'}" onclick="Expenses.renderPage('this_month')">This Month 📅</button>
            <button class="btn btn-sm ${filter === 'last_month' ? 'btn-primary' : 'btn-secondary'}" onclick="Expenses.renderPage('last_month')">Last Month 📆</button>
          </div>
          <span style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600;">${expenses.length} Records</span>
        </div>
      </div>

      <!-- Expenses Data Table -->
      <div class="glass-card">
        ${expenses.length ? `
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Category</th>
                  <th>Description</th>
                  <th>Type</th>
                  <th>Payment</th>
                  <th>Your Share</th>
                  <th>Split Details</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${expenses.map(e => `
                  <tr>
                    <td><span style="font-weight: 600;">${e.date}</span></td>
                    <td><strong>${e.category}</strong></td>
                    <td style="color: var(--text-muted);">${e.description || '-'}</td>
                    <td>
                      <span class="badge ${e.expense_type === 'Personal' ? 'badge-warning' : 'badge-success'}">
                        ${e.expense_type === 'Personal' ? '👤 Personal' : '👥 Split'}
                      </span>
                    </td>
                    <td><span style="font-size: 0.88rem; font-weight: 500;">${e.payment_mode}</span></td>
                    <td>
                      <strong style="color: var(--text-main); font-size: 1.05rem;">₹${e.amount.toLocaleString('en-IN')}</strong>
                      ${(e.total_bill_amount && e.total_bill_amount > e.amount) ? `
                        <br><span style="font-size: 0.74rem; color: var(--text-muted); font-weight: 400;">(Total Bill: ₹${e.total_bill_amount.toLocaleString('en-IN')})</span>
                      ` : ''}
                    </td>
                    <td>
                      ${e.split_with ? `
                        <span style="font-size: 0.85rem; color: var(--secondary); font-weight: 600;">Split with: ${e.split_with}</span>
                      ` : '-'}
                    </td>
                    <td>
                      <div style="display: flex; gap: 0.4rem; align-items: center;">
                        ${e.split_with ? `
                          <button class="btn btn-whatsapp btn-sm" onclick="Reminders.openReminderModal('${e.split_with}', ${e.amount}, '${e.category}')">
                            📲 Remind
                          </button>
                        ` : ''}
                        <button class="btn btn-secondary btn-sm" style="color: var(--danger); padding: 0.45rem 0.7rem;" onclick="Expenses.deleteExpense(${e.id})" title="Delete Expense">
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        ` : `
          <!-- Checklist Item 11: Illustrated Empty State -->
          <div class="empty-state-card">
            <div class="empty-state-icon">💸</div>
            <h3 class="empty-state-title">No expenses found</h3>
            <p class="empty-state-desc">
              You haven't logged any expenses for this time period. Use the AI Magic bar above or click Add Expense to get started!
            </p>
            <button class="btn btn-primary" onclick="Expenses.openAddModal()">
              ➕ Add New Expense
            </button>
          </div>
        `}
      </div>
    `;

    container.innerHTML = html;
  },

  async handleQuickAdd() {
    const input = document.getElementById('expenses-nlp-input');
    const btn = document.getElementById('btn-expenses-quick-add');
    if (!input) return;

    const text = input.value.trim();
    if (!text) {
      Toast.show('Please enter an expense like "Dinner 540 with Daksh"', 'error');
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
      Toast.show(err.message || 'Could not parse expense.', 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerText = '⚡ Quick Log';
      }
    }
  },

  openAddModal() {
    document.getElementById('modal-title').innerText = '➕ Record New Expense';
    document.getElementById('modal-body').innerHTML = `
      <form id="add-expense-form" onsubmit="Expenses.handleAddSubmit(event)">
        <div class="form-group">
          <label class="form-label">Expense Type</label>
          <select class="form-select" id="exp-type" onchange="Expenses.toggleSplitFields()">
            <option value="Personal">Personal Spending 👤</option>
            <option value="Split">Split with Friends 👥</option>
          </select>
        </div>

        <div class="form-group" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div>
            <label class="form-label">Category</label>
            <select class="form-select" id="exp-category">
              <option value="Food & Dining">Food & Dining 🍔</option>
              <option value="Travel & Cab">Travel & Cab 🚖</option>
              <option value="Shopping">Shopping 🛍</option>
              <option value="Bills & Utilities">Bills & Utilities 💡</option>
              <option value="Entertainment">Entertainment 🎬</option>
              <option value="Health">Health 🏥</option>
              <option value="Subscriptions">Subscriptions 📱</option>
              <option value="General">General / Other ✍️</option>
            </select>
          </div>
          <div>
            <label class="form-label" id="amount-label">Total Amount (₹)</label>
            <input type="number" step="0.01" class="form-input" id="exp-amount" placeholder="e.g. 450" required />
          </div>
        </div>

        <div class="form-group" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div>
            <label class="form-label">Payment Mode</label>
            <select class="form-select" id="exp-paymode">
              <option value="UPI">UPI (GPay / PhonePe / Paytm) 📱</option>
              <option value="Cash">Cash 💵</option>
              <option value="Online">Online / Net Banking 🌐</option>
              <option value="Card">Debit / Credit Card 💳</option>
            </select>
          </div>
          <div>
            <label class="form-label">Date</label>
            <input type="date" class="form-input" id="exp-date" value="${new Date().toISOString().split('T')[0]}" required />
          </div>
        </div>

        <div id="split-fields" style="display: none;">
          <div class="form-group">
            <label class="form-label">Split With (Names separated by commas)</label>
            <input type="text" class="form-input" id="exp-splitwith" placeholder="e.g. Daksh, Amrit" />
            <span style="font-size: 0.8rem; color: #4f46e5; margin-top: 0.35rem; display: block;">
              💡 <strong>Equal Split:</strong> Total amount will be divided equally (e.g. ₹450 total split with 1 friend = your ₹225 share logged).
            </span>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Description (Optional)</label>
          <input type="text" class="form-input" id="exp-desc" placeholder="e.g. Dinner at cafe with Daksh" />
        </div>

        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem; padding: 0.95rem;">
          Save Expense
        </button>
      </form>
    `;
    App.openModal();
  },

  toggleSplitFields() {
    const type = document.getElementById('exp-type').value;
    const splitFields = document.getElementById('split-fields');
    const amountLabel = document.getElementById('amount-label');
    if (splitFields) splitFields.style.display = (type === 'Split') ? 'block' : 'none';
    if (amountLabel) {
      amountLabel.innerText = (type === 'Split') ? 'Total Bill Amount (₹)' : 'Amount (₹)';
    }
  },

  async handleAddSubmit(e) {
    e.preventDefault();
    const expense_type = document.getElementById('exp-type').value;
    const category = document.getElementById('exp-category').value;
    const amount = parseFloat(document.getElementById('exp-amount').value);
    const payment_mode = document.getElementById('exp-paymode').value;
    const date = document.getElementById('exp-date').value;
    const split_with = document.getElementById('exp-splitwith') ? document.getElementById('exp-splitwith').value : '';
    const description = document.getElementById('exp-desc').value;

    try {
      await API.request('/api/expenses', {
        method: 'POST',
        body: JSON.stringify({ expense_type, category, amount, payment_mode, date, split_with, description })
      });
      App.closeModal();
      Toast.show('✅ Expense recorded successfully!', 'success');
      this.renderPage();
    } catch (err) {
      Toast.show(err.message || 'Failed to save expense', 'error');
    }
  },

  async deleteExpense(id) {
    if (!confirm('Are you sure you want to delete this expense record?')) return;
    try {
      await API.request(`/api/expenses/${id}`, { method: 'DELETE' });
      Toast.show('🗑️ Expense deleted', 'info');
      this.renderPage();
    } catch (err) {
      Toast.show(err.message || 'Failed to delete expense', 'error');
    }
  }
};
