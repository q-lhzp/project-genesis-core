/**
 * Genesis Core Dashboard - Core Plugin Loader (v0.1.0)
 */

const API_BASE = ""; // Relative to host

async function initDashboard() {
  const statusEl = document.getElementById('kernel-status');
  const contentEl = document.getElementById('content-area');

  try {
    // 1. Fetch active plugins
    const resp = await fetch('/v1/plugins');
    const plugins = await resp.json();

    statusEl.textContent = `Kernel Online (v7.0) • ${plugins.length} Modules`;
    statusEl.style.color = 'var(--text-dim)';

    // 2. Load Plugins
    plugins.forEach(plugin => {
      // Create Content Container if it doesn't exist
      if (!document.getElementById(`view-${plugin.id}`)) {
        const view = document.createElement('div');
        view.id = `view-${plugin.id}`;
        view.className = 'plugin-view';
        view.innerHTML = `<div id="plugin-root-${plugin.id}">Loading UI...</div>`;
        contentEl.appendChild(view);
      }

      // Load Assets
      if (plugin.ui && plugin.ui.entry) {
        const script = document.createElement('script');
        script.src = `/plugins/${plugin.id}/frontend/${plugin.ui.entry}`;
        if (plugin.ui.is_module) script.type = 'module';
        document.body.appendChild(script);
      }
    });

    // Initial Stats Load
    loadHeaderStats();
    setInterval(loadHeaderStats, 10000);

  } catch (e) {
    statusEl.textContent = 'Kernel Offline';
    statusEl.style.color = '#ef4444';
    console.error("Dashboard Init Error:", e);
  }
}

