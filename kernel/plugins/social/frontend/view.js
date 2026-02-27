/**
 * Social Intelligence Frontend - View Module (v1.0.0)
 */

async function initSocialUI() {
  const root = document.getElementById('plugin-root-social-engine');
  if (!root) return;

  root.innerHTML = `
    <div style="display:grid; grid-template-columns: 1.5fr 1fr; gap:2rem;">
      <div class="panel-card">
        <h3>👤 Contact CRM</h3>
        <div id="social-entities" style="display:grid; gap:1rem; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));">
          Loading contacts...
        </div>
        <button onclick="addNewContact()" style="margin-top:1.5rem; width:100%; padding:0.5rem; background:var(--accent); color:#fff; border:none; cursor:pointer;">+ Add Contact</button>
      </div>
      
      <div class="panel-card">
        <h3>📱 Social Feed</h3>
        <div id="social-feed" style="display:grid; gap:0.75rem; height:400px; overflow-y:auto; font-size:0.9rem;">
          No activity recorded.
        </div>
      </div>
    </div>
  `;

  updateSocialDisplay();
  setInterval(updateSocialDisplay, 15000);
}

async function updateSocialDisplay() {
  try {
    // 1. Load Entities
    const entResp = await fetch('/v1/plugins/social/entities');
    const entData = await entResp.json();
    const entEl = document.getElementById('social-entities');
    entEl.innerHTML = (entData.entities || []).map(e => `
      <div style="background:#0a0a12; padding:1rem; border-radius:8px; text-align:center; border:1px solid #2a2a3a;">
        <div style="font-size:2rem; margin-bottom:0.5rem;">👤</div>
        <strong>${e.name || e.entity_name}</strong>
        <div style="font-size:0.7rem; color:#888;">${e.relationship_type || 'Acquaintance'}</div>
        <div style="margin-top:0.5rem; height:4px; background:#222; border-radius:2px; overflow:hidden;">
          <div style="width:${(e.bond || 0) * 10}%; height:100%; background:#7c6ff0;"></div>
        </div>
      </div>
    `).join('') || 'No contacts yet.';

    // 2. Load Feed
    const feedResp = await fetch('/v1/plugins/social/feed');
    const feedData = await feedResp.json();
    const feedEl = document.getElementById('social-feed');
    feedEl.innerHTML = feedData.map(post => `
      <div style="background:#0a0a12; padding:0.75rem; border-radius:6px; border-left:3px solid var(--accent);">
        <small style="color:#666;">${new Date(post.timestamp).toLocaleTimeString()}</small>
        <div style="margin-top:0.25rem;">${post.content}</div>
      </div>
    `).join('') || 'Feed empty.';

  } catch (e) { console.error("Social UI Error:", e); }
}

async function addNewContact() {
  const name = prompt("Name of the person:");
  if (!name) return;
  try {
    await fetch('/v1/plugins/social/add', {
      method: 'POST',
      body: JSON.stringify({ name, relationship_type: 'Friend', bond: 1 })
    });
    updateSocialDisplay();
  } catch (e) {}
}

setTimeout(initSocialUI, 100);
window.addNewContact = addNewContact;
