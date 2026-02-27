/**
 * Bios Plugin Frontend - View Module (v0.1.0)
 */

async function initBiosUI() {
  const root = document.getElementById('plugin-root-bios-engine');
  if (!root) return;

  root.innerHTML = `
    <div style="display:grid; gap:1rem;">
      <div id="bios-needs-grid" style="display:grid; gap:0.5rem;">
        Loading needs...
      </div>
      <div style="display:flex; gap:0.5rem; margin-top:1rem;">
        <button onclick="triggerBiosAction('eat')">🍕 Eat</button>
        <button onclick="triggerBiosAction('drink')">💧 Drink</button>
        <button onclick="triggerBiosAction('sleep')">😴 Sleep</button>
      </div>
    </div>
  `;

  // Start Update Loop
  updateBiosDisplay();
  setInterval(updateBiosDisplay, 5000);
}

async function updateBiosDisplay() {
  const grid = document.getElementById('bios-needs-grid');
  if (!grid) return;

  try {
    const resp = await fetch('/v1/state/physique');
    const data = await resp.json();
    const needs = data.needs || {};

    grid.innerHTML = Object.entries(needs).map(([name, val]) => `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="text-transform:capitalize;">${name}</span>
        <div style="flex:1; height:8px; background:#2a2a3a; margin:0 1rem; border-radius:4px; overflow:hidden;">
          <div style="width:${val}%; height:100%; background:var(--accent);"></div>
        </div>
        <span style="width:40px; text-align:right;">${Math.round(val)}%</span>
      </div>
    `).join('');
  } catch (e) {
    grid.innerHTML = '<div style="color:#ef4444;">Error fetching needs.</div>';
  }
}

async function triggerBiosAction(action) {
  try {
    await fetch('/v1/plugins/bios/action', {
      method: 'POST',
      body: JSON.stringify({ action })
    });
    updateBiosDisplay();
  } catch (e) {
    console.error("Action Error:", e);
  }
}

// Initialize when container is ready
setTimeout(initBiosUI, 100);
window.triggerBiosAction = triggerBiosAction;
