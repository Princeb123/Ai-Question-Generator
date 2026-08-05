/* =====================================================
   VISUAL LEARNING PAGE — StudySphere
   Interactive SVG Diagrams: Solar System, Human Body, Water Cycle
   ===================================================== */

const DrawingPage = (() => {
  const TOPICS = [
    { id: 'solar', label: '🪐 Solar System' },
    { id: 'body',  label: '🫀 Human Anatomy' },
    { id: 'water', label: '🌧️ Water Cycle' },
  ];

  const DETAILS = {
    solar: {
      sun: { title: '☀️ The Sun', body: 'The star at the heart of our solar system. Contains 99.8% of system mass. Surface temperature is 5,500°C.', facts: ['Age: 4.6 Billion Years', 'Type: Yellow Dwarf Star', 'Core Temp: 15 Million °C'] },
      earth: { title: '🌍 Earth', body: 'The third planet from the Sun and the only astronomical object known to harbor life.', facts: ['Distance from Sun: 149.6 Million km', 'Atmosphere: 78% Nitrogen, 21% Oxygen', 'Moons: 1'] },
      mars: { title: '🔴 Mars', body: 'The dusty, cold, desert world with a very thin atmosphere. Home to Olympus Mons, the largest volcano in the solar system.', facts: ['Moons: Phobos & Deimos', 'Day length: 24h 37m', 'Gravity: 38% of Earth'] },
    },
    body: {
      brain: { title: '🧠 The Brain', body: 'The command center for the human nervous system. Receives signals from sensory organs and controls body activity.', facts: ['Neurons: ~86 Billion', 'Weight: ~1.4 kg', 'Energy consumption: 20% of body power'] },
      heart: { title: '🫀 The Heart', body: 'A muscular organ about the size of a closed fist that pumps blood through the network of blood vessels.', facts: ['Beats per day: ~100,000', 'Blood pumped/day: ~7,500 Liters', 'Chambers: 4'] },
      lungs: { title: '🫁 The Lungs', body: 'A pair of spongy, air-filled organs located on either side of the chest that extract oxygen into the bloodstream.', facts: ['Surface Area: ~70 m²', 'Breaths per day: ~20,000', 'Main muscle: Diaphragm'] },
    },
    water: {
      evaporation: { title: '☀️ Evaporation', body: 'Process where liquid water turns into water vapor gas due to solar heat.', facts: ['Driver: Solar Energy', 'Source: Oceans & Lakes', 'Result: Humidity'] },
      condensation: { title: '☁️ Condensation', body: 'Water vapor cools down high in the atmosphere and turns back into liquid droplets, forming clouds.', facts: ['Creates: Clouds & Fog', 'Trigger: Cooling Temperatures', 'Phase Change: Gas to Liquid'] },
      precipitation: { title: '🌧️ Precipitation', body: 'Water falls from clouds back to Earth as rain, snow, sleet, or hail when droplets become too heavy.', facts: ['Types: Rain, Snow, Hail', 'Gravity driven: Yes', 'Replenishes: Freshwater'] },
    }
  };

  let activeTopic = 'solar';
  let activeHotspot = 'sun';

  function render() {
    return `
<div class="section-header">
  <div>
    <div class="section-title">AI Drawing & Visual Learning</div>
    <div class="section-sub">Interactive SVG diagrams — Click elements to explore deep AI explanations!</div>
  </div>
  <div class="labels-toggle">
    <span>Show Hotspot Glow:</span>
    <div class="toggle active" onclick="this.classList.toggle('active')"></div>
  </div>
</div>

<div class="visual-selector">
  ${TOPICS.map(t => `
    <button class="tab-btn ${t.id === activeTopic ? 'active' : ''}" 
            onclick="DrawingPage.setTopic('${t.id}')">${t.label}</button>
  `).join('')}
</div>

<div class="visual-layout">
  <!-- Interactive SVG Display -->
  <div class="svg-container glass-card" id="svg-display-area">
    ${renderSVG(activeTopic)}
  </div>

  <!-- Detailed AI Info Sidebar -->
  <div class="info-panel glass-card" id="visual-info-panel">
    ${renderInfoPanel(activeTopic, activeHotspot)}
  </div>
</div>`;
  }

  function renderSVG(topic) {
    if (topic === 'solar') {
      return `
<svg viewBox="0 0 500 350" xmlns="http://www.w3.org/2000/svg">
  <!-- Sun -->
  <circle cx="80" cy="175" r="50" fill="#f59e0b" class="svg-hotspot" onclick="DrawingPage.clickHotspot('sun')"/>
  <text x="80" y="180" fill="#fff" font-size="12" font-weight="700" text-anchor="middle" pointer-events="none">Sun</text>

  <!-- Earth Orbit & Body -->
  <ellipse cx="80" cy="175" rx="180" ry="100" fill="none" stroke="rgba(255,255,255,0.15)" stroke-dasharray="4"/>
  <circle cx="260" cy="175" r="18" fill="#06b6d4" class="svg-hotspot" onclick="DrawingPage.clickHotspot('earth')"/>
  <text x="260" y="210" fill="#fff" font-size="11" text-anchor="middle" pointer-events="none">Earth</text>

  <!-- Mars Orbit & Body -->
  <ellipse cx="80" cy="175" rx="300" ry="140" fill="none" stroke="rgba(255,255,255,0.15)" stroke-dasharray="4"/>
  <circle cx="380" cy="175" r="14" fill="#ef4444" class="svg-hotspot" onclick="DrawingPage.clickHotspot('mars')"/>
  <text x="380" y="205" fill="#fff" font-size="11" text-anchor="middle" pointer-events="none">Mars</text>
</svg>`;
    } else if (topic === 'body') {
      return `
<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <!-- Brain -->
  <circle cx="200" cy="70" r="30" fill="#ec4899" class="svg-hotspot" onclick="DrawingPage.clickHotspot('brain')"/>
  <text x="200" y="75" fill="#fff" font-size="11" font-weight="700" text-anchor="middle" pointer-events="none">Brain</text>

  <!-- Lungs -->
  <ellipse cx="170" cy="160" rx="20" ry="35" fill="#3b82f6" class="svg-hotspot" onclick="DrawingPage.clickHotspot('lungs')"/>
  <ellipse cx="230" cy="160" rx="20" ry="35" fill="#3b82f6" class="svg-hotspot" onclick="DrawingPage.clickHotspot('lungs')"/>
  <text x="200" y="165" fill="#fff" font-size="11" font-weight="700" text-anchor="middle" pointer-events="none">Lungs</text>

  <!-- Heart -->
  <circle cx="200" cy="230" r="22" fill="#ef4444" class="svg-hotspot" onclick="DrawingPage.clickHotspot('heart')"/>
  <text x="200" y="235" fill="#fff" font-size="11" font-weight="700" text-anchor="middle" pointer-events="none">Heart</text>
</svg>`;
    } else {
      return `
<svg viewBox="0 0 500 350" xmlns="http://www.w3.org/2000/svg">
  <!-- Sun/Evaporation -->
  <circle cx="400" cy="70" r="35" fill="#f59e0b" class="svg-hotspot" onclick="DrawingPage.clickHotspot('evaporation')"/>
  <text x="400" y="75" fill="#fff" font-size="10" font-weight="700" text-anchor="middle" pointer-events="none">Evaporation</text>

  <!-- Cloud/Condensation -->
  <ellipse cx="200" cy="90" rx="50" ry="25" fill="#94a3b8" class="svg-hotspot" onclick="DrawingPage.clickHotspot('condensation')"/>
  <text x="200" y="94" fill="#fff" font-size="10" font-weight="700" text-anchor="middle" pointer-events="none">Condensation</text>

  <!-- Rain/Precipitation -->
  <rect x="150" y="220" width="100" height="60" rx="10" fill="#0284c7" class="svg-hotspot" onclick="DrawingPage.clickHotspot('precipitation')"/>
  <text x="200" y="255" fill="#fff" font-size="10" font-weight="700" text-anchor="middle" pointer-events="none">Precipitation</text>
</svg>`;
    }
  }

  function renderInfoPanel(topic, hotspot) {
    const data = DETAILS[topic]?.[hotspot] || { title: 'Select Hotspot', body: 'Click any element in the SVG diagram to learn more!', facts: [] };
    return `
<div class="info-panel-title">${data.title}</div>
<div class="info-panel-body">${data.body}</div>
<div class="info-panel-facts">
  <div class="font-bold text-sm mb-xs" style="color:var(--brand-primary)">Key Facts:</div>
  ${data.facts.map(f => `
    <div class="fact-item">
      <span class="fact-bullet">•</span>
      <span>${f}</span>
    </div>
  `).join('')}
</div>`;
  }

  function setTopic(top) {
    activeTopic = top;
    activeHotspot = top === 'solar' ? 'sun' : top === 'body' ? 'brain' : 'evaporation';
    App.navigate('drawing');
  }

  function clickHotspot(spot) {
    activeHotspot = spot;
    const panel = document.getElementById('visual-info-panel');
    if (panel) {
      panel.innerHTML = renderInfoPanel(activeTopic, activeHotspot);
    }
    App.toast(`Inspecting ${spot.toUpperCase()} details! ✨`, 'info');
  }

  function init() {}

  return { render, init, setTopic, clickHotspot };
})();
