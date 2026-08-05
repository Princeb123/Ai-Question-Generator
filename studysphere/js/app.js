/* =====================================================
   MAIN APP ROUTER & ENGINE — StudySphere
   Particles system, Page routing, XP tracker, Toast manager
   ===================================================== */

// ---------- Particle System for Canvas ----------
const ParticleSystem = (() => {
  let canvas, ctx, particles = [], animId;

  function init() {
    canvas = document.getElementById('particles-canvas');
    if (!canvas) return;
    ctx = canvas.getContext('2d');
    resize();
    window.addEventListener('resize', resize);
    createParticles();
    animate();
  }

  function resize() {
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function createParticles() {
    particles = [];
    const count = Math.floor((window.innerWidth * window.innerHeight) / 18000);
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 2 + 1,
        dx: (Math.random() - 0.5) * 0.4,
        dy: (Math.random() - 0.5) * 0.4,
        alpha: Math.random() * 0.5 + 0.2,
      });
    }
  }

  function animate() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const bgMode = document.documentElement.getAttribute('data-bg');

    if (bgMode === 'particles' || bgMode === 'space') {
      particles.forEach(p => {
        p.x += p.dx;
        p.y += p.dy;
        if (p.x < 0 || p.x > canvas.width) p.dx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.dy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
        ctx.fill();
      });
    }

    animId = requestAnimationFrame(animate);
  }

  function restart() {
    if (animId) cancelAnimationFrame(animId);
    createParticles();
    animate();
  }

  return { init, restart };
})();

// ---------- Main App State & Router ----------
const App = (() => {
  let currentPage = 'dashboard';
  let userXP = 2450;
  let userMaxXP = 3000;

  const PAGES = {
    dashboard:   { name: 'Dashboard',         icon: '🏠', controller: DashboardPage },
    learning:    { name: 'Learning Modes',    icon: '🎓', controller: LearningPage },
    story:       { name: 'Story Generator',   icon: '📖', controller: StoryPage },
    video:       { name: 'Video Lessons',     icon: '🎬', controller: VideoPage },
    reading:     { name: 'Reading Assistant', icon: '📚', controller: ReadingPage },
    gamification:{ name: 'Gamification',      icon: '🎮', controller: GamificationPage },
    drawing:     { name: 'Visual Learning',   icon: '🎨', controller: DrawingPage },
    parent:      { name: 'Parent Controls',   icon: '👪', controller: ParentPage },
    settings:    { name: 'Settings',          icon: '⚙️', controller: SettingsPage },
  };

  function init() {
    ThemeEngine.load();
    ParticleSystem.init();

    // Set default avatar
    const svgAvatar = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="%237c3aed"/><text x="50" y="65" font-size="45" text-anchor="middle" fill="white">👨‍🎓</text></svg>`;
    document.getElementById('sidebar-avatar-img').src = svgAvatar;
    document.getElementById('topbar-avatar-img').src = svgAvatar;

    // Navigation events
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
      item.addEventListener('click', e => {
        e.preventDefault();
        const page = item.getAttribute('data-page');
        if (page) navigate(page);
      });
    });

    // Mobile menu toggle
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');
    if (mobileBtn && sidebar) {
      mobileBtn.addEventListener('click', () => {
        sidebar.classList.toggle('mobile-open');
      });
    }

    // Sidebar collapse toggle
    const toggleBtn = document.getElementById('sidebar-toggle');
    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
      });
    }

    // Theme toggle button topbar
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        ThemeEngine.toggleTheme();
      });
    }

    // Notification Panel Toggle
    const notifBtn = document.getElementById('notif-btn');
    const notifPanel = document.getElementById('notif-panel');
    if (notifBtn && notifPanel) {
      notifBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        notifPanel.classList.toggle('hidden');
        document.getElementById('notif-dot').style.display = 'none';
      });
      document.addEventListener('click', (e) => {
        if (!notifPanel.contains(e.target) && !notifBtn.contains(e.target)) {
          notifPanel.classList.add('hidden');
        }
      });
    }

    // Initial render
    navigate('dashboard');
  }

  function navigate(pageId) {
    const pageConfig = PAGES[pageId];
    if (!pageConfig) return;

    currentPage = pageId;

    // Update Nav Active State
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
      item.classList.toggle('active', item.getAttribute('data-page') === pageId);
    });

    // Update Breadcrumb
    const bc = document.getElementById('page-breadcrumb');
    if (bc) bc.innerHTML = `${pageConfig.icon} ${pageConfig.name}`;

    // Render Page HTML
    const content = document.getElementById('page-content');
    if (content) {
      content.style.opacity = 0;
      setTimeout(() => {
        content.innerHTML = pageConfig.controller.render();
        pageConfig.controller.init();
        content.style.opacity = 1;
        content.style.transition = 'opacity 0.2s ease-out';
      }, 100);
    }

    // Close mobile menu if open
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.remove('mobile-open');
  }

  function toast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}</span>
      <div>${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      toast.style.transition = 'all 0.3s ease-out';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  function addXP(amount) {
    userXP += amount;
    const label = document.getElementById('xp-label');
    const bar = document.getElementById('xp-bar');

    if (label) label.textContent = `${userXP.toLocaleString()} / ${userMaxXP.toLocaleString()}`;
    if (bar) bar.style.width = `${Math.min((userXP / userMaxXP) * 100, 100)}%`;
  }

  return { init, navigate, toast, addXP };
})();

// Launch application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
