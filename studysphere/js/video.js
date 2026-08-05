/* =====================================================
   VIDEO LESSON GENERATOR PAGE — StudySphere
   Multi-style AI Animated Educational Video Generator
   ===================================================== */

const VideoPage = (() => {
  const STYLES = [
    { id: 'cartoon',     name: 'Cartoon Animation', icon: '🎨', desc: 'Friendly characters & fun sound effects' },
    { id: 'whiteboard',  name: 'Whiteboard Draw',   icon: '✏️', desc: 'Hand-drawn diagrams & step explanations' },
    { id: 'motion',      name: 'Motion Graphics',   icon: '📊', desc: 'Sleek 2D graphs & typography' },
    { id: 'storytelling',name: 'Storytelling 2D',   icon: '📖', desc: 'Character-led narrative lesson' },
  ];

  let selectedStyle = 'cartoon';
  let isPlaying = false;
  let animProgress = 0;
  let animTimer = null;

  function render() {
    return `
<div class="section-header">
  <div>
    <div class="section-title">AI Video Lesson Generator</div>
    <div class="section-sub">Upload notes or PDFs to create animated lesson videos automatically</div>
  </div>
  <div class="badge badge-primary">🎬 4K AI Renderer Ready</div>
</div>

<div style="display:grid;grid-template-columns:1fr 1.5fr;gap:var(--sp-xl)">
  <!-- Input Form -->
  <div class="glass-card p-lg" style="display:flex;flex-direction:column;gap:16px">
    <div class="form-group">
      <label class="form-label">Lesson Topic or Text Input</label>
      <textarea class="form-control" id="video-input-text" placeholder="Paste your chapter notes, summary, or PDF text here..." rows="4">The Solar System is composed of the Sun, 8 major planets, dwarf planets, and millions of asteroids. Earth is the 3rd planet, positioned perfectly in the habitable Goldilocks zone.</textarea>
    </div>

    <div class="form-group">
      <label class="form-label">Select Video Style</label>
      <div class="video-style-grid">
        ${STYLES.map(s => `
          <div class="video-style-card ${s.id === selectedStyle ? 'active' : ''}" 
               onclick="VideoPage.setStyle('${s.id}')">
            <div style="font-size:1.8rem">${s.icon}</div>
            <div style="font-weight:700;font-size:var(--fs-sm);margin:4px 0">${s.name}</div>
            <div style="font-size:10px;color:var(--text-muted)">${s.desc}</div>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Narration Voice</label>
      <select class="form-control" id="video-voice">
        <option value="friendly_female">Emma (Friendly & Energetic Female)</option>
        <option value="calm_male">David (Calm & Clear Male)</option>
        <option value="storyteller">Professor Willow (Storyteller Tone)</option>
        <option value="kid_character">Sparky (Cartoon Mascot Kid Voice)</option>
      </select>
    </div>

    <button class="btn btn-primary btn-lg w-full" onclick="VideoPage.generateVideo()">
      🎬 Generate Video Lesson
    </button>
  </div>

  <!-- Player Preview -->
  <div class="glass-card p-lg" style="display:flex;flex-direction:column;gap:16px">
    <div class="video-player-wrap">
      <canvas id="video-canvas" class="video-canvas"></canvas>
      <div id="video-overlay" style="position:relative;z-index:2;text-align:center;color:#fff;pointer-events:none">
        <div style="font-size:3.5rem;margin-bottom:8px">🎬</div>
        <div style="font-weight:700;font-size:var(--fs-lg)">Click Play to Watch Lesson</div>
        <div style="font-size:var(--fs-sm);opacity:0.8">Style: <span id="player-style-label">Cartoon Animation</span></div>
      </div>
    </div>

    <!-- Controls Bar -->
    <div class="video-controls glass-card p-md">
      <button class="btn btn-primary btn-sm btn-icon" onclick="VideoPage.togglePlay()" id="vid-play-btn">▶</button>
      <div class="video-time" id="vid-time-label">0:00 / 0:45</div>
      <div class="video-progress">
        <div class="progress-bar-wrap">
          <div class="progress-bar-fill" id="vid-progress-bar" style="width:0%"></div>
        </div>
      </div>
      <button class="btn btn-ghost btn-sm" onclick="App.toast('Captions enabled 📝','info')">CC</button>
      <button class="btn btn-ghost btn-sm" onclick="VideoPage.showQuizModal()">📝 End Quiz</button>
    </div>
  </div>
</div>`;
  }

  function setStyle(st) {
    selectedStyle = st;
    document.querySelectorAll('.video-style-card').forEach(c => c.classList.remove('active'));
    event.currentTarget.classList.add('active');
    const lbl = document.getElementById('player-style-label');
    if (lbl) lbl.textContent = STYLES.find(s => s.id === st)?.name || st;
  }

  function generateVideo() {
    App.toast('✨ AI is rendering your animated video lesson...', 'info');
    animProgress = 0;
    updateProgressUI();
    setTimeout(() => {
      App.toast('🎬 Video lesson successfully created!', 'success');
      App.addXP(30);
      togglePlay(true);
    }, 1500);
  }

  function togglePlay(forcePlay = false) {
    isPlaying = forcePlay ? true : !isPlaying;
    const btn = document.getElementById('vid-play-btn');
    const overlay = document.getElementById('video-overlay');
    
    if (btn) btn.textContent = isPlaying ? '⏸' : '▶';
    if (overlay) overlay.style.opacity = isPlaying ? '0' : '1';

    if (isPlaying) {
      if (animTimer) clearInterval(animTimer);
      animTimer = setInterval(() => {
        animProgress += 2;
        if (animProgress > 100) {
          animProgress = 100;
          isPlaying = false;
          clearInterval(animTimer);
          if (btn) btn.textContent = '▶';
          if (overlay) overlay.style.opacity = '1';
          App.toast('Lesson video completed! Take the quiz below 🎉', 'success');
        }
        updateProgressUI();
        drawCanvasFrame();
      }, 300);
    } else {
      if (animTimer) clearInterval(animTimer);
    }
  }

  function updateProgressUI() {
    const bar = document.getElementById('vid-progress-bar');
    const label = document.getElementById('vid-time-label');
    if (bar) bar.style.width = `${animProgress}%`;
    if (label) {
      const sec = Math.round((animProgress / 100) * 45);
      label.textContent = `0:${sec < 10 ? '0' + sec : sec} / 0:45`;
    }
  }

  function drawCanvasFrame() {
    const canvas = document.getElementById('video-canvas');
    if (!canvas) return;
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Render animated orbits and planets based on progress
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    
    // Sun
    ctx.beginPath();
    ctx.arc(cx, cy, 30, 0, Math.PI * 2);
    ctx.fillStyle = '#f59e0b';
    ctx.fill();

    // Orbiting Earth
    const angle = (animProgress / 100) * Math.PI * 4;
    const ex = cx + Math.cos(angle) * 100;
    const ey = cy + Math.sin(angle) * 60;

    ctx.beginPath();
    ctx.ellipse(cx, cy, 100, 60, 0, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(ex, ey, 12, 0, Math.PI * 2);
    ctx.fillStyle = '#06b6d4';
    ctx.fill();

    // Text Subtitles
    ctx.fillStyle = '#ffffff';
    ctx.font = '14px Inter';
    ctx.textAlign = 'center';
    const subtitle = animProgress < 33 ? "The Sun rests at the center of our Solar System."
                   : animProgress < 66 ? "Earth completes one full orbit around the Sun in 365 days."
                   : "This orbital path creates our four distinct seasons!";
    ctx.fillText(subtitle, cx, canvas.height - 30);
  }

  function showQuizModal() {
    App.toast('End-of-video quiz unlocked! Answer to claim 20 Gems 💎', 'info');
  }

  function init() {
    drawCanvasFrame();
  }

  return { render, init, setStyle, generateVideo, togglePlay, showQuizModal };
})();
