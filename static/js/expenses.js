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
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <div>
          <h2 class="page-title">💰 Expense Tracker</h2>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Manage personal spending and shared split expenses</p>
        </div>
        <div style="display: flex; gap: 0.8rem;">
          <a href="/api/export/csv" class="btn btn-secondary" target="_blank" download>
            📄 Export CSV
          </a>
          <button class="btn btn-primary" onclick="Expenses.openAddModal()">
            ➕ Add Expense
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
          <div style="display: flex; gap: 0.5rem;">
            <button class="btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}" onclick="Expenses.renderPage('all')">All Time</button>
            <button class="btn btn-sm ${filter === 'this_month' ? 'btn-primary' : 'btn-secondary'}" onclick="Expenses.renderPage('this_month')">This Month 📅</button>
            <button class="btn btn-sm ${filter === 'last_month' ? 'btn-primary' : 'btn-secondary'}" onclick="Expenses.renderPage('last_month')">Last Month 📆</button>
          </div>
          <span style="font-size: 0.85rem; color: var(--text-muted);">${expenses.length} Records</span>
        </div>
      </div>

      <!-- Expenses Data Table -->
      <div class="glass-card">
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
              ${expenses.length ? expenses.map(e => `
                <tr>
                  <td><span style="font-weight: 500;">${e.date}</span></td>
                  <td><strong>${e.category}</strong></td>
                  <td style="color: var(--text-muted);">${e.description || '-'}</td>
                  <td>
                    <span class="badge ${e.expense_type === 'Personal' ? 'badge-warning' : 'badge-success'}">
                      ${e.expense_type === 'Personal' ? '👤 Personal' : '👥 Split'}
                    </span>
                  </td>
                  <td>${e.payment_mode}</td>
                  <td>
                    <strong style="color: var(--text-main);">₹${e.amount.toLocaleString('en-IN')}</strong>
                    ${(e.total_bill_amount && e.total_bill_amount > e.amount) ? `
                      <br><span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 400;">(Total Bill: ₹${e.total_bill_amount.toLocaleString('en-IN')})</span>
                    ` : ''}
                  </td>
                  <td>
                    ${e.split_with ? `
                      <span style="font-size: 0.85rem; color: var(--secondary);">Split with: <strong>${e.split_with}</strong></span>
                    ` : '-'}
                  </td>
                  <td>
                    <div style="display: flex; gap: 0.4rem;">
                      ${e.split_with ? `
                        <button class="btn btn-whatsapp btn-sm" onclick="Reminders.openReminderModal('${e.split_with}', ${e.amount}, '${e.category}')">
                          📲 Remind
                        </button>
                      ` : ''}
                      <button class="btn btn-secondary btn-sm" style="color: var(--danger);" onclick="Expenses.deleteExpense(${e.id})">
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              `).join('') : `
                <tr>
                  <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    No expenses found for this filter. Click "Add Expense" above to record one!
                  </td>
                </tr>
              `}
            </tbody>
          </table>
        </div>
      </div>
    `;

    container.innerHTML = html;
  },

  openAddModal() {
    document.getElementById('modal-title').innerText = '➕ Log Expense';
    document.getElementById('modal-body').innerHTML = `
      <form id="expense-form" onsubmit="Expenses.handleAddSubmit(event)">
        <div class="form-group">
          <label class="form-label">Expense Type</label>
          <select class="form-select" id="exp-type" onchange="Expenses.toggleSplitFields()">
            <option value="Personal">Personal 💰</option>
            <option value="Split">Split 👥</option>
          </select>
        </div>

        <div class="form-group" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div>
            <label class="form-label">Category</label>
            <select class="form-select" id="exp-category">
              <option value="Food & Dining">Food 🍔</option>
              <option value="Travel & Cab">Travelling 🚖</option>
              <option value="Shopping">Shopping 🛍</option>
              <option value="Bills & Utilities">Bills 💡</option>
              <option value="Entertainment">Entertainment 🎬</option>
              <option value="Health">Health 🏥</option>
              <option value="Subscriptions">Subscriptions 📱</option>
              <option value="Custom">Custom ✍️</option>
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
              <option value="UPI">UPI 📱</option>
              <option value="Cash">Cash 💵</option>
              <option value="Online">Online 🌐</option>
              <option value="Card">Card 💳</option>
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
            <input type="text" class="form-input" id="exp-splitwith" placeholder="e.g. Amrit, Daksh" />
            <span style="font-size: 0.8rem; color: var(--cyan); margin-top: 0.3rem; display: block;">
              💡 <strong>Equal Split:</strong> Total amount will be divided equally (e.g. ₹450 total split with 1 friend = your ₹225 share logged).
            </span>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Description (Optional)</label>
          <input type="text" class="form-input" id="exp-desc" placeholder="e.g. Dinner at restaurant with Amrit" />
        </div>

        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 1rem;">
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
    splitFields.style.display = (type === 'Split') ? 'block' : 'none';
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
      this.renderPage();
    } catch (err) {
      alert(err.message || 'Failed to save expense');
    }
  },

  async deleteExpense(id) {
    if (!confirm('Are you sure you want to delete this expense record?')) return;
    try {
      await API.request(`/api/expenses/${id}`, { method: 'DELETE' });
      this.renderPage();
    } catch (err) {
      alert(err.message || 'Failed to delete expense');
    }
  }
};
