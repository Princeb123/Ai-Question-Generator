/* =====================================================
   DASHBOARD PAGE — StudySphere
   Drag-drop widgets, progress rings, schedule, AI tip
   ===================================================== */

const DashboardPage = (() => {

  const WIDGETS = [
    { id: 'welcome',   title: 'Welcome',        visible: true },
    { id: 'progress',  title: 'Subject Progress',visible: true },
    { id: 'schedule',  title: "Today's Schedule",visible: true },
    { id: 'aitip',     title: 'AI Tip',          visible: true },
    { id: 'pinned',    title: 'Pinned Notes',    visible: true },
    { id: 'exams',     title: 'Upcoming Exams',  visible: true },
    { id: 'streak',    title: 'Streak & Stats',  visible: true },
  ];

  const AI_TIPS = [
    { tip: 'Try <strong>spaced repetition</strong> — review notes after 1 day, 3 days, then a week. Your retention improves by 80%!', icon: '🧠' },
    { tip: 'The <strong>Pomodoro Technique</strong>: 25 min focus → 5 min break. Your brain stays fresh and efficient.', icon: '🍅' },
    { tip: '<strong>Active recall</strong> beats re-reading. Close your notes and try to explain the topic from memory.', icon: '💡' },
    { tip: 'Sleep is when your brain <strong>consolidates memories</strong>. Studying before bed + good sleep = better retention.', icon: '😴' },
    { tip: 'Teaching others is the fastest way to <strong>deepen your own understanding</strong> of a topic.', icon: '👨‍🏫' },
  ];

  const SUBJECTS = [
    { name: 'Mathematics', pct: 85, color: '#7c3aed', stroke: '#7c3aed' },
    { name: 'Physics',     pct: 72, color: '#06b6d4', stroke: '#06b6d4' },
    { name: 'Chemistry',   pct: 60, color: '#ec4899', stroke: '#ec4899' },
    { name: 'Biology',     pct: 91, color: '#22c55e', stroke: '#22c55e' },
  ];

  const SCHEDULE = [
    { time: '08:00', subject: 'Mathematics', color: '#7c3aed' },
    { time: '10:00', subject: 'Physics', color: '#06b6d4' },
    { time: '13:00', subject: 'Chemistry', color: '#ec4899' },
    { time: '15:30', subject: 'Self Study', color: '#22c55e' },
    { time: '18:00', subject: 'Review & Quiz', color: '#f59e0b' },
  ];

  const PINNED = [
    { text: 'Newton\'s 3rd Law: Every action has an equal and opposite reaction.', color: '#7c3aed' },
    { text: 'Mitosis stages: PMAT — Prophase, Metaphase, Anaphase, Telophase.', color: '#06b6d4' },
    { text: 'Quadratic formula: x = (-b ± √(b²-4ac)) / 2a', color: '#ec4899' },
  ];

  const EXAMS = [
    { name: 'Mathematics Final', sub: 'Calculus & Algebra', date: 'Aug 10' },
    { name: 'Physics Mid-term', sub: 'Optics & Waves', date: 'Aug 14' },
    { name: 'Chemistry Quiz', sub: 'Organic Chemistry', date: 'Aug 17' },
  ];

  let widgetOrder = [...WIDGETS];
  let dragSrc = null;

  function render() {
    const tip = AI_TIPS[Math.floor(Math.random() * AI_TIPS.length)];
    const saved = localStorage.getItem('ss_widgets');
    if (saved) {
      try {
        const ids = JSON.parse(saved);
        widgetOrder = ids.map(id => WIDGETS.find(w => w.id === id)).filter(Boolean);
        // Add any widgets not in saved order
        WIDGETS.forEach(w => { if (!widgetOrder.find(x => x.id === w.id)) widgetOrder.push(w); });
      } catch(e) {}
    }

    return `
<div class="section-header">
  <div>
    <div class="section-title">My Dashboard</div>
    <div class="section-sub">Drag to rearrange • Click ⋯ to pin/hide widgets</div>
  </div>
  <div class="dashboard-controls">
    <button class="btn btn-ghost btn-sm" onclick="DashboardPage.resetLayout()">↺ Reset</button>
    <button class="btn btn-ghost btn-sm" onclick="DashboardPage.saveLayout()">💾 Save Layout</button>
    <button class="btn btn-primary btn-sm" onclick="DashboardPage.showHiddenWidgets()">+ Add Widget</button>
  </div>
</div>
<div class="dashboard-grid" id="widget-grid">
  ${widgetOrder.map(w => w.visible ? renderWidget(w.id, tip) : '').join('')}
</div>`;
  }

  function renderWidget(id, tip) {
    tip = tip || AI_TIPS[0];
    const actions = `<button class="widget-menu-btn" onclick="DashboardPage.toggleMenu('${id}')" title="Options">⋯</button>`;
    switch(id) {
      case 'welcome':  return renderWelcome(actions);
      case 'progress': return renderProgress(actions);
      case 'schedule': return renderSchedule(actions);
      case 'aitip':    return renderAiTip(tip, actions);
      case 'pinned':   return renderPinned(actions);
      case 'exams':    return renderExams(actions);
      case 'streak':   return renderStreak(actions);
      default: return '';
    }
  }

  function renderWelcome(actions) {
    const h = new Date().getHours();
    const greeting = h < 12 ? 'Good Morning' : h < 17 ? 'Good Afternoon' : 'Good Evening';
    return `
<div class="widget widget-welcome" draggable="true" data-widget-id="welcome">
  <div class="widget-header"><span class="widget-title">👋 Welcome</span><div class="widget-actions">${actions}</div></div>
  <div class="welcome-content">
    <div>
      <div class="welcome-greeting">${greeting}, <span>Alex! 🎉</span></div>
      <div class="welcome-sub">Ready to conquer today's learning goals?</div>
    </div>
    <div class="welcome-stats">
      <div class="wstat"><div class="wstat-val">7</div><div class="wstat-label">Day Streak</div></div>
      <div class="wstat"><div class="wstat-val">85%</div><div class="wstat-label">Weekly Goal</div></div>
      <div class="wstat"><div class="wstat-val">12</div><div class="wstat-label">Level</div></div>
    </div>
  </div>
</div>`;
  }

  function renderProgress(actions) {
    const r = 28, circ = 2 * Math.PI * r;
    const rings = SUBJECTS.map(s => {
      const offset = circ - (s.pct / 100) * circ;
      return `
<div class="ring-item">
  <svg class="ring-svg" viewBox="0 0 68 68">
    <circle class="ring-circle-bg" cx="34" cy="34" r="${r}"/>
    <circle class="ring-circle" cx="34" cy="34" r="${r}"
      stroke="${s.color}" stroke-dasharray="${circ}" stroke-dashoffset="${offset}"
      transform="rotate(-90 34 34)"/>
    <text x="34" y="38" text-anchor="middle" fill="${s.color}" font-size="11" font-weight="700">${s.pct}%</text>
  </svg>
  <div class="ring-label">${s.name.split(' ')[0]}</div>
</div>`;
    }).join('');
    return `
<div class="widget" draggable="true" data-widget-id="progress">
  <div class="widget-header"><span class="widget-title">📊 Subject Progress</span><div class="widget-actions">${actions}</div></div>
  <div class="rings-grid">${rings}</div>
</div>`;
  }

  function renderSchedule(actions) {
    const items = SCHEDULE.map(s => `
<div class="schedule-item">
  <span class="schedule-dot" style="background:${s.color}"></span>
  <span class="schedule-time">${s.time}</span>
  <span class="schedule-subject">${s.subject}</span>
</div>`).join('');
    return `
<div class="widget" draggable="true" data-widget-id="schedule">
  <div class="widget-header"><span class="widget-title">📅 Today's Schedule</span><div class="widget-actions">${actions}</div></div>
  <div class="schedule-list">${items}</div>
</div>`;
  }

  function renderAiTip(tip, actions) {
    return `
<div class="widget ai-tip" draggable="true" data-widget-id="aitip">
  <div class="widget-header"><span class="widget-title">🤖 AI Tip of the Day</span><div class="widget-actions">${actions}</div></div>
  <div class="ai-tip-content">
    <div class="ai-avatar">${tip.icon}</div>
    <p class="ai-text">${tip.tip}</p>
  </div>
  <button class="btn btn-ghost btn-sm mt-md" onclick="DashboardPage.refreshTip()">🔄 New Tip</button>
</div>`;
  }

  function renderPinned(actions) {
    const notes = PINNED.map(n => `
<div class="pinned-note" style="border-color:${n.color}">${n.text}</div>`).join('');
    return `
<div class="widget" draggable="true" data-widget-id="pinned">
  <div class="widget-header"><span class="widget-title">📌 Pinned Notes</span><div class="widget-actions">${actions}</div></div>
  <div class="pinned-notes-list">${notes}</div>
  <button class="btn btn-ghost btn-sm mt-md" onclick="App.toast('Note pinning — coming soon!','info')">+ Add Note</button>
</div>`;
  }

  function renderExams(actions) {
    const items = EXAMS.map(e => `
<div class="exam-item">
  <span class="exam-date">${e.date}</span>
  <div><div class="exam-name">${e.name}</div><div class="exam-sub">${e.sub}</div></div>
</div>`).join('');
    return `
<div class="widget" draggable="true" data-widget-id="exams">
  <div class="widget-header"><span class="widget-title">🗓️ Upcoming Exams</span><div class="widget-actions">${actions}</div></div>
  <div class="exam-list">${items}</div>
</div>`;
  }

  function renderStreak(actions) {
    return `
<div class="widget" draggable="true" data-widget-id="streak">
  <div class="widget-header"><span class="widget-title">🔥 Streaks & Stats</span><div class="widget-actions">${actions}</div></div>
  <div style="display:flex;flex-direction:column;gap:12px">
    <div style="display:flex;gap:16px;flex-wrap:wrap">
      <div class="wstat"><div class="wstat-val">7</div><div class="wstat-label">Day Streak 🔥</div></div>
      <div class="wstat"><div class="wstat-val">42</div><div class="wstat-label">Quizzes Done ✅</div></div>
      <div class="wstat"><div class="wstat-val">18h</div><div class="wstat-label">Study Time ⏱️</div></div>
    </div>
    <div>
      <div class="xp-row" style="margin-bottom:4px"><span style="font-size:12px;color:var(--text-muted)">Weekly Goal</span><span style="font-size:12px;color:var(--text-muted)">85%</span></div>
      <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:85%"></div></div>
    </div>
  </div>
</div>`;
  }

  function init() {
    const grid = document.getElementById('widget-grid');
    if (!grid) return;
    setupDragDrop(grid);
  }

  function setupDragDrop(grid) {
    grid.addEventListener('dragstart', e => {
      const w = e.target.closest('[data-widget-id]');
      if (!w) return;
      dragSrc = w;
      w.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });
    grid.addEventListener('dragend', e => {
      const w = e.target.closest('[data-widget-id]');
      if (w) w.classList.remove('dragging');
      document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
    });
    grid.addEventListener('dragover', e => {
      e.preventDefault();
      const target = e.target.closest('[data-widget-id]');
      if (target && target !== dragSrc) {
        document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
        target.classList.add('drag-over');
      }
    });
    grid.addEventListener('drop', e => {
      e.preventDefault();
      const target = e.target.closest('[data-widget-id]');
      if (!target || !dragSrc || target === dragSrc) return;
      target.classList.remove('drag-over');
      const allWidgets = [...grid.querySelectorAll('[data-widget-id]')];
      const srcIdx = allWidgets.indexOf(dragSrc);
      const tgtIdx = allWidgets.indexOf(target);
      if (srcIdx < tgtIdx) grid.insertBefore(dragSrc, target.nextSibling);
      else grid.insertBefore(dragSrc, target);
      App.toast('Widget rearranged!', 'success');
    });
  }

  function refreshTip() {
    const tip = AI_TIPS[Math.floor(Math.random() * AI_TIPS.length)];
    const tipEl = document.querySelector('.ai-tip .ai-text');
    const iconEl = document.querySelector('.ai-tip .ai-avatar');
    if (tipEl) { tipEl.style.opacity = 0; setTimeout(() => { tipEl.innerHTML = tip.tip; iconEl.textContent = tip.icon; tipEl.style.opacity = 1; tipEl.style.transition = 'opacity 0.3s'; }, 200); }
  }

  function toggleMenu(id) {
    App.toast(`Widget options for "${id}" — try dragging to rearrange!`, 'info');
  }

  function saveLayout() {
    const grid = document.getElementById('widget-grid');
    if (!grid) return;
    const ids = [...grid.querySelectorAll('[data-widget-id]')].map(el => el.dataset.widgetId);
    localStorage.setItem('ss_widgets', JSON.stringify(ids));
    App.toast('Layout saved! ✅', 'success');
  }

  function resetLayout() {
    localStorage.removeItem('ss_widgets');
    widgetOrder = [...WIDGETS];
    App.navigate('dashboard');
    App.toast('Layout reset to default', 'info');
  }

  function showHiddenWidgets() {
    App.toast('All widgets are currently visible!', 'info');
  }

  return { render, init, refreshTip, toggleMenu, saveLayout, resetLayout, showHiddenWidgets };
})();
