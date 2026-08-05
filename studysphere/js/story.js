/* =====================================================
   STORY GENERATOR PAGE — StudySphere
   Choose Your Adventure / Educational Animated Story Generator
   ===================================================== */

const StoryPage = (() => {
  const CATEGORIES = [
    { id: 'science', label: '🔬 Science', color: '#06b6d4' },
    { id: 'history', label: '🏛️ History', color: '#f59e0b' },
    { id: 'math',    label: '📐 Mathematics', color: '#ec4899' },
    { id: 'adventure', label: '🧭 Adventure', color: '#22c55e' },
    { id: 'moral',    label: '✨ Moral & Values', color: '#7c3aed' },
  ];

  const SAMPLE_STORIES = {
    science: {
      title: "The Great Solar Journey of Captain Ray",
      chapter: "Chapter 1: Launch into the Unknown",
      text: "Captain Ray strapped into his rocket suit. Today was the day he would travel from Earth to the Sun! Next to him stood Sol, a friendly photon of light who had lived inside the Sun's core for 100,000 years before finally breaking free.\n\n'Hold tight, Captain!' beamed Sol. 'We're going to explore day, night, and the magical reason why Earth has four distinct seasons!'",
      choices: [
        { text: "Ask Sol why the Sun looks so big from Earth", next: "Sol smiled warm bright light. 'Because Earth is just 93 million miles away! Other stars are trillions of miles further!'" },
        { text: "Fly straight to Earth's equator to check the weather", next: "Ray zoomed to the equator! It was sunny and warm because sunlight hits the equator directly at a high angle all year round." },
        { text: "Spin the Earth on its tilted axis to see what happens", next: "Ray gave Earth a gentle push. As Earth orbited while tilted 23.5 degrees, North America tilted away from the Sun — triggering WINTER!" }
      ]
    },
    history: {
      title: "The Mystery of the Pyramid Builders",
      chapter: "Chapter 1: The Banks of the Nile",
      text: "In ancient Egypt, young Nefertari watched thousands of workers transport massive limestone blocks across the flooding Nile River. The Grand Vizier had just challenged her to solve the riddle of how a 2-ton stone could be lifted up the Great Pyramid of Giza without modern cranes!",
      choices: [
        { text: "Inspect the wet sand in front of the sledges", next: "Nefertari noticed workers pouring water on the sand! Pouring just enough water reduced friction by 50%, allowing sledges to slide easily!" },
        { text: "Examine the long muddy ramps wrapping around the pyramid", next: "She ran up the ramp! The inclined plane made lifting heavy stones easier by spreading the work over a longer distance." }
      ]
    },
    math: {
      title: "The Kingdom of Fractions",
      chapter: "Chapter 1: The Divided Feast",
      text: "King Numerator sat at the round table with 8 hungry knight commanders. A giant golden pizza sat in the center. 'If we divide this pizza into 8 equal slices, each knight gets 1/8!' proclaimed the King. But suddenly, Sir Half-Hearted demanded 2 slices!",
      choices: [
        { text: "Calculate if 2/8 is equivalent to 1/4 of the pizza", next: "King Numerator drew in the air: 2/8 simplify to 1/4! Sir Half-Hearted was asking for exactly a quarter of the feast!" },
        { text: "Offer him 3/12 of a second pizza instead", next: "Sir Half-Hearted was confused, but 3/12 simplifies to 1/4 too! Equivalent fractions saved the feast!" }
      ]
    }
  };

  let currentCategory = 'science';
  let isGenerating = false;

  function render() {
    return `
<div class="section-header">
  <div>
    <div class="section-title">AI Story Generator</div>
    <div class="section-sub">Transform lessons into interactive "Choose Your Adventure" stories!</div>
  </div>
  <div class="badge badge-primary">✨ Powered by AI StoryCraft</div>
</div>

<div class="story-layout">
  <!-- Controls Panel -->
  <div class="glass-card p-lg" style="display:flex;flex-direction:column;gap:16px">
    <div class="form-group">
      <label class="form-label">Story Topic / Subject</label>
      <input class="form-control" id="story-topic" value="The Solar System & Earth's Orbit" placeholder="e.g. Water Cycle, Ancient Rome, Fractions..." />
    </div>

    <div class="form-group">
      <label class="form-label">Target Grade Level</label>
      <select class="form-control" id="story-grade">
        <option value="kindergarten">K-2 (Early Readers & Cartoon Style)</option>
        <option value="primary" selected>Grade 3-5 (Interactive Adventures)</option>
        <option value="middle">Grade 6-8 (Middle School Mystery)</option>
        <option value="high">Grade 9-12 (Advanced Narrative)</option>
      </select>
    </div>

    <div class="form-group">
      <label class="form-label">Story Category</label>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        ${CATEGORIES.map(c => `
          <button class="time-btn ${c.id === currentCategory ? 'active' : ''}" 
                  onclick="StoryPage.setCategory('${c.id}')">${c.label}</button>
        `).join('')}
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Language</label>
      <select class="form-control" id="story-lang">
        <option value="en">English 🇺🇸</option>
        <option value="es">Spanish 🇪🇸</option>
        <option value="fr">French 🇫🇷</option>
        <option value="de">German 🇩🇪</option>
        <option value="hi">Hindi 🇮🇳</option>
      </select>
    </div>

    <button class="btn btn-primary btn-lg w-full" id="gen-story-btn" onclick="StoryPage.generateStory()">
      ✨ Generate AI Story
    </button>
  </div>

  <!-- Story Display Output -->
  <div class="story-output" id="story-display-box">
    ${renderStoryBox(SAMPLE_STORIES.science)}
  </div>
</div>`;
  }

  function renderStoryBox(story) {
    return `
<div class="story-title">${story.title}</div>
<div class="story-chapter">${story.chapter}</div>
<div class="story-text" id="story-animated-text">${story.text.replace(/\n\n/g, '<br><br>')}</div>
<div class="story-choices" id="story-choices-container">
  ${story.choices.map((c, i) => `
    <button class="story-choice" onclick="StoryPage.pickChoice(${i})">
      👉 ${c.text}
    </button>
  `).join('')}
</div>`;
  }

  function setCategory(cat) {
    currentCategory = cat;
    document.querySelectorAll('.story-layout .time-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
  }

  function generateStory() {
    if (isGenerating) return;
    isGenerating = true;

    const topic = document.getElementById('story-topic').value || 'Learning Adventure';
    const box = document.getElementById('story-display-box');
    
    box.innerHTML = `
<div class="story-generating">
  <span style="font-size:2rem">🧙‍♂️</span>
  <div>
    <div style="font-weight:700">AI Storycrafting in progress...</div>
    <div class="story-dots">Weaving topic <em>"${topic}"</em> into an adventure story <span>.</span><span>.</span><span>.</span></div>
  </div>
</div>`;

    setTimeout(() => {
      isGenerating = false;
      const storyData = SAMPLE_STORIES[currentCategory] || SAMPLE_STORIES.science;
      storyData.title = `The Legend of ${topic}`;
      box.innerHTML = renderStoryBox(storyData);
      App.toast('✨ Story generated successfully!', 'success');
      App.addXP(20);
    }, 1800);
  }

  function pickChoice(idx) {
    const storyData = SAMPLE_STORIES[currentCategory] || SAMPLE_STORIES.science;
    const choice = storyData.choices[idx];
    if (!choice) return;

    const choicesContainer = document.getElementById('story-choices-container');
    const textEl = document.getElementById('story-animated-text');

    if (textEl && choicesContainer) {
      textEl.innerHTML += `<br><br><strong style="color:var(--brand-primary)">Your Choice:</strong> ${choice.text}<br><br>🌟 ${choice.next}`;
      choicesContainer.innerHTML = `<div class="badge badge-success">Choice selected! +10 XP earned 🎉</div>`;
      App.toast('Great choice! +10 XP', 'success');
      App.addXP(10);
    }
  }

  function init() {}

  return { render, init, setCategory, generateStory, pickChoice };
})();
