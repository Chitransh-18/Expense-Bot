const Reminders = {
  buildMessage(personName, amount, title = 'Split Expense') {
    const formattedAmount = `₹${parseFloat(amount).toLocaleString('en-IN')}`;
    return `Hi ${personName}! 👋\n\nQuick reminder regarding *${title}*:\n💰 Amount / Share: *${formattedAmount}*\n\nPlease let me know your UPI / payment details or confirm once settled. Thanks! 🙏`;
  },

  sendWhatsAppReminder(personName, amount, title = 'Split Expense') {
    const text = this.buildMessage(personName, amount, title);
    const encodedText = encodeURIComponent(text);
    const whatsappUrl = `https://api.whatsapp.com/send?text=${encodedText}`;
    window.open(whatsappUrl, '_blank');
  },

  async shareNative(personName, amount, title = 'Split Expense') {
    const text = this.buildMessage(personName, amount, title);
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Split Reminder: ${title}`,
          text: text
        });
      } catch (err) {
        console.log('Native share error or cancelled:', err);
      }
    } else {
      this.copyToClipboard(text);
    }
  },

  copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
      alert('Reminder message copied to clipboard! You can paste it into WhatsApp, SMS, or Telegram.');
    }).catch(err => {
      console.error('Clipboard copy failed:', err);
      alert(text);
    });
  },

  openReminderModal(personName, amount, title) {
    const text = this.buildMessage(personName, amount, title);
    document.getElementById('modal-title').innerText = '📲 Send Split Reminder';
    document.getElementById('modal-body').innerHTML = `
      <div style="margin-bottom: 1.5rem;">
        <label class="form-label">Preview Reminder Message:</label>
        <div style="background: rgba(11, 15, 25, 0.7); border: 1px solid var(--border-glass); padding: 1rem; border-radius: var(--radius-md); font-size: 0.9rem; white-space: pre-wrap; color: var(--text-main);">
${text}
        </div>
      </div>
      <div style="display: flex; flex-direction: column; gap: 0.8rem;">
        <button class="btn btn-whatsapp" onclick="Reminders.sendWhatsAppReminder('${personName}', ${amount}, '${title}'); App.closeModal();">
          📲 Send via WhatsApp
        </button>
        <button class="btn btn-secondary" onclick="Reminders.shareNative('${personName}', ${amount}, '${title}'); App.closeModal();">
          📤 Share via Phone Apps / SMS
        </button>
        <button class="btn btn-secondary" onclick="Reminders.copyToClipboard(\`${text.replace(/`/g, '\\`')}\`); App.closeModal();">
          📋 Copy Text to Clipboard
        </button>
      </div>
    `;
    App.openModal();
  }
};
