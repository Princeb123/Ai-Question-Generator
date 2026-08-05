/* =====================================================
   READING ASSISTANT PAGE — StudySphere
   Text-to-Speech, Live Word Translator & Comprehension Checker
   ===================================================== */

const ReadingPage = (() => {
  const DICTIONARY = {
    gravitational: { def: 'The force that attracts a body toward the center of the earth or toward any other physical body having mass.', trans: 'Gravitacional (Spanish)' },
    consolidates:  { def: 'Combines multiple things into a single, stronger, or more coherent whole.', trans: 'Consolida (Spanish)' },
    photosynthesis:{ def: 'The process by which green plants use sunlight to synthesize nutrients from carbon dioxide and water.', trans: 'Fotosíntesis (Spanish)' },
    habitable:    { def: 'Suitable or good enough for living in.', trans: 'Habitable (Spanish)' },
  };

  let isReading = false;
  let ttsUtterance = null;

  function render() {
    return `
<div class="section-header">
  <div>
    <div class="section-title">AI Reading Assistant</div>
    <div class="section-sub">Read books aloud, explain complex words, translate text & test comprehension!</div>
  </div>
  <div class="badge badge-primary">🗣️ Web Speech Synthesis API Active</div>
</div>

<!-- Controls Bar -->
<div class="tts-controls">
  <button class="btn btn-primary btn-sm" id="tts-play-btn" onclick="ReadingPage.toggleReadAloud()">
    🔊 Read Aloud
  </button>
  <button class="btn btn-ghost btn-sm" onclick="ReadingPage.stopReadAloud()">
    ⏹️ Stop
  </button>
  <div style="display:flex;align-items:center;gap:6px;margin-left:auto">
    <span class="tts-speed-label">Speed:</span>
    <select class="form-control" style="padding:2px 8px;width:auto" id="tts-rate-sel">
      <option value="0.75">0.75x (Slow)</option>
      <option value="1" selected>1.0x (Normal)</option>
      <option value="1.25">1.25x (Fast)</option>
      <option value="1.5">1.5x (Very Fast)</option>
    </select>
  </div>
</div>

<div class="reading-layout">
  <!-- Book Content Container -->
  <div class="book-reader">
    <div class="book-title">Journey to the Center of Science</div>
    <div class="book-chapter">Chapter 3: The Forces of Nature</div>
    <div class="book-text" id="book-reader-content">
      All objects in the universe exert a <span class="word-btn" onclick="ReadingPage.explainWord('gravitational', this)">gravitational</span> pull on one another. The strength of this pull depends on two main factors: mass and distance.
      <br><br>
      During the night, your brain <span class="word-btn" onclick="ReadingPage.explainWord('consolidates', this)">consolidates</span> memories from the day, storing key lessons into long-term memory.
      <br><br>
      Plants sustain life on Earth through <span class="word-btn" onclick="ReadingPage.explainWord('photosynthesis', this)">photosynthesis</span>, converting sunlight into clean oxygen and organic compounds.
      <br><br>
      Earth sits in the ideal <span class="word-btn" onclick="ReadingPage.explainWord('habitable', this)">habitable</span> zone, allowing liquid water to exist continuously on its surface.
    </div>
  </div>

  <!-- Side Panel: Comprehension & AI Tools -->
  <div class="comprehension-panel">
    <div class="glass-card p-lg">
      <h3 style="font-weight:700;font-size:var(--fs-md);margin-bottom:12px">❓ Comprehension Check</h3>
      <div class="comp-q">
        <div class="comp-q-text">What two factors determine the strength of gravitational pull?</div>
        <input class="form-control comp-q-input" id="comp-ans-1" placeholder="Type answer..." />
        <button class="btn btn-ghost btn-sm mt-sm" onclick="ReadingPage.checkAns(1)">Verify Answer ✓</button>
      </div>
      <div class="comp-q mt-md">
        <div class="comp-q-text">What does photosynthesis convert sunlight into?</div>
        <input class="form-control comp-q-input" id="comp-ans-2" placeholder="Type answer..." />
        <button class="btn btn-ghost btn-sm mt-sm" onclick="ReadingPage.checkAns(2)">Verify Answer ✓</button>
      </div>
    </div>
  </div>
</div>

<!-- Word Explanation Popup (Hidden initially) -->
<div class="word-popup hidden" id="word-pop">
  <div class="word-popup-title" id="pop-word">Word</div>
  <div class="word-popup-def" id="pop-def">Definition goes here...</div>
  <div class="word-popup-translate" id="pop-trans">Translation</div>
  <button class="btn btn-primary btn-sm mt-md w-full" onclick="ReadingPage.closePop()">Close</button>
</div>`;
  }

  function explainWord(word, element) {
    const data = DICTIONARY[word];
    if (!data) return;

    const pop = document.getElementById('word-pop');
    const wordEl = document.getElementById('pop-word');
    const defEl = document.getElementById('pop-def');
    const transEl = document.getElementById('pop-trans');

    if (pop && wordEl && defEl && transEl) {
      wordEl.textContent = word.toUpperCase();
      defEl.textContent = data.def;
      transEl.textContent = `🌐 ${data.trans}`;
      
      const rect = element.getBoundingClientRect();
      pop.style.top = `${rect.bottom + 8}px`;
      pop.style.left = `${Math.min(rect.left, window.innerWidth - 300)}px`;
      pop.classList.remove('hidden');
    }
  }

  function closePop() {
    const pop = document.getElementById('word-pop');
    if (pop) pop.classList.add('hidden');
  }

  function toggleReadAloud() {
    if (!('speechSynthesis' in window)) {
      App.toast('Speech synthesis is not supported in this browser.', 'error');
      return;
    }

    if (isReading) {
      window.speechSynthesis.pause();
      isReading = false;
      document.getElementById('tts-play-btn').textContent = '🔊 Read Aloud';
    } else {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      } else {
        const text = document.getElementById('book-reader-content')?.innerText || '';
        ttsUtterance = new SpeechSynthesisUtterance(text);
        const rate = parseFloat(document.getElementById('tts-rate-sel')?.value || 1);
        ttsUtterance.rate = rate;
        
        ttsUtterance.onend = () => {
          isReading = false;
          document.getElementById('tts-play-btn').textContent = '🔊 Read Aloud';
        };

        window.speechSynthesis.speak(ttsUtterance);
      }
      isReading = true;
      document.getElementById('tts-play-btn').textContent = '⏸️ Pause';
    }
  }

  function stopReadAloud() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      isReading = false;
      const btn = document.getElementById('tts-play-btn');
      if (btn) btn.textContent = '🔊 Read Aloud';
    }
  }

  function checkAns(qNum) {
    const input = document.getElementById(`comp-ans-${qNum}`);
    const val = (input?.value || '').toLowerCase();

    if (qNum === 1 && (val.includes('mass') || val.includes('distance'))) {
      App.toast('✅ Correct! Mass and distance dictate gravity!', 'success');
      App.addXP(15);
    } else if (qNum === 2 && (val.includes('oxygen') || val.includes('nutrient') || val.includes('glucose'))) {
      App.toast('✅ Correct! Plants produce oxygen & nutrients!', 'success');
      App.addXP(15);
    } else {
      App.toast('❌ Not quite! Give it another try.', 'warning');
    }
  }

  function init() {}

  return { render, init, explainWord, closePop, toggleReadAloud, stopReadAloud, checkAns };
})();
