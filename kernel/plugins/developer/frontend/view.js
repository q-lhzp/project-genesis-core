/**
 * Developer Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initDeveloperUI() {
  const root = document.getElementById('plugin-root-developer');
  if (!root) return;

  root.innerHTML = `
    <style>
      .dev-container { max-width: 1000px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .dev-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
      .dev-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1rem; }
      
      .proj-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
      .proj-item { background: #0a0a0f; border: 1px solid #1e1e30; padding: 1rem; border-radius: 10px; border-left: 4px solid #10b981; }
      .proj-name { font-weight: bold; font-size: 1rem; color: #eeeef4; margin-bottom: 0.3rem; }
      .proj-desc { font-size: 0.8rem; color: #6a6a80; line-height: 1.4; margin-bottom: 0.8rem; }
      
      .status-tag { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.6rem; font-weight: bold; text-transform: uppercase; font-family: 'JetBrains Mono', monospace; }
      .st-completed { background: rgba(16, 185, 129, 0.15); color: #10b981; }
      .st-implementing { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
      .st-brainstorm { background: rgba(139, 92, 246, 0.15); color: #8b5cf6; }
    </style>

    <div class="dev-container">
      <div class="dev-card">
        <h2>Autonomous Development Manifest</h2>
        <p style="color: #6a6a80; font-size: 0.8rem; margin-bottom: 1.5rem;">Tracking Q's technical self-expansion and tool creation projects.</p>
        
        <div id="project-list" class="proj-grid">
          <p style="color: #6a6a80; font-size: 0.8rem;">Scanning neural repositories...</p>
        </div>
      </div>
    </div>
  `;

  updateDeveloperDisplay();
  setInterval(updateDeveloperDisplay, 20000);
}

async function updateDeveloperDisplay() {
  const list = document.getElementById('project-list');
  if (!list) return;

  try {
    const resp = await fetch('/v1/plugins/developer/projects');
    const data = await resp.json();

    if (data.projects && data.projects.length > 0) {
      list.innerHTML = data.projects.map(p => `
        <div class="proj-item" style="border-left-color: ${getStatusColor(p.status)}">
          <div class="proj-name">${p.name}</div>
          <div class="proj-desc">${p.description}</div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="status-tag st-${p.status}">${p.status}</span>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: #6a6a80;">TYPE: ${p.type.toUpperCase()}</span>
          </div>
        </div>
      `).join('');
    } else {
      list.innerHTML = '<p style="color: #6a6a80; font-size: 0.8rem;">No active development projects.</p>';
    }
  } catch (e) {
    console.error("Developer Update Error:", e);
  }
}

function getStatusColor(status) {
  const colors = {
    completed: '#10b981',
    implementing: '#3b82f6',
    brainstorm: '#8b5cf6',
    planning: '#f59e0b'
  };
  return colors[status] || '#6a6a80';
}

// Initialize
setTimeout(initDeveloperUI, 100);
