/* =====================================================
   LIGHTWEIGHT HTTP BACKEND SERVER & AI PIPELINES
   Zero-dependency Node.js native server (Http + FS + Path)
   ===================================================== */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 4000;
const PUBLIC_DIR = path.join(__dirname, '..');

// Simulated Database State
let userProfile = {
  id: 'usr_1',
  username: 'Alex Johnson',
  email: 'alex@studysphere.edu',
  level: 12,
  xp: 2450,
  stars: 1240,
  coins: 890,
  gems: 42,
  streak: 7,
  preferences: {
    theme: 'dark',
    bgMode: 'particles',
    fontFamily: 'inter',
    fontSize: 'md',
  },
  pet: {
    name: 'Sparky',
    happiness: 4,
  },
  parentControl: {
    dailyLimitMins: 90,
    distractionBlocker: true,
  }
};

const server = http.createServer((req, res) => {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }

  // Parse Body JSON helper
  const parseBody = (cb) => {
    let body = '';
    req.on('data', chunk => body += chunk.toString());
    req.on('end', () => {
      try { cb(body ? JSON.parse(body) : {}); } catch(e) { cb({}); }
    });
  };

  // API ROUTING
  if (req.url.startsWith('/api/')) {
    res.setHeader('Content-Type', 'application/json');

    // GET Profile
    if (req.url === '/api/user/profile' && req.method === 'GET') {
      res.writeHead(200);
      return res.end(JSON.stringify(userProfile));
    }

    // AI Story Pipeline
    if (req.url === '/api/ai/story' && req.method === 'POST') {
      return parseBody((data) => {
        const topic = data.topic || 'The Solar System';
        const response = {
          success: true,
          story: {
            title: `The Legend of ${topic}`,
            chapter: `Chapter 1: The AI Quest (${data.grade || 'Primary'} Level)`,
            text: `Once upon a time, young explorers set out to discover the mysteries of ${topic}. Guided by their AI companion, they noticed how every phenomenon around them followed elegant natural laws!`,
            choices: [
              { text: `Investigate the primary cause of ${topic}`, next: `They discovered that heat and energy transfer were the primary drivers!` },
              { text: `Ask the AI companion for a visual simulation`, next: `A glowing hologram appeared showing the molecular structure in action!` },
            ]
          }
        };
        res.writeHead(200);
        res.end(JSON.stringify(response));
      });
    }

    // AI Video Script Pipeline
    if (req.url === '/api/ai/video-script' && req.method === 'POST') {
      return parseBody((data) => {
        const response = {
          success: true,
          data: {
            topic: data.topic || 'The Solar System',
            style: data.style || 'cartoon',
            durationSeconds: 45,
            script: [
              { time: '0:00', line: `Welcome to our animated lesson on ${data.topic || 'The Solar System'}!` },
              { time: '0:15', line: `Notice how orbital mechanics dictate planet rotation.` },
              { time: '0:35', line: `That concludes our quick overview!` }
            ],
            quiz: [
              { question: `What is the primary star in our Solar System?`, options: ['The Sun', 'Sirius', 'Proxima', 'Alpha Centauri'], correctIndex: 0 }
            ]
          }
        };
        res.writeHead(200);
        res.end(JSON.stringify(response));
      });
    }

    // AI Word Explanation Pipeline
    if (req.url === '/api/ai/explain-word' && req.method === 'POST') {
      return parseBody((data) => {
        const word = (data.word || '').toLowerCase();
        const dict = {
          gravitational: { def: 'The attractive force between physical objects with mass.', trans: 'Gravitacional (Spanish)' },
          photosynthesis: { def: 'Process of turning sunlight into glucose and oxygen.', trans: 'Fotosíntesis (Spanish)' },
          consolidates: { def: 'Combines multiple elements into a unified whole.', trans: 'Consolida (Spanish)' },
        };
        const entry = dict[word] || {
          def: `An essential concept in educational studies referring to ${word}.`,
          trans: `${word} (Multilingual AI Translation)`
        };
        res.writeHead(200);
        res.end(JSON.stringify({ word, ...entry }));
      });
    }

    // Feed Pet Endpoint
    if (req.url === '/api/gamification/pet/feed' && req.method === 'POST') {
      userProfile.pet.happiness = Math.min(userProfile.pet.happiness + 1, 5);
      res.writeHead(200);
      return res.end(JSON.stringify({ success: true, pet: userProfile.pet }));
    }

    // Parent Control Updates
    if (req.url === '/api/parent/controls' && req.method === 'PUT') {
      return parseBody((data) => {
        if (data.dailyLimitMins) userProfile.parentControl.dailyLimitMins = data.dailyLimitMins;
        if (data.distractionBlocker !== undefined) userProfile.parentControl.distractionBlocker = data.distractionBlocker;
        res.writeHead(200);
        res.end(JSON.stringify({ success: true, parentControl: userProfile.parentControl }));
      });
    }

    // Fallback API 404
    res.writeHead(404);
    return res.end(JSON.stringify({ error: 'Endpoint not found' }));
  }

  // STATIC FILE SERVING
  let filePath = path.join(PUBLIC_DIR, req.url === '/' ? 'index.html' : req.url);
  const ext = path.extname(filePath);
  const mimeTypes = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
  };
  const contentType = mimeTypes[ext] || 'text/plain';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      // Fallback to index.html for SPA routing
      fs.readFile(path.join(PUBLIC_DIR, 'index.html'), (err2, indexContent) => {
        if (err2) {
          res.writeHead(500);
          res.end('Server Error');
        } else {
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(indexContent, 'utf-8');
        }
      });
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
    }
  });
});

server.listen(PORT, () => {
  console.log(`🚀 StudySphere Backend & AI Pipelines active on http://localhost:${PORT}`);
});
