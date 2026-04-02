// ─── Toast Notifications ──────────────────────────────────────────────────────
function showToast(msg, type = 'success') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.className = `toast ${type}`;
  setTimeout(() => toast.classList.add('hidden'), 3000);
}

// ─── Mobile Menu ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('mobileToggle');
  const menu = document.getElementById('mobileMenu');
  if (toggle && menu) {
    toggle.addEventListener('click', () => menu.classList.toggle('open'));
    document.addEventListener('click', e => {
      if (!menu.contains(e.target) && e.target !== toggle) {
        menu.classList.remove('open');
      }
    });
  }

  // Animate elements on load
  document.querySelectorAll('.fade-up').forEach((el, i) => {
    if (!el.style.animationDelay) {
      el.style.animationDelay = (i * 0.04) + 's';
    }
  });

  // Active nav link highlight
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === path) link.classList.add('active');
  });
});

// ─── Keyboard shortcuts ───────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    // Close any open modals
    document.querySelectorAll('[id$="modal"]').forEach(m => {
      if (m.style.display !== 'none') m.style.display = 'none';
    });
  }
});
