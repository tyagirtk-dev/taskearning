/* main.js – TaskEarner frontend logic */
'use strict';

// ── Sidebar toggle ──────────────────────────────────────────────────────────
(function () {
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sidebarOverlay');
  const toggleBtn = document.getElementById('sidebarToggle');
  const closeBtn  = document.getElementById('sidebarClose');
  if (!sidebar) return;

  function openSidebar()  { sidebar.classList.add('open');  overlay && overlay.classList.add('open'); }
  function closeSidebar() { sidebar.classList.remove('open'); overlay && overlay.classList.remove('open'); }

  toggleBtn && toggleBtn.addEventListener('click', openSidebar);
  closeBtn  && closeBtn.addEventListener('click', closeSidebar);
  overlay   && overlay.addEventListener('click', closeSidebar);
})();

// ── Dark / Light theme toggle ───────────────────────────────────────────────
(function () {
  const btn  = document.getElementById('themeToggle');
  const icon = document.getElementById('themeIcon');
  const html = document.documentElement;

  const stored = localStorage.getItem('te-theme') || 'light';
  html.setAttribute('data-bs-theme', stored);
  updateIcon(stored);

  btn && btn.addEventListener('click', () => {
    const next = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-bs-theme', next);
    localStorage.setItem('te-theme', next);
    updateIcon(next);
  });

  function updateIcon(theme) {
    if (!icon) return;
    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
  }
})();

// ── Auto-dismiss alerts after 5 s ──────────────────────────────────────────
document.querySelectorAll('.alert.fade.show').forEach(el => {
  setTimeout(() => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
    bsAlert && bsAlert.close();
  }, 5000);
});

// ── Confirm delete / destructive actions ────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm || 'Are you sure?')) e.preventDefault();
  });
});

// ── Copy to clipboard ───────────────────────────────────────────────────────
document.querySelectorAll('[data-copy]').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = document.querySelector(btn.dataset.copy);
    if (!target) return;
    navigator.clipboard.writeText(target.value || target.textContent.trim())
      .then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
        setTimeout(() => { btn.innerHTML = orig; }, 2000);
      });
  });
});

// ── nl2br Jinja filter shim (handled server-side, kept for clarity) ─────────
// Server-side: add custom filter in __init__.py if needed.
