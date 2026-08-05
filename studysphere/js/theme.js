/* =====================================================
   THEME ENGINE — StudySphere
   ===================================================== */

const ThemeEngine = (() => {
  const root = document.documentElement;

  const THEMES = {
    dark:          { label: '🌙 Dark',          preview: 'linear-gradient(135deg,#0f1629,#1a1a2e)' },
    light:         { label: '☀️ Light',         preview: 'linear-gradient(135deg,#f0f4ff,#e8ecf8)' },
    'high-contrast':{ label: '⚡ High Contrast', preview: 'linear-gradient(135deg,#000,#111)' },
    colorblind:    { label: '👁️ Colorblind',    preview: 'linear-gradient(135deg,#0066cc,#ff7700)' },
  };

  const BG_MODES = {
    particles: { label: '✨ Particles', emoji: '✨' },
    aurora:    { label: '🌌 Aurora',    emoji: '🌌' },
    geometric: { label: '🔷 Geometric', emoji: '🔷' },
    space:     { label: '🚀 Space',     emoji: '🚀' },
  };

  const COLORS = [
    { h: 258, s: 84, l: 65, name: 'Violet' },
    { h: 190, s: 100, l: 47, name: 'Cyan' },
    { h: 142, s: 76, l: 45, name: 'Green' },
    { h: 328, s: 86, l: 65, name: 'Pink' },
    { h: 231, s: 98, l: 65, name: 'Blue' },
    { h: 38,  s: 92, l: 50, name: 'Amber' },
    { h: 0,   s: 84, l: 62, name: 'Red' },
  ];

  const FONTS = ['inter', 'outfit', 'nunito', 'poppins', 'space', 'lexend'];
  const FONT_LABELS = { inter: 'Inter', outfit: 'Outfit', nunito: 'Nunito', poppins: 'Poppins', space: 'Space Grotesk', lexend: 'Lexend' };
  const FONT_SIZES = { sm: '14px', md: '16px', lg: '18px', xl: '20px' };

  let state = {
    theme: 'dark',
    bg: 'particles',
    color: COLORS[0],
    font: 'inter',
    fontsize: 'md',
    readingMode: false,
    focusMode: false,
    highContrast: false,
    dyslexicFont: false,
  };

  function load() {
    const saved = localStorage.getItem('ss_theme');
    if (saved) {
      try { state = { ...state, ...JSON.parse(saved) }; } catch(e) {}
    }
    apply();
  }

  function save() {
    localStorage.setItem('ss_theme', JSON.stringify(state));
  }

  function apply() {
    // Theme
    root.setAttribute('data-theme', state.theme);
    root.setAttribute('data-bg', state.bg);
    root.setAttribute('data-font', state.dyslexicFont ? 'lexend' : state.font);
    root.setAttribute('data-fontsize', state.fontsize);

    // Custom color
    const c = state.color;
    root.style.setProperty('--brand-primary', `hsl(${c.h},${c.s}%,${c.l}%)`);
    root.style.setProperty('--brand-gradient', `linear-gradient(135deg,hsl(${c.h},${c.s}%,${c.l}%) 0%,hsl(${(c.h+130)%360},${Math.min(c.s+10,100)}%,${Math.max(c.l-10,30)}%) 100%)`);

    // Reading mode
    document.body.classList.toggle('reading-mode', state.readingMode);

    // Focus mode
    const fOverlay = document.getElementById('focus-overlay');
    if (fOverlay) fOverlay.classList.toggle('active', state.focusMode);

    // Theme toggle icons
    const dark  = document.getElementById('theme-icon-dark');
    const light = document.getElementById('theme-icon-light');
    if (dark && light) {
      dark.classList.toggle('hidden', state.theme === 'light');
      light.classList.toggle('hidden', state.theme !== 'light');
    }

    save();

    // Restart particles if needed
    if (window.ParticleSystem) ParticleSystem.restart();
  }

  function setTheme(t) { state.theme = t; apply(); }
  function toggleTheme() { setTheme(state.theme === 'dark' ? 'light' : 'dark'); }
  function setBg(b) { state.bg = b; apply(); }
  function setColor(c) { state.color = c; apply(); }
  function setFont(f) { state.font = f; apply(); }
  function setFontSize(s) { state.fontsize = s; apply(); }
  function toggleReadingMode() { state.readingMode = !state.readingMode; apply(); }
  function toggleFocusMode() { state.focusMode = !state.focusMode; apply(); }
  function toggleDyslexicFont() { state.dyslexicFont = !state.dyslexicFont; apply(); }

  return { load, apply, setTheme, toggleTheme, setBg, setColor, setFont, setFontSize,
           toggleReadingMode, toggleFocusMode, toggleDyslexicFont,
           THEMES, BG_MODES, COLORS, FONTS, FONT_LABELS, FONT_SIZES,
           getState: () => state };
})();
