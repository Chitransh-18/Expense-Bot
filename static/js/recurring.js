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
    // Check if any bill is due today or overdue
    const urgentBills = bills.filter(b => (b.status === 'Due Today' || b.status === 'Overdue' || b.status === 'Upcoming') && !b.is_settled_this_month);
    if (!urgentBills.length) return '';

    return urgentBills.map(bill => {
      const isDueToday = bill.status === 'Due Today';
      const badgeClass = isDueToday ? 'badge-danger' : (bill.status === 'Overdue' ? 'badge-danger' : 'badge-warning');
      const paidByText = bill.paid_by !== 'Self' ? ` (Paid by <strong>${bill.paid_by}</strong>)` : '';
      
      return `
        <div class="alert-banner">
          <div class="alert-info">
            <div class="alert-icon">${isDueToday ? '🚨' : '📅'}</div>
            <div>
              <div style="font-weight: 700; font-size: 1.05rem;">
                ${bill.title} - ${bill.status_text} ${paidByText}
              </div>
              <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.2rem;">
                Your Share: <strong style="color: var(--text-main);">₹${bill.user_share.toLocaleString('en-IN')}</strong> of Total ₹${bill.total_amount.toLocaleString('en-IN')}
              </div>
            </div>
          </div>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            ${bill.paid_by !== 'Self' ? `
              <button class="btn btn-whatsapp btn-sm" onclick="Reminders.sendWhatsAppReminder('${bill.paid_by}', ${bill.user_share}, '${bill.title}')">
                📲 Remind ${bill.paid_by}
              </button>
            ` : ''}
            <button class="btn btn-primary btn-sm" onclick="Recurring.settleBill(${bill.id})">
              ✅ Mark Paid
            </button>
          </div>
        </div>
      `;
    }).join('');
  },

  async renderPage() {
    const container = document.getElementById('view-container');
    const bills = await this.fetchBills();
    const alertBanners = this.renderAlertBanners(bills);

    let html = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <div>
          <h2 class="page-title">📅 Recurring Monthly Bills</h2>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Track monthly subscriptions like YouTube Family (Daksh), Wi-Fi & Rent</p>
        </div>
        <button class="btn btn-primary" onclick="Recurring.openAddModal()">
          ➕ Add Recurring Bill
        </button>
      </div>

      ${alertBanners}

      <div class="glass-card">
        <h3 style="margin-bottom: 1.2rem; font-size: 1.1rem; font-weight: 600;">Your Active Monthly Bills</h3>
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
              ${bills.length ? bills.map(b => `
                <tr>
                  <td>
                    <strong>${b.title}</strong>
                    <div style="font-size: 0.75rem; color: var(--text-dim);">${b.category}</div>
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
                    <div style="display: flex; gap: 0.4rem;">
                      ${!b.is_settled_this_month ? `
                        <button class="btn btn-primary btn-sm" onclick="Recurring.settleBill(${b.id})">
                          ✅ Settle
                        </button>
                      ` : '<span style="color: var(--success); font-size: 0.85rem; font-weight: 600;">Paid ✅</span>'}
                      ${b.paid_by !== 'Self' ? `
                        <button class="btn btn-whatsapp btn-sm" onclick="Reminders.sendWhatsAppReminder('${b.paid_by}', ${b.user_share}, '${b.title}')">
                          📲 Remind
                        </button>
                      ` : ''}
                    </div>
                  </td>
                </tr>
              `).join('') : `
                <tr>
                  <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    No recurring bills set up yet. Click "Add Recurring Bill" above to track YouTube Premium (Daksh), Wi-Fi, etc.
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
            <option value="Subscriptions">Subscriptions (YouTube, Netflix, etc.)</option>
            <option value="Bills">Bills (Wi-Fi, Electricity)</option>
            <option value="Housing">Housing (Rent, Maintenance)</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 1rem;">
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
      this.renderPage();
    } catch (err) {
      alert(err.message || 'Failed to add recurring bill');
    }
  },

  async settleBill(billId) {
    if (!confirm('Mark this bill as settled for the current month? This will also log it as an expense.')) return;
    try {
      await API.request(`/api/recurring/${billId}/settle`, { method: 'POST' });
      this.renderPage();
    } catch (err) {
      alert(err.message || 'Failed to settle bill');
    }
  }
};
