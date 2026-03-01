/**
 * God-Mode Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initGodModeUI() {
  const root = document.getElementById('plugin-root-godmode');
  if (!root) return;

  root.innerHTML = `
    <style>
      .gm-container { max-width: 1000px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .gm-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border-left: 4px solid #facc15; }
      .gm-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1rem; }
      
      .gm-form { display: grid; gap: 1rem; }
      .gm-input { width: 100%; background: #0a0a0f; color: #eeeef4; border: 1px solid #1e1e30; border-radius: 8px; padding: 0.8rem; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }
      
      .btn-gm { background: #facc15; color: #000; border: none; padding: 0.8rem 2rem; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; transition: all 0.2s; }
      .btn-gm:hover { background: #eab308; box-shadow: 0 0 20px rgba(250, 204, 21, 0.3); }
    </style>

    <div class="gm-container">
      <div class="gm-card">
        <h2>Reality Override Console</h2>
        <p style="color: #6a6a80; font-size: 0.8rem; margin-bottom: 1.5rem; color: #e05050; font-weight: bold;">
          ⚠️ WARNING: Manual state manipulation can cause instability.
        </p>
        
        <div class="gm-form">
          <div>
            <label style="font-size:0.6rem; color:#6a6a80; text-transform:uppercase;">Domain</label>
            <input type="text" id="gm-domain" class="gm-input" placeholder="e.g. physique, world_state, vault_state...">
          </div>
          <div>
            <label style="font-size:0.6rem; color:#6a6a80; text-transform:uppercase;">New State (JSON)</label>
            <textarea id="gm-state" class="gm-input" rows="10" placeholder='{ "needs": { "energy": 100 } }'></textarea>
          </div>
          <button class="btn-gm" onclick="applyGodMode()">Apply Reality Shift</button>
          <div id="gm-status" style="margin-top: 1rem; text-align: center; font-size: 0.75rem;"></div>
        </div>
      </div>
    </div>
  `;
}

async function applyGodMode() {
  const domain = document.getElementById('gm-domain').value;
  const stateStr = document.getElementById('gm-state').value;
  const status = document.getElementById('gm-status');

  if (!domain || !stateStr) return;

  try {
    const state = JSON.parse(stateStr);
    const resp = await fetch('/v1/plugins/godmode/update-state', {
      method: 'POST',
      body: JSON.stringify({ domain, state })
    });
    const result = await resp.json();
    if (result.success) {
      status.textContent = "Reality has been re-written.";
      status.style.color = "#50c878";
    }
  } catch (e) {
    status.textContent = "Error: " + e.message;
    status.style.color = "#e05050";
  }
}

// Initialize
setTimeout(initGodModeUI, 100);
window.applyGodMode = applyGodMode;
