let deferredPrompt = null;

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('PWA Service Worker registered:', reg.scope))
      .catch(err => console.error('Service Worker registration failed:', err));
  });
}

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const installBtn = document.getElementById('btn-install-app');
  if (installBtn) {
    installBtn.style.display = 'inline-flex';
  }
});

function triggerInstallApp() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted PWA installation');
      }
      deferredPrompt = null;
      const installBtn = document.getElementById('btn-install-app');
      if (installBtn) installBtn.style.display = 'none';
    });
  } else {
    alert('App is already installed or your browser supports installing via Menu -> Add to Home Screen.');
  }
}