async function loadHeaderStats() {
  const statsBar = document.getElementById('stats-bar');
  const nameEl = document.getElementById('agent-name');
  if (!statsBar) return;

  try {
    const biosResp = await fetch('/v1/plugins/bios/needs');
    const bios = await biosResp.json();
    
    const idResp = await fetch('/v1/plugins/identity/soul');
    const identity = await idResp.json();

    // Update Name
    if (identity.tree && identity.tree[0]) {
        const namePart = identity.tree[0].children.find(c => c.text.includes('I am'));
        if (namePart) nameEl.textContent = namePart.text.replace('I am', '').trim();
    }

    // Update Stats Bar (Legacy Style)
    if (bios.needs) {
        statsBar.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Energy</span>
                <span class="stat-value" style="color: ${bios.needs.energy < 20 ? '#e05050' : 'var(--growth)'}">${Math.round(bios.needs.energy)}%</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Hunger</span>
                <span class="stat-value" style="color: ${bios.needs.hunger > 80 ? '#e05050' : 'var(--text-bright)'}">${Math.round(bios.needs.hunger)}%</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Cycle</span>
                <span class="stat-value" style="color: var(--accent)">Day ${bios.cycle?.day || 1}</span>
            </div>
        `;
    }
  } catch(e) {}
}

let mindmap = null;

async function loadDefaultView() {
  try {
    // 0. Initialize Mindmap if exists
    if (!mindmap && document.getElementById('soul-mindmap-canvas')) {
      mindmap = new SoulMindmap('soul-mindmap-canvas', 'mm-tooltip');
      document.getElementById('mm-reset').onclick = () => mindmap.fitToVisible(false);
      document.getElementById('mm-fit').onclick = () => mindmap.fitToVisible(false);
    }

    // Load Identity (Soul Map)
    const idResp = await fetch('/v1/plugins/identity/soul');
    const identity = await idResp.json();

    if (identity.success && identity.tree && mindmap) {
      mindmap.setData({ soul_tree: identity.tree });
    }

    // Load Bios (Vitals)
    const biosResp = await fetch('/v1/plugins/bios/needs');
    const bios = await biosResp.json();
    const vitalsResource = document.getElementById('vitals-content');
    if (vitalsResource && bios.needs) {
      const needKeys = ['energy', 'hunger', 'thirst', 'bladder', 'bowel', 'hygiene', 'stress', 'arousal', 'libido'];
      const getVColor = (val, key) => {
          if (key === 'energy') return val < 20 ? '#e05050' : '#50c878';
          return val > 80 ? '#e05050' : '#50c878';
      };

      vitalsResource.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 0.8rem; padding: 0 0.5rem;">
          ${needKeys.map(k => {
            const v = bios.needs[k] ?? 0;
            const color = getVColor(v, k);
            return `
              <div style="display: flex; align-items: center; gap: 0.8rem;">
                <span style="width: 60px; font-family: 'JetBrains Mono'; font-size: 0.6rem; color: var(--text-dim); text-transform: uppercase;">${k}</span>
                <div style="flex: 1; height: 4px; background: #1a1a28; border-radius: 2px; overflow: hidden;">
                  <div style="height: 100%; width: ${v}%; background: ${color}; box-shadow: 0 0 5px ${color}66;"></div>
                </div>
                <span style="width: 25px; font-family: 'JetBrains Mono'; font-size: 0.65rem; color: var(--text-bright); text-align: right;">${Math.round(v)}</span>
              </div>
            `;
          }).join('')}
        </div>
      `;
    }
    // Load Hardware (Resonance)
    const hwResp = await fetch('/v1/plugins/hardware/stats');
    const hw = await hwResp.json();
    const hwResource = document.getElementById('hardware-content');
    if (hwResource && hw.cpu_percent !== undefined) {
        hwResource.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; padding: 0 0.5rem;">
                <div style="background: #0a0a0f; padding: 0.8rem; border-radius: 8px; border: 1px solid var(--border); text-align: center;">
                    <span style="display: block; font-size: 0.55rem; color: var(--text-dim); text-transform: uppercase;">CPU</span>
                    <span style="font-family: 'JetBrains Mono'; font-size: 1rem; color: var(--accent); font-weight: bold;">${Math.round(hw.cpu_percent)}%</span>
                </div>
                <div style="background: #0a0a0f; padding: 0.8rem; border-radius: 8px; border: 1px solid var(--border); text-align: center;">
                    <span style="display: block; font-size: 0.55rem; color: var(--text-dim); text-transform: uppercase;">RAM</span>
                    <span style="font-family: 'JetBrains Mono'; font-size: 1rem; color: var(--accent); font-weight: bold;">${Math.round(hw.memory?.percent || 0)}%</span>
                </div>
                <div style="background: #0a0a0f; padding: 0.8rem; border-radius: 8px; border: 1px solid var(--border); text-align: center;">
                    <span style="display: block; font-size: 0.55rem; color: var(--text-dim); text-transform: uppercase;">TEMP</span>
                    <span style="font-family: 'JetBrains Mono'; font-size: 1rem; color: var(--accent); font-weight: bold;">${hw.cpu_temp_c || 0}°C</span>
                </div>
                <div style="background: #0a0a0f; padding: 0.8rem; border-radius: 8px; border: 1px solid var(--border); text-align: center;">
                    <span style="display: block; font-size: 0.55rem; color: var(--text-dim); text-transform: uppercase;">STATE</span>
                    <span style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: var(--growth); font-weight: bold;">${hw.resonance || 'CALM'}</span>
                </div>
            </div>
        `;
    }

    // Load Timeline (Evolution Proposals)
    const idPropResp = await fetch('/v1/plugins/identity/proposals');
    const idProps = await idPropResp.json();
    const timelineEl = document.getElementById('timeline-content');
    if (timelineEl && idProps.pending) {
        if (idProps.pending.length > 0) {
            timelineEl.innerHTML = `
                <div style="display: flex; flex-direction: column; gap: 0.6rem; padding: 0 0.5rem; text-align: left;">
                    ${idProps.pending.slice(0, 3).map(p => `
                        <div style="border-left: 2px solid var(--accent); padding-left: 0.8rem;">
                            <div style="font-size: 0.6rem; color: var(--text-dim); text-transform: uppercase;">${p.change_type}</div>
                            <div style="font-size: 0.75rem; color: var(--text); line-height: 1.2;">${p.summary}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            timelineEl.innerHTML = '<div style="font-size: 0.75rem; color: var(--text-dim); font-style: italic;">Awaiting next evolution cycle.</div>';
        }
    }

    // Load Life Stream (Latest Images)
    const imgResp = await fetch('/v1/plugins/image_gen/gallery');
    const gallery = await imgResp.json();
    const feedEl = document.getElementById('feed-content');
    if (feedEl && Array.isArray(gallery)) {
        if (gallery.length > 0) {
            feedEl.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; padding: 0 0.5rem;">
                    ${gallery.slice(0, 2).map(img => `
                        <img src="${img.url}" style="width: 100%; height: 120px; object-fit: cover; border-radius: 8px; border: 1px solid var(--border);">
                    `).join('')}
                </div>
                <div style="margin-top: 0.8rem; font-size: 0.7rem; color: var(--text-dim);">Total neural captures: ${gallery.length}</div>
            `;
        } else {
            feedEl.innerHTML = '<div style="font-size: 0.75rem; color: var(--text-dim); font-style: italic;">No visual memories captured.</div>';
        }
    }

    // Load Mental Activity (Logs)
    const mentalEl = document.getElementById('mental-content');
    const logsResp = await fetch('/v1/plugins/diagnostic/logs');
    const logsData = await logsResp.json();
    if (mentalEl && logsData.logs) {
        mentalEl.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 0.4rem; padding: 0 0.5rem; text-align: left; font-family: 'JetBrains Mono'; font-size: 0.65rem;">
                ${logsData.logs.reverse().slice(0, 8).map(line => {
                    try {
                        const entry = JSON.parse(line);
                        const msg = entry.message || entry.event || "Neural pulse detected";
                        return `<div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-dim);">
                            <span style="color: var(--accent)">●</span> ${msg}
                        </div>`;
                    } catch(e) { return ""; }
                }).join('')}
            </div>
        `;
    }

    // Load Proposals (Dashboard)
    const proposalsEl = document.getElementById('proposals-content');
    if (proposalsEl && idProps.pending) {
        if (idProps.pending.length > 0) {
            proposalsEl.innerHTML = idProps.pending.map(p => `
                <div style="background: #0a0a0f; padding: 0.8rem; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 0.5rem;">
                    <div style="font-size: 0.6rem; color: #7c6ff0; text-transform: uppercase; margin-bottom: 0.2rem;">${p.change_type}</div>
                    <div style="font-size: 0.75rem; color: #eeeef4;">${p.summary}</div>
                </div>
            `).join('');
        } else {
            proposalsEl.innerHTML = '<div style="font-size: 0.75rem; color: var(--text-dim); font-style: italic; text-align: center; padding-top: 2rem;">No pending evolution proposals.</div>';
        }
    }
  } catch (e) {
    console.error("Default view load error:", e);
  }
}

function switchTab(id) {
  // Update Buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.id === id);
  });

  // Update Views
  document.querySelectorAll('.plugin-view').forEach(view => {
    view.classList.remove('active');
  });

  const target = document.getElementById(`view-${id}`) || document.getElementById('default-view');
  if (target) {
    target.classList.add('active');
    localStorage.setItem('activePlugin', id);
    if (target.id === 'default-view') {
      loadDefaultView();
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
  loadDefaultView();
});
window.switchTab = switchTab;
