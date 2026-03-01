/**
 * Hobby Engine Plugin Frontend - Interests & Research (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initHobbyUI() {
  const root = document.getElementById('plugin-root-hobby');
  if (!root) return;

  root.innerHTML = `
    <style>
      .hobby-container { max-width: 1000px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .hobby-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
      .hobby-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1rem; }
      
      /* Hobby List */
      .hobby-item { background: #0a0a0f; border: 1px solid #1e1e30; padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem; display: flex; justify-content: space-between; align-items: center; }
      .hobby-topic { font-weight: bold; color: #eeeef4; font-size: 1rem; }
      .hobby-meta { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #6a6a80; margin-top: 0.3rem; }
      .hobby-count { background: rgba(124, 111, 240, 0.15); color: #7c6ff0; padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.75rem; font-weight: bold; }
      
      /* Chips */
      .chip-grid { display: flex; flex-wrap: wrap; gap: 0.6rem; }
      .chip { padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.75rem; font-weight: 500; border: 1px solid #1e1e30; }
      .chip-like { background: rgba(80, 200, 120, 0.1); color: #50c878; border-color: rgba(80, 200, 120, 0.3); }
      .chip-dislike { background: rgba(224, 80, 80, 0.1); color: #e05050; border-color: rgba(224, 80, 80, 0.3); }
      .chip-wish { background: rgba(124, 111, 240, 0.1); color: #7c6ff0; border-color: rgba(124, 111, 240, 0.3); }
      
      .btn-add-hobby { background: #7c6ff0; color: white; border: none; padding: 0.5rem 1.2rem; border-radius: 6px; cursor: pointer; font-size: 0.75rem; font-weight: bold; }
    </style>

    <div class="hobby-container">
      <div class="hobby-card">
        <h2>Active Hobbies & Research <button class="btn-add-hobby" style="float: right;">+ New Topic</button></h2>
        <div id="hobby-list">
          <p style="color: #6a6a80; font-size: 0.8rem;">Loading hobbies...</p>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
        <div class="hobby-card">
          <h2>Likes</h2>
          <div id="likes-grid" class="chip-grid">
            <!-- Chips -->
          </div>
        </div>
        <div class="hobby-card">
          <h2>Dislikes</h2>
          <div id="dislikes-grid" class="chip-grid">
            <!-- Chips -->
          </div>
        </div>
      </div>

      <div class="hobby-card">
        <h2>Neural Wishlist</h2>
        <div id="wishlist-grid" class="chip-grid">
          <!-- Chips -->
        </div>
      </div>
    </div>
  `;

  updateHobbyDisplay();
  setInterval(updateHobbyDisplay, 30000);
}

async function updateHobbyDisplay() {
  const hList = document.getElementById('hobby-list');
  const lGrid = document.getElementById('likes-grid');
  const dGrid = document.getElementById('dislikes-grid');
  const wGrid = document.getElementById('wishlist-grid');

  if (!hList) return;

  try {
    const resp = await fetch('/v1/plugins/hobby/interests');
    const data = await resp.json();

    // 1. Hobbies
    if (data.hobbies && data.hobbies.length > 0) {
      hList.innerHTML = data.hobbies.map(h => `
        <div class="hobby-item">
          <div>
            <div class="hobby-topic">${h.topic}</div>
            <div class="hobby-meta">Discovered: ${h.discoveredAt.split('T')[0]} • Sentiment: ${(h.sentiment * 100).toFixed(0)}%</div>
          </div>
          <div class="hobby-count">${h.researchCount} Sessions</div>
        </div>
      `).join('');
    } else {
      hList.innerHTML = '<p style="color: #6a6a80; font-size: 0.8rem;">No active hobbies found.</p>';
    }

    // 2. Likes
    if (data.likes) {
      lGrid.innerHTML = Object.entries(data.likes).map(([k, v]) => `
        <span class="chip chip-like">${k}</span>
      `).join('');
    }

    // 3. Dislikes
    if (data.dislikes) {
      dGrid.innerHTML = data.dislikes.map(d => `
        <span class="chip chip-dislike">${d}</span>
      `).join('');
    }

    // 4. Wishlist
    if (data.wishlist) {
      wGrid.innerHTML = data.wishlist.map(w => `
        <span class="chip chip-wish">${w}</span>
      `).join('');
    }

  } catch (e) {
    console.error("Hobby Update Error:", e);
  }
}

// Initialize
setTimeout(initHobbyUI, 100);
