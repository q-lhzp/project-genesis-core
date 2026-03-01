/**
 * Social Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initSocialUI() {
  const root = document.getElementById('plugin-root-social');
  if (!root) return;

  root.innerHTML = `
    <style>
      .soc-container { max-width: 1200px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .soc-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
      .soc-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1rem; }
      
      /* Reputation Meter */
      .rep-meter { display: flex; align-items: center; gap: 1rem; margin-top: 1rem; }
      .rep-track { flex: 1; background: #0a0a0f; height: 24px; border-radius: 12px; overflow: hidden; position: relative; border: 1px solid #1e1e30; }
      .rep-fill { height: 100%; background: linear-gradient(90deg, #e05050, #f0a050, #50c878); transition: width 0.5s; }
      .rep-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: bold; font-size: 0.75rem; color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
      
      /* Contact CRM */
      .contact-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
      .contact-item { background: #0a0a0f; border: 1px solid #1e1e30; padding: 1rem; border-radius: 10px; border-left: 3px solid #7c6ff0; }
      .contact-name { font-weight: bold; font-size: 1rem; color: #eeeef4; margin-bottom: 0.5rem; }
      .contact-stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem; }
      .stat-box { text-align: center; }
      .stat-val { display: block; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: #7c6ff0; }
      .stat-lab { font-size: 0.55rem; color: #6a6a80; text-transform: uppercase; }
      
      /* Feed */
      .feed-list { max-height: 400px; overflow-y: auto; }
      .feed-item { padding: 0.8rem; border-bottom: 1px solid #1e1e30; }
      .feed-meta { display: flex; justify-content: space-between; font-size: 0.7rem; color: #6a6a80; margin-bottom: 0.3rem; }
      .feed-msg { font-size: 0.85rem; line-height: 1.4; color: #c8c8d8; }
      .cat-chat { color: #7c6ff0; }
      .cat-request { color: #f0a050; }
      
      .btn-add { background: #e05050; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; }
    </style>

    <div class="soc-container">
      <!-- Global Reputation -->
      <div class="soc-card">
        <h2>Global Reputation</h2>
        <div class="rep-meter">
          <div class="rep-track">
            <div id="soc-rep-fill" class="rep-fill" style="width: 50%;"></div>
            <div id="soc-rep-text" class="rep-text">Neutral</div>
          </div>
          <span id="soc-rep-score" style="font-size: 1.2rem; font-weight: bold; font-family: 'JetBrains Mono', monospace;">0</span>
        </div>
      </div>

      <!-- CRM -->
      <div class="soc-card" style="border-left: 4px solid #e05050;">
        <h2>Contact CRM <button class="btn-add" style="float: right;">+ New Contact</button></h2>
        <div id="soc-contact-list" class="contact-grid">
          <p style="color: #6a6a80; font-size: 0.8rem;">Loading contacts...</p>
        </div>
      </div>

      <!-- Social Feed -->
      <div class="soc-card" style="border-left: 4px solid #ec4899;">
        <h2>📱 Social Feed</h2>
        <div id="soc-feed-list" class="feed-list">
          <p style="color: #6a6a80; font-size: 0.8rem;">Loading feed...</p>
        </div>
      </div>
    </div>
  `;

  updateSocialDisplay();
  setInterval(updateSocialDisplay, 10000);
}

async function updateSocialDisplay() {
  const contactList = document.getElementById('soc-contact-list');
  const feedList = document.getElementById('soc-feed-list');
  const repFill = document.getElementById('soc-rep-fill');
  const repText = document.getElementById('soc-rep-text');
  const repScore = document.getElementById('soc-rep-score');

  if (!contactList) return;

  try {
    // 1. Fetch Entities
    const eResp = await fetch('/v1/plugins/social/entities');
    const entities = await eResp.json();
    
    if (entities && entities.length > 0) {
      contactList.innerHTML = entities.map(e => `
        <div class="contact-item">
          <div class="contact-name">${e.name} <span style="font-size:0.6rem; color:#6a6a80; font-weight:normal;">(${e.type})</span></div>
          <div class="contact-stats">
            <div class="stat-box"><span class="stat-val">${e.bond}</span><span class="stat-lab">Bond</span></div>
            <div class="stat-box"><span class="stat-val">${e.trust}</span><span class="stat-lab">Trust</span></div>
            <div class="stat-box"><span class="stat-val">${e.intimacy}</span><span class="stat-lab">Intimacy</span></div>
          </div>
        </div>
      `).join('');
      
      // Calculate global rep (simple avg of human bond)
      const humans = entities.filter(e => e.type === 'human');
      const avgBond = humans.length > 0 ? humans.reduce((sum, h) => sum + h.bond, 0) / humans.length : 0;
      repFill.style.width = (50 + avgBond / 2) + '%';
      repScore.textContent = Math.round(avgBond);
      repText.textContent = avgBond > 50 ? "Icon" : (avgBond < -20 ? "Pariah" : "Neutral");
    }

    // 2. Fetch Feed
    const fResp = await fetch('/v1/plugins/social/feed');
    const feed = await fResp.json();
    
    if (feed && feed.length > 0) {
      feedList.innerHTML = feed.map(item => `
        <div class="feed-item">
          <div class="feed-meta">
            <span class="cat-${item.category}">${item.sender_name} • ${item.category.toUpperCase()}</span>
            <span>${item.timestamp.split('T')[1].split('.')[0]}</span>
          </div>
          <div class="feed-msg">${item.message}</div>
        </div>
      `).join('');
    } else {
      feedList.innerHTML = '<div style="color:#6a6a80; font-size:0.75rem; font-style:italic;">No social activities yet.</div>';
    }

  } catch (e) {
    console.error("Social Update Error:", e);
  }
}

// Initialize
setTimeout(initSocialUI, 100);
