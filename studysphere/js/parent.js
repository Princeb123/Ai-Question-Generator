/* =====================================================
   PARENT CONTROLS PAGE — StudySphere
   Screen time limits, study schedules, distraction blocker & progress monitoring
   ===================================================== */

const ParentPage = (() => {
  const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  let limits = { Mon: 90, Tue: 90, Wed: 90, Thu: 90, Fri: 120, Sat: 180, Sun: 180 };
  let distractionBlocker = true;

  function render() {
    return `
<div class="section-header">
  <div>
    <div class="section-title">Parent Dashboard & Controls</div>
    <div class="section-sub">Set study limits, schedule study windows, approve friends, and reward progress.</div>
  </div>
  <div class="badge badge-success">🔒 Parent PIN Active</div>
</div>

<div class="parent-grid">
  <!-- Screen Time Manager -->
  <div class="glass-card p-lg">
    <h3 class="font-bold text-lg mb-md">⏱️ Daily Screen Time Limits</h3>
    <div class="screen-time-days">
      ${DAYS.map(d => `
        <div class="day-row">
          <div class="day-label">${d}</div>
          <input type="range" class="form-range day-slider" min="30" max="300" step="15" 
                 value="${limits[d]}" onchange="ParentPage.setLimit('${d}', this.value)" />
          <div class="day-val" id="limit-val-${d}">${limits[d]}m</div>
        </div>
      `).join('')}
    </div>
  </div>

  <!-- Distraction Blocker & Safety -->
  <div class="glass-card p-lg flex flex-col gap-md">
    <h3 class="font-bold text-lg">🛡️ Safety & Focus Controls</h3>
    
    <div class="settings-row">
      <div>
        <div class="settings-row-label">Distraction Blocker</div>
        <div class="settings-row-sub">Blocks social media & gaming during study hours</div>
      </div>
      <div class="toggle ${distractionBlocker ? 'active' : ''}" 
           onclick="ParentPage.toggleDistraction(this)"></div>
    </div>

    <div class="settings-row">
      <div>
        <div class="settings-row-label">AI Conversation Monitoring</div>
        <div class="settings-row-sub">Flag inappropriate content or non-educational prompts</div>
      </div>
      <div class="toggle active"></div>
    </div>

    <div class="settings-row">
      <div>
        <div class="settings-row-label">Require Parent Approval</div>
        <div class="settings-row-sub">For new friend requests & external links</div>
      </div>
      <div class="toggle active"></div>
    </div>

    <button class="btn btn-primary mt-sm" onclick="App.toast('Daily progress PDF report generated! 📄','success')">
      📥 Download Weekly PDF Report
    </button>
  </div>

  <!-- Friend Requests -->
  <div class="glass-card p-lg">
    <h3 class="font-bold text-lg mb-md">👥 Pending Friend Requests</h3>
    <div class="friend-list">
      <div class="friend-item">
        <div class="friend-avatar">S</div>
        <div class="friend-name">Sophia (Grade 5)</div>
        <div class="friend-actions">
          <button class="btn btn-primary btn-sm" onclick="App.toast('Friend approved!','success')">Approve</button>
          <button class="btn btn-danger btn-sm" onclick="App.toast('Request declined','info')">Decline</button>
        </div>
      </div>
      <div class="friend-item">
        <div class="friend-avatar">L</div>
        <div class="friend-name">Liam (Grade 5)</div>
        <div class="friend-actions">
          <button class="btn btn-primary btn-sm" onclick="App.toast('Friend approved!','success')">Approve</button>
          <button class="btn btn-danger btn-sm" onclick="App.toast('Request declined','info')">Decline</button>
        </div>
      </div>
    </div>
  </div>
</div>`;
  }

  function setLimit(day, val) {
    limits[day] = val;
    const label = document.getElementById(`limit-val-${day}`);
    if (label) label.textContent = `${val}m`;
    App.toast(`Limit for ${day} updated to ${val} mins`, 'info');
  }

  function toggleDistraction(el) {
    distractionBlocker = !distractionBlocker;
    el.classList.toggle('active', distractionBlocker);
    App.toast(`Distraction blocker ${distractionBlocker ? 'ENABLED 🛡️' : 'DISABLED ⚠️'}`, distractionBlocker ? 'success' : 'warning');
  }

  function init() {}

  return { render, init, setLimit, toggleDistraction };
})();
