/* =====================================================
   SETTINGS & ACCESSIBILITY PAGE — StudySphere
   Theme colors, background modes, typography, dyslexia fonts, A11y options
   ===================================================== */

const SettingsPage = (() => {
  function render() {
    const state = ThemeEngine.getState();

    return `
<div class="section-header">
  <div>
    <div class="section-title">Settings & Accessibility</div>
    <div class="section-sub">Customize theme colors, background animations, font styles, and learning preferences</div>
  </div>
</div>

<div class="settings-grid">
  <!-- Appearance Customization -->
  <div class="settings-section">
    <div class="settings-section-title">🎨 Appearance Customization</div>

    <div class="form-group">
      <label class="form-label">Theme Preset</label>
      <div class="theme-cards">
        ${Object.entries(ThemeEngine.THEMES).map(([id, t]) => `
          <div class="theme-card ${state.theme === id ? 'active' : ''}" onclick="ThemeEngine.setTheme('${id}')">
            <div class="theme-card-preview" style="background:${t.preview}"></div>
            <div>${t.label}</div>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Background Animation</label>
      <div class="bg-cards">
        ${Object.entries(ThemeEngine.BG_MODES).map(([id, b]) => `
          <div class="bg-card ${state.bg === id ? 'active' : ''}" onclick="ThemeEngine.setBg('${id}')">
            <div class="bg-preview">${b.emoji}</div>
            <div>${b.label}</div>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Custom Accent Color</label>
      <div class="color-swatches">
        ${ThemeEngine.COLORS.map(c => `
          <div class="color-swatch ${state.color.name === c.name ? 'active' : ''}" 
               style="background:hsl(${c.h},${c.s}%,${c.l}%)"
               title="${c.name}"
               onclick="ThemeEngine.setColor(${JSON.stringify(c).replace(/"/g,'&quot;')})"></div>
        `).join('')}
      </div>
    </div>
  </div>

  <!-- Typography & Focus -->
  <div class="settings-section">
    <div class="settings-section-title">🔤 Typography & Modes</div>

    <div class="form-group">
      <label class="form-label">Font Family Selection</label>
      <div class="font-grid">
        ${ThemeEngine.FONTS.map(f => `
          <div class="font-pill ${state.font === f ? 'active' : ''}" 
               onclick="ThemeEngine.setFont('${f}')">${ThemeEngine.FONT_LABELS[f]}</div>
        `).join('')}
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Font Size Adjustment</label>
      <div class="time-btn-group">
        ${Object.entries(ThemeEngine.FONT_SIZES).map(([sz, px]) => `
          <button class="time-btn ${state.fontsize === sz ? 'active' : ''}" 
                  onclick="ThemeEngine.setFontSize('${sz}')">${sz.toUpperCase()} (${px})</button>
        `).join('')}
      </div>
    </div>

    <div class="settings-row">
      <div>
        <div class="settings-row-label">Reading Mode (Warm Sepia)</div>
        <div class="settings-row-sub">Reduces eye strain during long reading sessions</div>
      </div>
      <div class="toggle ${state.readingMode ? 'active' : ''}" onclick="ThemeEngine.toggleReadingMode()"></div>
    </div>

    <div class="settings-row">
      <div>
        <div class="settings-row-label">Focus Mode (Distraction Free)</div>
        <div class="settings-row-sub">Dims background elements for total concentration</div>
      </div>
      <div class="toggle ${state.focusMode ? 'active' : ''}" onclick="ThemeEngine.toggleFocusMode()"></div>
    </div>
  </div>

  <!-- Accessibility Suite -->
  <div class="settings-section">
    <div class="settings-section-title">♿ Accessibility Suite</div>

    <div class="a11y-features">
      <div class="a11y-item">
        <div class="a11y-label">
          <div class="a11y-title">Dyslexia-Friendly Font (Lexend)</div>
          <div class="a11y-desc">Designed to reduce visual stress and improve readability</div>
        </div>
        <div class="toggle ${state.dyslexicFont ? 'active' : ''}" onclick="ThemeEngine.toggleDyslexicFont()"></div>
      </div>

      <div class="a11y-item">
        <div class="a11y-label">
          <div class="a11y-title">High Contrast Mode</div>
          <div class="a11y-desc">Maximum contrast ratio for visually impaired learners</div>
        </div>
        <div class="toggle ${state.theme === 'high-contrast' ? 'active' : ''}" onclick="ThemeEngine.setTheme('high-contrast')"></div>
      </div>

      <div class="a11y-item">
        <div class="a11y-label">
          <div class="a11y-title">Screen Reader Enhancements</div>
          <div class="a11y-desc">Optimized ARIA live zones & semantic landmarks</div>
        </div>
        <div class="toggle active"></div>
      </div>

      <div class="a11y-item">
        <div class="a11y-label">
          <div class="a11y-title">Speech-to-Text Input</div>
          <div class="a11y-desc">Dictate answers & story prompts via microphone</div>
        </div>
        <div class="toggle active"></div>
      </div>
    </div>
  </div>
</div>`;
  }

  function init() {}

  return { render, init };
})();
