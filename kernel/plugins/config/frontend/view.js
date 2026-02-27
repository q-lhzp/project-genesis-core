/**
 * Config Plugin Frontend - Model & MAC Configuration (v2026.1.0)
 * Provides dynamic model switching via dropdowns for MAC roles.
 */

const ROLES = ["Persona", "Limbic", "Analyst", "Developer"];

async function initConfigUI() {
  const root = document.getElementById('plugin-root-config-engine');
  if (!root) return;

  root.innerHTML = `
    <div style="display:grid; gap:1rem;">
      <h3 style="margin:0;">MAC Role Assignments</h3>
      <p style="color:#888;font-size:0.9rem;">Select models for each agent role. Only configured OpenClaw models are shown.</p>
      <div id="config-roles-grid" style="display:grid; gap:0.75rem;">
        Loading configuration...
      </div>
      <div id="config-status" style="color:#888;font-size:0.85rem;"></div>
    </div>
  `;

  // Initial load
  await updateConfigDisplay();
}

async function updateConfigDisplay() {
  const grid = document.getElementById('config-roles-grid');
  const status = document.getElementById('config-status');
  if (!grid) return;

  try {
    // Fetch both available models and current assignments
    const [configResp, modelsResp] = await Promise.all([
      fetch('/v1/plugins/config/assignments'),
      fetch('/v1/plugins/config/models')
    ]);

    const config = await configResp.json();
    const modelsData = await modelsResp.json();

    const assignments = config.assignments || {};
    const models = modelsData.models || [];

    // Build model options for dropdowns
    const modelOptions = models.map(m =>
      `<option value="${m.key}">${m.name} (${m.key})</option>`
    ).join('');

    // Build role rows
    grid.innerHTML = ROLES.map(role => {
      const currentModel = assignments[role] || '';
      const isCurrentConfigured = models.some(m => m.key === currentModel);

      return `
        <div style="display:flex; align-items:center; gap:0.5rem; padding:0.5rem; background:#1e1e2e;border-radius:6px;">
          <span style="width:80px;font-weight:600;">${role}</span>
          <select
            id="select-${role}"
            style="flex:1; padding:0.4rem; background:#2a2a3a; color:#fff; border:1px solid #3a3a4a; border-radius:4px;"
            onchange="updateRoleModel('${role}', this.value)"
          >
            <option value="">-- Select Model --</option>
            ${models.map(m => `
              <option value="${m.key}" ${m.key === currentModel ? 'selected' : ''}>
                ${m.name}
              </option>
            `).join('')}
          </select>
          ${currentModel && isCurrentConfigured ?
            '<span style="color:#4ade80;font-size:0.8rem;">✓</span>' :
            (currentModel ? '<span style="color:#f87171;font-size:0.8rem;">⚠</span>' : '')}
        </div>
      `;
    }).join('');

    status.textContent = `${models.length} models available • ${Object.keys(assignments).length} roles configured`;

  } catch (e) {
    grid.innerHTML = '<div style="color:#ef4444;">Error loading configuration.</div>';
    console.error("Config Error:", e);
  }
}

async function updateRoleModel(role, model) {
  const status = document.getElementById('config-status');
  if (!status) return;

  try {
    const resp = await fetch('/v1/plugins/config/set_role', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role, model })
    });

    const result = await resp.json();

    if (result.success) {
      status.textContent = `✓ Updated ${role} to ${model}`;
      status.style.color = '#4ade80';

      // Also save to model_config.json
      try {
        const allRoles = {};
        ROLES.forEach(r => {
          const select = document.getElementById(`select-${r}`);
          if (select) allRoles[r] = select.value;
        });
        allRoles[role] = model;

        await fetch('/v1/plugins/config/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(allRoles)
        });
      } catch (e) {
        console.warn("Model config save failed:", e);
      }

      // Also notify the bridge to update
      try {
        await fetch('/v1/tools/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tool: 'mac_set_role_model',
            params: { role: role.toLowerCase(), model }
          })
        });
      } catch (e) {
        console.warn("Bridge notification failed:", e);
      }
    } else {
      status.textContent = `✗ Failed to update: ${result.error}`;
      status.style.color = '#ef4444';
    }

    setTimeout(() => {
      status.style.color = '#888';
    }, 3000);

  } catch (e) {
    status.textContent = `✗ Error: ${e.message}`;
    status.style.color = '#ef4444';
  }
}

// Initialize when container is ready
setTimeout(initConfigUI, 100);
window.updateRoleModel = updateRoleModel;
