/* =====================================================
   FRONTEND API CLIENT — StudySphere
   Connects UI components directly to Express AI & Data Pipelines
   ===================================================== */

const API = (() => {
  const BASE_URL = 'http://localhost:4000/api';

  async function request(endpoint, options = {}) {
    try {
      const res = await fetch(`${BASE_URL}${endpoint}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });
      return await res.json();
    } catch (err) {
      console.warn(`API call failed for ${endpoint}, falling back to local simulation:`, err);
      return null;
    }
  }

  return {
    getProfile: () => request('/user/profile'),
    generateStory: (data) => request('/ai/story', { method: 'POST', body: JSON.stringify(data) }),
    generateVideoScript: (data) => request('/ai/video-script', { method: 'POST', body: JSON.stringify(data) }),
    explainWord: (word) => request('/ai/explain-word', { method: 'POST', body: JSON.stringify({ word }) }),
    feedPet: () => request('/gamification/pet/feed', { method: 'POST' }),
    updateParentControls: (data) => request('/parent/controls', { method: 'PUT', body: JSON.stringify(data) }),
  };
})();
