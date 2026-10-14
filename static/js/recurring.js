const Recurring = {
  async fetchBills() {
    try {
      const data = await API.request('/api/recurring');
      return data.recurring_bills || [];
    } catch (err) {
      console.error('Error fetching recurring bills:', err);
      return [];
    }
  },

  renderAlertBanners(bills) {
    const overdueBills = bills.filter(b => b.status === 'Overdue');
    const dueTodayBills = bills.filter(b => b.status === 'Due Today');

    let html = '';

    if (overdueBills.length > 0) {
      html += `
        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--radius-lg); padding: 1rem 1.4rem; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.8rem;">
          <div style="display: flex; align-items: center; gap: 0.8rem;">
            <span style="font-size: 1.5rem;">🚨</span>
            <div>
              <strong style="color: #ef4444; font-size: 0.95rem;">Overdue Recurring Bill${overdueBills.length > 1 ? 's' : ''}!</strong>
              <div style="font-size: 0.85rem; color: var(--text-muted);">${overdueBills.map(b => `${b.title} (₹${b.user_share})`).join(', ')}</div>
            </div>
          </div>
          <button class="btn btn-primary btn-sm" onclick="window.location.hash='#recurring'">Review Overdue Bills</button>
        </div>
      `;
    }

    if (dueTodayBills.length > 0) {
      html += `
        <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: var(--radius-lg); padding: 1rem 1.4rem; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.8rem;">
          <div style="display: flex; align-items: center; gap: 0.8rem;">
            <span style="font-size: 1.5rem;">📅</span>
            <div>
              <strong style="color: #f59e0b; font-size: 0.95rem;">Due Today!</strong>
              <div style="font-size: 0.85rem; color: var(--text-muted);">${dueTodayBills.map(b => `${b.title} (₹${b.user_share})`).join(', ')}</div>
            </div>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#recurring'">Check Bills</button>
        </div>
      `;
    }

    return html;
  },

  async renderPage() {
    const container = document.getElementById('view-container');
    const bills = await this.fetchBills();
    const alertBanners = this.renderAlertBanners(bills);

    let html = `
      <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2rem; flex-wrap: wrap; gap: 1rem;">
        <div>
          <h2 class="page-title">📅 Recurring Monthly Bills</h2>
          <p style="color: var(--text-muted); font-size: 0.95rem; margin-top: 0.2rem;">Track monthly subscriptions like YouTube Family (Daksh), Wi-Fi & Rent</p>
        </div>
        <button class="btn btn-primary" onclick="Recurring.openAddModal()">
          ➕ Add Recurring Bill
        </button>
      </div>

      ${alertBanners}

      <div class="glass-card">
        <h3 style="margin-bottom: 1.2rem; font-size: 1.15rem; font-weight: 700;">Your Active Monthly Bills</h3>
        
        ${bills.length ? `
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Bill / Subscription</th>
                  <th>Due Day</th>
                  <th>Paid By</th>
                  <th>Total Bill</th>
                  <th>Your Share</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${bills.map(b => `
                  <tr>
                    <td>
                      <strong>${b.title}</strong>
                      <div style="font-size: 0.75rem; color: var(--text-muted);">${b.category}</div>
                    </td>
                    <td><span style="font-weight: 600;">${b.due_day}th</span> of month</td>
                    <td>${b.paid_by === 'Self' ? '👤 Self' : `👥 ${b.paid_by}`}</td>
                    <td>₹${b.total_amount.toLocaleString('en-IN')}</td>
                    <td><strong style="color: var(--primary);">₹${b.user_share.toLocaleString('en-IN')}</strong></td>
                    <td>
                      <span class="badge ${b.is_settled_this_month ? 'badge-success' : (b.status === 'Due Today' || b.status === 'Overdue' ? 'badge-danger' : 'badge-warning')}">
                        ${b.status_text}
                      </span>
                    </td>
                    <td>
                      <div style="display: flex; gap: 0.4rem; align-items: center;">
                        ${!b.is_settled_this_month ? `
                          <button class="btn btn-primary btn-sm" onclick="Recurring.settleBill(${b.id})">
                            ✅ Settle
                          </button>
                        ` : '<span style="color: var(--success); font-size: 0.85rem; font-weight: 700;">Paid ✅</span>'}
                        ${b.paid_by !== 'Self' ? `
                          <button class="btn btn-whatsapp btn-sm" onclick="Reminders.sendWhatsAppReminder('${b.paid_by}', ${b.user_share}, '${b.title}')">
                            📲 Remind
                          </button>
                        ` : ''}
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
            <div class="empty-state-icon">📅</div>
            <h3 class="empty-state-title">No Recurring Bills Set Up</h3>
            <p class="empty-state-desc">
              Never miss a monthly subscription again! Add your YouTube Family plan, Wi-Fi bill, or Rent to get automated payment alerts and split reminders.
            </p>
            <button class="btn btn-primary" onclick="Recurring.openAddModal()">
              ➕ Add Your First Bill
            </button>
          </div>
        `}
      </div>
    `;

    container.innerHTML = html;
  },

  openAddModal() {
    document.getElementById('modal-title').innerText = '➕ Add Recurring Monthly Bill';
    document.getElementById('modal-body').innerHTML = `
      <form id="recurring-form" onsubmit="Recurring.handleAddSubmit(event)">
        <div class="form-group">
          <label class="form-label">Bill / Subscription Title</label>
          <input type="text" class="form-input" id="rec-title" placeholder="e.g. YouTube Family Premium" required />
        </div>
        <div class="form-group" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div>
            <label class="form-label">Total Monthly Bill (₹)</label>
            <input type="number" step="0.01" class="form-input" id="rec-total" placeholder="e.g. 299" required />
          </div>
          <div>
            <label class="form-label">Your Share (₹)</label>
            <input type="number" step="0.01" class="form-input" id="rec-share" placeholder="e.g. 50" required />
          </div>
        </div>
        <div class="form-group" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div>
            <label class="form-label">Paid By</label>
            <input type="text" class="form-input" id="rec-paidby" placeholder="e.g. Daksh or Self" required />
          </div>
          <div>
            <label class="form-label">Due Day of Month (1-31)</label>
            <input type="number" min="1" max="31" class="form-input" id="rec-dueday" placeholder="e.g. 3" required />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Category</label>
          <select class="form-select" id="rec-category">
            <option value="Subscriptions">Subscriptions (YouTube, Netflix, Spotify)</option>
            <option value="Bills">Utilities (Wi-Fi, Electricity, Gas)</option>
            <option value="Housing">Housing (Rent, Maintenance, Maid)</option>
            <option value="Other">Other Recurring Expense</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem; padding: 0.95rem;">
          Save Recurring Bill
        </button>
      </form>
    `;
    App.openModal();
  },

  async handleAddSubmit(e) {
    e.preventDefault();
    const title = document.getElementById('rec-title').value;
    const total_amount = parseFloat(document.getElementById('rec-total').value);
    const user_share = parseFloat(document.getElementById('rec-share').value);
    const paid_by = document.getElementById('rec-paidby').value;
    const due_day = parseInt(document.getElementById('rec-dueday').value);
    const category = document.getElementById('rec-category').value;

    try {
      await API.request('/api/recurring', {
        method: 'POST',
        body: JSON.stringify({ title, total_amount, user_share, paid_by, due_day, category })
      });
      App.closeModal();
      Toast.show('✅ Recurring bill added successfully!', 'success');
      this.renderPage();
    } catch (err) {
      Toast.show(err.message || 'Failed to add recurring bill', 'error');
    }
  },

  async settleBill(billId) {
    if (!confirm('Mark this bill as settled for the current month? This will also log it as an expense.')) return;
    try {
      await API.request(`/api/recurring/${billId}/settle`, { method: 'POST' });
      Toast.show('🎉 Bill marked as settled and logged!', 'success');
      this.renderPage();
    } catch (err) {
      Toast.show(err.message || 'Failed to settle bill', 'error');
    }
  }
};
