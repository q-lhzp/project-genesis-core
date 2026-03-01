/**
 * Config Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initConfigUI() {
  const root = document.getElementById('plugin-root-config');
  if (!root) return;

  root.innerHTML = `
    <style>
      .cfg-container { max-width: 800px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .cfg-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; border-left: 4px solid #6a6a80; }
      .cfg-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1.2rem; }
      
      .mac-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
      @media (max-width: 600px) { .mac-grid { grid-template-columns: 1fr; } }
      
      .role-box { background: #0a0a0f; padding: 1rem; border-radius: 8px; border: 1px solid #1e1e30; }
      .role-label { font-size: 0.7rem; color: #7c6ff0; font-weight: bold; text-transform: uppercase; letter-spacing: 0.1em; display: block; margin-bottom: 0.5rem; }
      
      .cfg-select { width: 100%; background: #12121a; color: #eeeef4; border: 1px solid #1e1e30; border-radius: 4px; padding: 0.4rem; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace; }
      
      .btn-save-cfg { background: #50c878; color: white; border: none; padding: 0.8rem 2rem; border-radius: 8px; cursor: pointer; font-weight: bold; margin-top: 2rem; width: 100%; transition: all 0.2s; }
      .btn-save-cfg:hover { background: #45b36b; transform: translateY(-1px); }
    </style>

    <div class="cfg-container">
      <div class="cfg-card">
        <h2>Multi-Agent Cluster (MAC) Configuration</h2>
        <p style="color: #6a6a80; font-size: 0.75rem; margin-bottom: 1.5rem;">Assign specialized AI models to Q's cognitive sub-layers.</p>
        
        <div class="mac-grid">
          <div class="role-box">
            <span class="role-label">Persona (Primary)</span>
            <select id="sel-persona" class="cfg-select"></select>
          </div>
          <div class="role-box">
            <span class="role-label">Limbic (Emotions)</span>
            <select id="sel-limbic" class="cfg-select"></select>
          </div>
          <div class="role-box">
            <span class="role-label">Analyst (Strategy)</span>
            <select id="sel-analyst" class="cfg-select"></select>
          </div>
          <div class="role-box">
            <span class="role-label">Developer (System)</span>
            <select id="sel-developer" class="cfg-select"></select>
          </div>
        </div>

        <button class="btn-save-cfg" onclick="saveMACConfig()">💾 Save MAC Assignments</button>
        <div id="cfg-status" style="margin-top: 1rem; text-align: center; font-size: 0.75rem;"></div>
      </div>
    </div>
  `;

  updateConfigDisplay();
}

async function updateConfigDisplay() {
  try {
    const resp = await fetch('/v1/plugins/config/all');
    const data = await resp.json();

    const roles = ['persona', 'limbic', 'analyst', 'developer'];
    const models = data.available_models || [];

    roles.forEach(role => {
      const sel = document.getElementById(`sel-${role}`);
      if (!sel) return;
      
      sel.innerHTML = models.map(m => `
        <option value="${m.id}" ${data.mac_assignments[role] === m.id ? 'selected' : ''}>${m.name || m.id}</option>
      `).join('');
    });

  } catch (e) {
    console.error("Config Update Error:", e);
  }
}

async function saveMACConfig() {
  const status = document.getElementById('cfg-status');
  const assignments = {
    persona: document.getElementById('sel-persona').value,
    limbic: document.getElementById('sel-limbic').value,
    analyst: document.getElementById('sel-analyst').value,
    developer: document.getElementById('sel-developer').value
  };

  status.textContent = "Updating neural pathways...";
  status.style.color = "#7c6ff0";

  try {
    const resp = await fetch('/v1/plugins/config/save', {
      method: 'POST',
      body: JSON.stringify({ assignments })
    });
    const result = await resp.json();
    if (result.success) {
      status.textContent = "MAC configuration synchronized successfully.";
      status.style.color = "#50c878";
    }
  } catch (e) {
    status.textContent = "Sync error: " + e.message;
    status.style.color = "#e05050";
  }
}

// Initialize
setTimeout(initConfigUI, 100);
window.saveMACConfig = saveMACConfig;
