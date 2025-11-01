'use strict';

(function(){
  // Register Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('/static/js/sw.js').catch(function(err){
        console.debug('SW registration failed:', err);
      });
    });
  }

  // Minimal install prompt handler
  let deferredPrompt;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const btn = document.createElement('button');
    btn.className = 'btn btn-primary position-fixed';
    btn.style.bottom = '1rem';
    btn.style.left = '1rem';
    btn.style.zIndex = '1100';
    btn.textContent = document.documentElement.lang === 'ar' ? 'تثبيت التطبيق' : 'Install App';
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      try {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome !== 'accepted') { btn.remove(); }
      } catch(_) {}
    });
    document.body.appendChild(btn);
  });
})();
