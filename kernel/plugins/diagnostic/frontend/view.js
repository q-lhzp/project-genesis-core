/**
 * Diagnostic Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initDiagnosticUI() {
  const root = document.getElementById('plugin-root-diagnostic');
  if (!root) return;

  root.innerHTML = `
    <style>
      .diag-container { max-width: 1200px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .diag-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
      .diag-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1.2rem; }
      
      .plugin-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1rem; }
      .plugin-item { background: #0a0a0f; border: 1px solid #1e1e30; padding: 1rem; border-radius: 10px; }
      .plugin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; }
      .plugin-name { font-weight: bold; color: #eeeef4; font-size: 0.9rem; }
      .plugin-status { font-size: 0.6rem; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: bold; text-transform: uppercase; }
      .status-online { background: rgba(80, 200, 120, 0.15); color: #50c878; }
      
      .endpoint-list { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #6a6a80; list-style: none; padding: 0; }
      .endpoint-item { display: flex; justify-content: space-between; padding: 0.3rem 0; border-bottom: 1px solid #1a1a28; }
      .endpoint-ok { color: #50c878; }
      
      .btn-verify { background: #e05050; color: white; border: none; padding: 0.8rem 2rem; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; transition: all 0.2s; }
      .btn-verify:hover { background: #c04040; box-shadow: 0 5px 15px rgba(224, 80, 80, 0.3); }
    </style>

    <div class="diag-container">
      <div class="diag-card">
        <h2>Neural Core Integrity</h2>
        <div id="plugin-health-list" class="plugin-grid">
          <p style="color: #6a6a80; font-size: 0.8rem;">Analyzing system health...</p>
        </div>
      </div>

      <div class="diag-card" style="border-left: 4px solid #e05050;">
        <h2>Global Security Audit</h2>
        <p style="color: #6a6a80; font-size: 0.8rem; margin-bottom: 1.5rem;">Trigger a full verification of data flows and domain isolation.</p>
        <button class="btn-verify" onclick="triggerGlobalVerify()">Run Integrity Check</button>
        <div id="verify-status" style="margin-top: 1rem; text-align: center; font-size: 0.75rem; color: #6a6a80;"></div>
      </div>
    </div>
  `;

  updateDiagnosticDisplay();
}

async function updateDiagnosticDisplay() {
  const list = document.getElementById('plugin-health-list');
  if (!list) return;

  try {
    const resp = await fetch('/v1/plugins/diagnostic/health');
    const data = await resp.json();

    if (data.plugins) {
      list.innerHTML = Object.entries(data.plugins).map(([id, p]) => `
        <div class="plugin-item">
          <div class="plugin-header">
            <span class="plugin-name">${p.name} <span style="font-size:0.6rem; color:#6a6a80;">v${p.version}</span></span>
            <span class="plugin-status status-online">${p.backend}</span>
          </div>
          <div class="endpoint-list">
            ${p.endpoints.map(e => `
              <div class="endpoint-item">
                <span>${e.route}</span>
                <span class="endpoint-ok">${e.status}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `).join('');
    }
  } catch (e) {
    console.error("Diagnostic Update Error:", e);
  }
}

async function triggerGlobalVerify() {
  const status = document.getElementById('verify-status');
  status.textContent = "Initiating global audit... checking 14 domains...";
  try {
    const resp = await fetch('/v1/plugins/diagnostic/verify', { method: 'POST' });
    const result = await resp.json();
    status.textContent = result.message;
    status.style.color = "#50c878";
  } catch (e) {
    status.textContent = "Audit failed: " + e.message;
    status.style.color = "#e05050";
  }
}

// Initialize
setTimeout(initDiagnosticUI, 100);
window.triggerGlobalVerify = triggerGlobalVerify;
