/* =====================================================
   GAMIFICATION PAGE — StudySphere
   Avatars, Virtual Pet System, Badges, Daily Missions & Certificates
   ===================================================== */

const GamificationPage = (() => {
  const AVATARS = [
    { id: 'a1', name: 'Astro Cat', icon: '🐱', cost: 0, unlocked: true },
    { id: 'a2', name: 'Cyber Fox', icon: '🦊', cost: 0, unlocked: true },
    { id: 'a3', name: 'Wizard Owl', icon: '🦉', cost: 100, unlocked: false },
    { id: 'a4', name: 'Robo Bear', icon: '🐻', cost: 200, unlocked: false },
    { id: 'a5', name: 'Cosmic Dragon', icon: '🐲', cost: 500, unlocked: false },
    { id: 'a6', name: 'Galactic Unicorn', icon: '🦄', cost: 1000, unlocked: false },
  ];

  const BADGES = [
    { id: 'b1', name: 'Quick Learner', emoji: '⚡', desc: 'Finish 5 lessons in 1 day', earned: true },
    { id: 'b2', name: 'Streak Master', emoji: '🔥', desc: 'Maintain a 7-day streak', earned: true },
    { id: 'b3', name: 'Quiz Champion', emoji: '🏆', desc: 'Score 100% on 3 quizzes', earned: true },
    { id: 'b4', name: 'Bookworm', emoji: '📚', desc: 'Read 10 chapters in Assistant', earned: false },
    { id: 'b5', name: 'AI Explorer', emoji: '🤖', desc: 'Try all 9 AI Learning Modes', earned: false },
  ];

  const MISSIONS = [
    { id: 'm1', title: 'Watch 1 Video Lesson', reward: 50, done: true },
    { id: 'm2', title: 'Complete 1 AI Quiz with >80%', reward: 100, done: false },
    { id: 'm3', title: 'Read 1 Chapter in Reading Assistant', reward: 50, done: false },
    { id: 'm4', title: 'Interact with 3 Visual Hotspots', reward: 30, done: true },
  ];

  let petHappiness = 4; // 1 to 5

  function render() {
    return `
<div class="section-header">
  <div>
    <div class="section-title">Gamified Rewards & Fun Zone</div>
    <div class="section-sub">Earn XP, unlock avatars, care for your virtual pet, and complete daily missions!</div>
  </div>
</div>

<!-- Hero Stats Strip -->
<div class="gamification-hero">
  <div style="font-size:4rem">🏆</div>
  <div>
    <div class="player-title">Level 12 Scholar</div>
    <div class="player-sub">Keep learning daily to level up!</div>
  </div>
  <div class="hero-stats">
    <div class="hero-stat">
      <div class="hero-stat-val">⭐ 1,240</div>
      <div class="hero-stat-label">Stars</div>
    </div>
    <div class="hero-stat">
      <div class="hero-stat-val">🪙 890</div>
      <div class="hero-stat-label">Coins</div>
    </div>
    <div class="hero-stat">
      <div class="hero-stat-val">💎 42</div>
      <div class="hero-stat-label">Gems</div>
    </div>
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-xl);margin-bottom:var(--sp-xl)">
  <!-- Virtual Pet Widget -->
  <div class="glass-card p-lg pet-container text-center">
    <h3 class="font-bold text-lg mb-md">🐱 Virtual Study Companion: "Sparky"</h3>
    <div class="pet-wrap">
      <div class="pet-body">⚡</div>
      <div class="pet-mood">🥰</div>
    </div>
    <div class="pet-name">Sparky</div>
    <div class="pet-happiness">
      ${Array.from({ length: 5 }).map((_, i) => `
        <span class="pet-heart">${i < petHappiness ? '❤️' : '🖤'}</span>
      `).join('')}
    </div>
    <p class="text-sm text-muted mt-sm">Sparky grows happier every time you complete lessons!</p>
    <div class="flex gap-sm justify-center mt-md">
      <button class="btn btn-primary btn-sm" onclick="GamificationPage.feedPet()">🍎 Feed Pet (10 Coins)</button>
      <button class="btn btn-ghost btn-sm" onclick="GamificationPage.petCompanion()">🫳 Pet Companion</button>
    </div>
  </div>

  <!-- Daily Missions -->
  <div class="glass-card p-lg">
    <h3 class="font-bold text-lg mb-md">🎯 Daily Missions</h3>
    <div class="mission-list">
      ${MISSIONS.map(m => `
        <div class="mission-item ${m.done ? 'done' : ''}">
          <div class="mission-check" onclick="GamificationPage.toggleMission('${m.id}')">
            ${m.done ? '✓' : ''}
          </div>
          <div class="mission-text">${m.title}</div>
          <div class="mission-reward">+${m.reward} XP</div>
        </div>
      `).join('')}
    </div>
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-xl)">
  <!-- Avatar Gallery -->
  <div class="glass-card p-lg">
    <h3 class="font-bold text-lg mb-md">🎭 Unlockable Avatars</h3>
    <div class="avatar-gallery">
      ${AVATARS.map(a => `
        <div class="avatar-item ${a.unlocked ? '' : 'locked'}" onclick="GamificationPage.selectAvatar('${a.id}')">
          <div style="font-size:2.5rem">${a.icon}</div>
          <div style="font-weight:600;font-size:12px;margin-top:4px">${a.name}</div>
          ${a.unlocked ? '<div class="badge badge-success" style="font-size:9px">Owned</div>' : `<div class="avatar-price">🪙 ${a.cost}</div>`}
        </div>
      `).join('')}
    </div>
  </div>

  <!-- Badge Wall -->
  <div class="glass-card p-lg">
    <h3 class="font-bold text-lg mb-md">🏅 Achievement Badges</h3>
    <div class="badge-wall">
      ${BADGES.map(b => `
        <div class="badge-item ${b.earned ? 'earned' : 'locked-badge'}">
          <div class="badge-emoji">${b.emoji}</div>
          <div class="badge-title">${b.name}</div>
          <div style="font-size:10px;color:var(--text-muted);margin-top:2px">${b.desc}</div>
        </div>
      `).join('')}
    </div>
  </div>
</div>`;
  }

  function feedPet() {
    if (petHappiness < 5) {
      petHappiness++;
      App.toast('🍎 You fed Sparky! Sparky is super happy now!', 'success');
      App.navigate('gamification');
    } else {
      App.toast('Sparky is already full and happy! 🥰', 'info');
    }
  }

  function petCompanion() {
    App.toast('⚡ Sparky purrs happily!', 'success');
  }

  function toggleMission(mId) {
    const m = MISSIONS.find(x => x.id === mId);
    if (m) {
      m.done = !m.done;
      if (m.done) {
        App.toast(`Mission completed! +${m.reward} XP earned! 🎉`, 'success');
        App.addXP(m.reward);
      }
      App.navigate('gamification');
    }
  }

  function selectAvatar(aId) {
    const avatar = AVATARS.find(x => x.id === aId);
    if (!avatar) return;
    if (avatar.unlocked) {
      App.toast(`Avatar changed to ${avatar.name}! ${avatar.icon}`, 'success');
    } else {
      App.toast(`Unlock ${avatar.name} for 🪙 ${avatar.cost} Coins!`, 'warning');
    }
  }

  function init() {}

  return { render, init, feedPet, petCompanion, toggleMission, selectAvatar };
})();
