/* =====================================================
   LEARNING MODES PAGE — StudySphere
   Read, Watch, Listen, Flashcard, Quiz, MindMap, Game, Story
   ===================================================== */

const LearningPage = (() => {
  const MODES = [
    { id: 'read',     label: 'Read',      emoji: '📖' },
    { id: 'watch',    label: 'Watch',     emoji: '📺' },
    { id: 'listen',   label: 'Listen',    emoji: '🎧' },
    { id: 'practice', label: 'Practice',  emoji: '✍️' },
    { id: 'flashcard',label: 'Flashcard', emoji: '🃏' },
    { id: 'quiz',     label: 'Quiz',      emoji: '❓' },
    { id: 'mindmap',  label: 'Mind Map',  emoji: '🧠' },
    { id: 'game',     label: 'Game',      emoji: '🎮' },
    { id: 'story',    label: 'Story',     emoji: '📚' },
  ];

  const FLASHCARDS = [
    { q: 'What is Newton\'s Second Law of Motion?', a: 'F = ma\nForce equals mass times acceleration.' },
    { q: 'What is the powerhouse of the cell?', a: 'The Mitochondria!\nIt produces ATP energy for the cell.' },
    { q: 'What does DNA stand for?', a: 'Deoxyribonucleic Acid\nThe molecule carrying genetic information.' },
    { q: 'What is Photosynthesis?', a: '6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂\nPlants convert light into glucose.' },
    { q: 'What is the speed of light?', a: '≈ 299,792,458 m/s\nOr roughly 3×10⁸ m/s in a vacuum.' },
  ];

  const QUIZ_QUESTIONS = [
    {
      q: 'Which planet is closest to the Sun?',
      opts: ['Venus', 'Mercury', 'Earth', 'Mars'],
      correct: 1,
    },
    {
      q: 'What is the chemical symbol for Gold?',
      opts: ['Go', 'Gd', 'Au', 'Ag'],
      correct: 2,
    },
    {
      q: 'How many bones are in the adult human body?',
      opts: ['198', '206', '212', '220'],
      correct: 1,
    },
    {
      q: 'What is the largest organ in the human body?',
      opts: ['Liver', 'Heart', 'Brain', 'Skin'],
      correct: 3,
    },
    {
      q: 'Which gas do plants absorb from the atmosphere?',
      opts: ['Oxygen', 'Nitrogen', 'Carbon Dioxide', 'Hydrogen'],
      correct: 2,
    },
  ];

  let activeMode = 'read';
  let cardIdx = 0;
  let cardFlipped = false;
  let quizIdx = 0;
  let quizScore = 0;
  let quizTimer = null;
  let quizTimeLeft = 30;
  let answered = false;

  function render() {
    const modeCards = MODES.map(m => `
<div class="mode-card ${m.id === activeMode ? 'active' : ''}" onclick="LearningPage.setMode('${m.id}')">
  <div class="mode-emoji">${m.emoji}</div>
  <div class="mode-name">${m.label}</div>
</div>`).join('');

    return `
<div class="section-header">
  <div>
    <div class="section-title">AI Learning Modes</div>
    <div class="section-sub">Choose how you want to learn today</div>
  </div>
  <div class="badge badge-primary">AI Recommended: Flashcard</div>
</div>
<div class="learning-modes-grid">${modeCards}</div>
<div id="mode-content" class="glass-card p-lg">${renderModeContent()}</div>`;
  }

  function renderModeContent() {
    switch(activeMode) {
      case 'read':      return renderRead();
      case 'watch':     return renderWatch();
      case 'listen':    return renderListen();
      case 'practice':  return renderPractice();
      case 'flashcard': return renderFlashcard();
      case 'quiz':      return renderQuiz();
      case 'mindmap':   return renderMindmap();
      case 'game':      return renderGame();
      case 'story':     return renderStoryMode();
      default:          return renderRead();
    }
  }

  function renderRead() {
    return `
<h3 style="font-family:var(--font-display);font-size:1.4rem;font-weight:800;margin-bottom:16px">📖 The Solar System</h3>
<div style="color:var(--text-secondary);line-height:2;font-size:var(--fs-md)">
  <p>The <strong>Solar System</strong> consists of the <mark style="background:hsla(258,84%,65%,0.2);border-radius:2px;padding:0 2px">Sun</mark> and everything that orbits it, including eight planets, dozens of moons, millions of asteroids, comets, and meteoroids.</p>
  <br>
  <p>The eight planets in order from the Sun are: <strong>Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune</strong>. The inner four planets are rocky while the outer four are gas or ice giants.</p>
  <br>
  <p>The Sun contains <strong>99.86%</strong> of the Solar System's total mass. Its gravitational influence extends well beyond Neptune, keeping all objects in their orbital paths.</p>
  <br>
  <div style="display:flex;gap:8px;flex-wrap:wrap">
    ${['Mercury','Venus','Earth','Mars','Jupiter','Saturn','Uranus','Neptune'].map((p,i)=>`<span style="padding:4px 12px;background:hsla(${(i*45)}%,80%,60%,0.15);border-radius:20px;font-size:var(--fs-sm);font-weight:600;border:1px solid hsla(${i*45},80%,60%,0.3)">${p}</span>`).join('')}
  </div>
</div>
<div style="display:flex;gap:8px;margin-top:16px">
  <button class="btn btn-primary btn-sm" onclick="App.toast('Text-to-Speech started!','info')">🔊 Listen</button>
  <button class="btn btn-ghost btn-sm" onclick="App.toast('Translating...','info')">🌐 Translate</button>
  <button class="btn btn-ghost btn-sm" onclick="App.toast('Summary generated!','success')">✨ Summarize</button>
</div>`;
  }

  function renderWatch() {
    return `
<h3 style="font-family:var(--font-display);font-size:1.4rem;font-weight:800;margin-bottom:16px">📺 Watch Mode</h3>
<div style="background:#000;border-radius:16px;aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;margin-bottom:16px;border:1px solid var(--border-glass)">
  <div style="position:absolute;inset:0;background:radial-gradient(ellipse at center, hsl(230,35%,15%) 0%, #000 100%)"></div>
  <div style="position:relative;text-align:center">
    <div style="font-size:4rem;margin-bottom:8px">🎬</div>
    <div style="font-size:var(--fs-md);color:var(--text-secondary)">AI Video Lesson</div>
    <div style="font-size:var(--fs-sm);color:var(--text-muted)">The Solar System</div>
  </div>
  <button onclick="App.navigate('video')" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:transparent;border:none;cursor:pointer">
    <div style="width:64px;height:64px;border-radius:50%;background:hsla(258,84%,65%,0.9);display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 24px hsla(258,84%,65%,0.5);transition:transform 0.2s" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">▶</div>
  </button>
</div>
<div style="display:flex;gap:8px"><button class="btn btn-primary btn-sm" onclick="App.navigate('video')">🎬 Go to Video Generator</button></div>`;
  }

  function renderListen() {
    return `
<h3 style="font-family:var(--font-display);font-size:1.4rem;font-weight:800;margin-bottom:16px">🎧 Listen Mode</h3>
<div style="text-align:center;padding:24px">
  <div style="width:120px;height:120px;border-radius:50%;background:var(--brand-gradient);display:flex;align-items:center;justify-content:center;font-size:3rem;margin:0 auto 16px;box-shadow:0 0 40px hsla(258,84%,65%,0.4);animation:petBob 2s ease-in-out infinite">🎙️</div>
  <div style="font-size:var(--fs-xl);font-weight:700;margin-bottom:4px">AI Narration</div>
  <div style="color:var(--text-muted);font-size:var(--fs-sm);margin-bottom:24px">The Solar System — Chapter 1</div>
  <div style="display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:16px">
    <button class="btn btn-ghost btn-sm btn-icon" onclick="LearningPage.seekBack()">⏮</button>
    <button class="btn btn-primary" id="listen-play-btn" onclick="LearningPage.toggleListen()">▶ Play</button>
    <button class="btn btn-ghost btn-sm btn-icon" onclick="LearningPage.seekFwd()">⏭</button>
  </div>
  <div style="display:flex;align-items:center;gap:12px">
    <span style="font-size:var(--fs-xs);color:var(--text-muted)">0:00</span>
    <div class="progress-bar-wrap" style="flex:1"><div class="progress-bar-fill" id="listen-progress" style="width:0%;transition:width 0.1s linear"></div></div>
    <span style="font-size:var(--fs-xs);color:var(--text-muted)">3:42</span>
  </div>
  <div style="margin-top:16px;display:flex;align-items:center;justify-content:center;gap:8px">
    <span style="font-size:var(--fs-xs);color:var(--text-muted)">Speed:</span>
    ${[0.5, 0.75, 1, 1.25, 1.5, 2].map(s=>`<button class="time-btn ${s===1?'active':''}" onclick="LearningPage.setSpeed(${s},this)">${s}x</button>`).join('')}
  </div>
</div>`;
  }

  function renderPractice() {
    return `
<h3 style="font-family:var(--font-display);font-size:1.4rem;font-weight:800;margin-bottom:16px">✍️ Interactive Practice</h3>
<div style="display:flex;flex-direction:column;gap:16px">
  <div class="info-card">
    <p style="font-size:var(--fs-sm);color:var(--text-secondary);margin-bottom:12px"><strong>Fill in the blank:</strong> The planet closest to the sun is ___.</p>
    <input class="form-control" placeholder="Type your answer..." id="practice-input" />
    <button class="btn btn-primary btn-sm mt-md" onclick="LearningPage.checkPractice()">Check Answer ✓</button>
  </div>
  <div class="info-card">
    <p style="font-size:var(--fs-sm);color:var(--text-secondary);margin-bottom:12px"><strong>Short Answer:</strong> Explain why Pluto is no longer classified as a planet.</p>
    <textarea class="form-control" placeholder="Write your explanation..." rows="3" id="practice-text"></textarea>
    <button class="btn btn-ghost btn-sm mt-md" onclick="App.toast('AI is evaluating your answer...','info')">Get AI Feedback 🤖</button>
  </div>
</div>`;
  }

  function renderFlashcard() {
    const card = FLASHCARDS[cardIdx];
    return `
<div style="text-align:center;margin-bottom:16px">
  <span style="font-size:var(--fs-sm);color:var(--text-muted)">Card ${cardIdx + 1} of ${FLASHCARDS.length} • Click card to flip</span>
</div>
<div class="flashcard-container">
  <div class="flashcard ${cardFlipped ? 'flipped' : ''}" id="flashcard" onclick="LearningPage.flipCard()">
    <div class="flashcard-front">
      <div class="flashcard-label">Question</div>
      <div class="flashcard-text">${card.q}</div>
      <div class="flashcard-hint">Tap to reveal answer</div>
    </div>
    <div class="flashcard-back">
      <div class="flashcard-label">Answer</div>
      <div class="flashcard-text">${card.a}</div>
    </div>
  </div>
</div>
<div style="display:flex;gap:8px;justify-content:center;margin-top:16px">
  <button class="btn btn-ghost" onclick="LearningPage.prevCard()">← Previous</button>
  <button class="btn btn-danger btn-sm" onclick="LearningPage.markCard('hard')">Hard 😓</button>
  <button class="btn btn-ghost btn-sm" onclick="LearningPage.markCard('medium')">Medium 🤔</button>
  <button class="btn btn-primary btn-sm" onclick="LearningPage.markCard('easy')">Easy 😊</button>
  <button class="btn btn-ghost" onclick="LearningPage.nextCard()">Next →</button>
</div>`;
  }

  function renderQuiz() {
    if (quizIdx >= QUIZ_QUESTIONS.length) return renderQuizResults();
    const q = QUIZ_QUESTIONS[quizIdx];
    return `
<div style="margin-bottom:8px;display:flex;justify-content:space-between;align-items:center">
  <span class="badge badge-primary">Question ${quizIdx + 1} / ${QUIZ_QUESTIONS.length}</span>
  <span style="font-size:var(--fs-sm);color:var(--text-muted)">Score: ${quizScore}</span>
</div>
<div class="quiz-container">
  <div class="quiz-timer-bar"><div class="quiz-timer-fill" id="quiz-timer" style="width:${(quizTimeLeft/30)*100}%"></div></div>
  <div class="quiz-question">${q.q}</div>
  <div class="quiz-options">
    ${q.opts.map((o, i) => `<button class="quiz-option" id="quiz-opt-${i}" onclick="LearningPage.answerQuiz(${i})">${String.fromCharCode(65+i)}. ${o}</button>`).join('')}
  </div>
</div>`;
  }

  function renderQuizResults() {
    const pct = Math.round((quizScore / QUIZ_QUESTIONS.length) * 100);
    const grade = pct >= 80 ? '🏆 Excellent!' : pct >= 60 ? '👍 Good Job!' : '📚 Keep Practicing!';
    return `
<div style="text-align:center;padding:32px">
  <div style="font-size:4rem;margin-bottom:8px">${pct >= 80 ? '🏆' : pct >= 60 ? '🎉' : '💪'}</div>
  <div style="font-family:var(--font-display);font-size:2rem;font-weight:800;margin-bottom:4px">${grade}</div>
  <div style="font-size:3rem;font-weight:800;background:var(--brand-gradient);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin:16px 0">${pct}%</div>
  <div style="color:var(--text-muted);margin-bottom:24px">You answered ${quizScore} out of ${QUIZ_QUESTIONS.length} questions correctly</div>
  <div style="display:flex;gap:8px;justify-content:center">
    <button class="btn btn-primary" onclick="LearningPage.resetQuiz()">🔄 Try Again</button>
    <button class="btn btn-ghost" onclick="App.navigate('gamification')">🎮 View Rewards</button>
  </div>
</div>`;
  }

  function renderMindmap() {
    return `
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
  <h3 style="font-family:var(--font-display);font-size:1.2rem;font-weight:800">🧠 Mind Map: Solar System</h3>
  <div style="display:flex;gap:8px">
    <button class="btn btn-ghost btn-sm" onclick="LearningPage.expandMindmap()">+ Expand</button>
    <button class="btn btn-ghost btn-sm" onclick="App.toast('Mind map exported!','success')">📤 Export</button>
  </div>
</div>
<canvas id="mindmap-canvas"></canvas>`;
  }

  function renderGame() {
    return `
<h3 style="font-family:var(--font-display);font-size:1.4rem;font-weight:800;margin-bottom:16px">🎮 Planet Rush!</h3>
<p style="color:var(--text-secondary);font-size:var(--fs-sm);margin-bottom:16px">Match the planet to its correct description before time runs out!</p>
<div id="game-area" style="display:flex;flex-direction:column;gap:12px"></div>
<div style="display:flex;justify-content:center;margin-top:16px">
  <button class="btn btn-primary" onclick="LearningPage.startGame()">🚀 Start Game</button>
</div>`;
  }

  function renderStoryMode() {
    return `
<h3 style="font-family:var(--font-display);font-size:1.4rem;font-weight:800;margin-bottom:4px">📚 Story Mode</h3>
<p style="color:var(--text-muted);font-size:var(--fs-sm);margin-bottom:16px">Learn through an engaging adventure story!</p>
<div style="padding:24px;background:linear-gradient(135deg,hsla(258,84%,65%,0.1),hsla(190,100%,47%,0.05));border-radius:16px;border:1px solid hsla(258,84%,65%,0.2);font-family:Georgia,serif;line-height:2;margin-bottom:16px">
  <p style="font-style:italic;color:var(--text-secondary)">🌟 <strong style="color:var(--text-primary)">Chapter 1: The Cosmic Journey</strong><br><br>
  Young Maya stepped aboard the <em>Stellar Explorer</em>, her heart racing with excitement. The holographic dashboard lit up, showing their destination: The Solar System Tour.<br><br>
  "First stop," announced ARIA, the ship's AI, "is the smallest and closest planet to the Sun — <strong style="color:var(--brand-secondary)">Mercury</strong>!"<br><br>
  What do you want Maya to do next?</p>
</div>
<div style="display:flex;flex-direction:column;gap:8px">
  <button class="story-choice" onclick="LearningPage.storyChoice(1)">🔭 Ask ARIA about Mercury's temperature</button>
  <button class="story-choice" onclick="LearningPage.storyChoice(2)">🚀 Fly to Mercury immediately</button>
  <button class="story-choice" onclick="LearningPage.storyChoice(3)">📖 Check the ship's encyclopedia first</button>
</div>`;
  }

  // Mode switching
  function setMode(mode) {
    activeMode = mode;
    if (quizTimer) { clearInterval(quizTimer); quizTimer = null; }
    const content = document.getElementById('mode-content');
    if (content) {
      content.style.opacity = 0;
      content.style.transform = 'translateY(8px)';
      content.style.transition = 'all 0.2s';
      setTimeout(() => {
        content.innerHTML = renderModeContent();
        content.style.opacity = 1;
        content.style.transform = 'translateY(0)';
        initMode(mode);
      }, 150);
    }
    document.querySelectorAll('.mode-card').forEach(c => {
      c.classList.toggle('active', c.onclick?.toString().includes(`'${mode}'`));
    });
  }

  function initMode(mode) {
    if (mode === 'quiz') startQuizTimer();
    if (mode === 'mindmap') drawMindmap();
    if (mode === 'game') startGame();
  }

  // Flashcard
  function flipCard() {
    cardFlipped = !cardFlipped;
    const card = document.getElementById('flashcard');
    if (card) card.classList.toggle('flipped', cardFlipped);
  }
  function nextCard() { cardFlipped = false; cardIdx = (cardIdx + 1) % FLASHCARDS.length; updateFlashcard(); }
  function prevCard() { cardFlipped = false; cardIdx = (cardIdx - 1 + FLASHCARDS.length) % FLASHCARDS.length; updateFlashcard(); }
  function markCard(diff) {
    const msgs = { easy: 'Great! Moving to next card 🎉', medium: 'OK, will review again later 👍', hard: 'Added to review list 📌' };
    App.toast(msgs[diff], 'success');
    nextCard();
  }
  function updateFlashcard() {
    const content = document.getElementById('mode-content');
    if (content) { content.innerHTML = renderFlashcard(); }
  }

  // Quiz
  function startQuizTimer() {
    quizTimeLeft = 30;
    if (quizTimer) clearInterval(quizTimer);
    quizTimer = setInterval(() => {
      quizTimeLeft--;
      const bar = document.getElementById('quiz-timer');
      if (bar) bar.style.width = `${(quizTimeLeft / 30) * 100}%`;
      if (quizTimeLeft <= 0) { clearInterval(quizTimer); autoSkipQuiz(); }
    }, 1000);
  }

  function answerQuiz(idx) {
    if (answered) return;
    answered = true;
    if (quizTimer) clearInterval(quizTimer);
    const q = QUIZ_QUESTIONS[quizIdx];
    document.querySelectorAll('.quiz-option').forEach((btn, i) => {
      if (i === q.correct) btn.classList.add('correct');
      else if (i === idx && i !== q.correct) btn.classList.add('wrong');
      btn.disabled = true;
    });
    if (idx === q.correct) { quizScore++; App.toast('✅ Correct! +10 XP', 'success'); App.addXP(10); }
    else App.toast(`❌ Wrong! Correct: ${q.opts[q.correct]}`, 'error');
    setTimeout(() => { quizIdx++; answered = false; const c = document.getElementById('mode-content'); if(c) { c.innerHTML = renderQuiz(); if (quizIdx < QUIZ_QUESTIONS.length) startQuizTimer(); } }, 1500);
  }

  function autoSkipQuiz() {
    answered = false;
    App.toast('⏱️ Time\'s up!', 'warning');
    quizIdx++;
    const c = document.getElementById('mode-content');
    if (c) { c.innerHTML = renderQuiz(); if (quizIdx < QUIZ_QUESTIONS.length) startQuizTimer(); }
  }

  function resetQuiz() { quizIdx = 0; quizScore = 0; answered = false; const c = document.getElementById('mode-content'); if(c) { c.innerHTML = renderQuiz(); startQuizTimer(); } }

  // Mindmap
  function drawMindmap() {
    setTimeout(() => {
      const canvas = document.getElementById('mindmap-canvas');
      if (!canvas) return;
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight || 450;
      const ctx = canvas.getContext('2d');
      const cx = canvas.width / 2, cy = canvas.height / 2;
      const nodes = [
        { x: cx, y: cy, label: 'Solar System', r: 50, color: '#7c3aed', fontSize: 13 },
        { x: cx - 200, y: cy - 120, label: 'Inner Planets', r: 36, color: '#06b6d4', fontSize: 11 },
        { x: cx + 200, y: cy - 120, label: 'Outer Planets', r: 36, color: '#ec4899', fontSize: 11 },
        { x: cx - 200, y: cy + 120, label: 'The Sun', r: 36, color: '#f59e0b', fontSize: 11 },
        { x: cx + 200, y: cy + 120, label: 'Moons', r: 36, color: '#22c55e', fontSize: 11 },
        { x: cx - 280, y: cy - 40, label: 'Mercury', r: 24, color: '#7c3aed', fontSize: 9 },
        { x: cx - 160, y: cy - 220, label: 'Venus', r: 24, color: '#7c3aed', fontSize: 9 },
        { x: cx + 160, y: cy - 220, label: 'Jupiter', r: 24, color: '#ec4899', fontSize: 9 },
        { x: cx + 290, y: cy - 40, label: 'Saturn', r: 24, color: '#ec4899', fontSize: 9 },
      ];
      const edges = [[0,1],[0,2],[0,3],[0,4],[1,5],[1,6],[2,7],[2,8]];

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      // Draw edges
      edges.forEach(([a, b]) => {
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255,255,255,0.1)';
        ctx.lineWidth = 2;
        ctx.moveTo(nodes[a].x, nodes[a].y);
        ctx.lineTo(nodes[b].x, nodes[b].y);
        ctx.stroke();
      });
      // Draw nodes
      nodes.forEach(n => {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = n.color + '33';
        ctx.fill();
        ctx.strokeStyle = n.color;
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = '#fff';
        ctx.font = `${n.fontSize}px Inter`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const words = n.label.split(' ');
        words.forEach((w, i) => ctx.fillText(w, n.x, n.y + (i - (words.length-1)/2) * (n.fontSize+2)));
      });
    }, 100);
  }

  function expandMindmap() { App.toast('Mind map expanded with more concepts!', 'success'); drawMindmap(); }

  // Game
  function startGame() {
    const area = document.getElementById('game-area');
    if (!area) return;
    const planets = [
      { name: 'Mercury', desc: 'Closest to the Sun, no atmosphere' },
      { name: 'Venus', desc: 'Hottest planet, thick CO₂ atmosphere' },
      { name: 'Earth', desc: 'Only known planet with life' },
      { name: 'Mars', desc: 'Red planet, has the largest volcano' },
    ];
    const shuffled = [...planets].sort(() => Math.random() - 0.5);
    area.innerHTML = shuffled.map((p, i) => `
<div style="display:flex;align-items:center;gap:12px;padding:12px;background:var(--bg-glass);border:1px solid var(--border-glass);border-radius:12px;flex-wrap:wrap">
  <span style="font-weight:700;min-width:80px;color:var(--brand-primary)">${p.name}</span>
  <select class="form-control" id="game-sel-${i}" style="flex:1;min-width:200px">
    <option value="">-- Select description --</option>
    ${planets.map(x=>`<option value="${x.name}">${x.desc}</option>`).join('')}
  </select>
</div>`).join('') + `
<button class="btn btn-primary mt-md" onclick="LearningPage.checkGame(${JSON.stringify(shuffled).replace(/"/g,'&quot;')})">Check Answers ✓</button>`;
  }

  function checkGame(planets) {
    let correct = 0;
    planets.forEach((p, i) => {
      const sel = document.getElementById(`game-sel-${i}`);
      if (sel && sel.value === p.name) correct++;
    });
    App.toast(`You got ${correct}/${planets.length} correct! ${correct === planets.length ? '🏆' : '💪'}`, correct === planets.length ? 'success' : 'warning');
    if (correct > 0) App.addXP(correct * 15);
  }

  // Listen
  let listenInterval = null, listenPct = 0, listenPlaying = false;
  function toggleListen() {
    listenPlaying = !listenPlaying;
    const btn = document.getElementById('listen-play-btn');
    if (btn) btn.textContent = listenPlaying ? '⏸ Pause' : '▶ Play';
    if (listenPlaying) {
      listenInterval = setInterval(() => {
        listenPct = Math.min(listenPct + 0.5, 100);
        const bar = document.getElementById('listen-progress');
        if (bar) bar.style.width = listenPct + '%';
        if (listenPct >= 100) { clearInterval(listenInterval); listenPlaying = false; if(btn) btn.textContent = '▶ Play'; App.toast('Chapter complete! 🎉', 'success'); App.addXP(25); }
      }, 200);
    } else clearInterval(listenInterval);
  }
  function seekBack() { listenPct = Math.max(0, listenPct - 10); const bar = document.getElementById('listen-progress'); if(bar) bar.style.width = listenPct + '%'; }
  function seekFwd()  { listenPct = Math.min(100, listenPct + 10); const bar = document.getElementById('listen-progress'); if(bar) bar.style.width = listenPct + '%'; }
  function setSpeed(s, el) { document.querySelectorAll('.time-btn').forEach(b=>b.classList.remove('active')); el.classList.add('active'); App.toast(`Speed set to ${s}x`, 'info'); }

  // Practice
  function checkPractice() {
    const v = (document.getElementById('practice-input') || {}).value || '';
    if (v.toLowerCase().includes('mercury')) App.toast('✅ Correct! Mercury is closest to the Sun.', 'success');
    else if (v.trim().length > 0) App.toast('❌ Not quite. Hint: It starts with M!', 'error');
    else App.toast('Please type an answer first.', 'warning');
  }

  // Story choices
  function storyChoice(c) {
    const NEXT = {
      1: 'ARIA explains: "Mercury\'s surface reaches <strong>430°C</strong> on the day side and drops to <strong>-180°C</strong> at night. Its thin exosphere provides no insulation!" Maya takes notes eagerly.',
      2: 'The Stellar Explorer zooms toward Mercury! Through the viewport, Maya sees a grey, cratered surface — looking just like Earth\'s Moon.',
      3: 'Maya opens the encyclopedia: <em>"Mercury: Diameter 4,879 km. 88 Earth days to orbit the Sun. Named after the Roman messenger god."</em>'
    };
    const story = document.querySelector('.story-choice')?.closest('div');
    if (story) {
      story.previousElementSibling.querySelector('p').innerHTML += `<br><br>🌟 <em style="color:var(--brand-secondary)">${NEXT[c]}</em>`;
      App.toast('Great choice! Story continues... 📖', 'success');
      App.addXP(5);
    }
  }

  function init() { initMode(activeMode); }

  return { render, init, setMode, flipCard, nextCard, prevCard, markCard,
           answerQuiz, resetQuiz, checkPractice, toggleListen, seekBack, seekFwd, setSpeed,
           startGame, checkGame, expandMindmap, storyChoice };
})();
