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
      try {
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
          script.onerror = () => console.warn(`Failed to load plugin script: ${plugin.id}`);
          document.body.appendChild(script);
        }
      } catch (err) {
        console.error(`Error initialization plugin ${plugin.id}:`, err);
      }
    });

    // Initial Stats Load
    loadHeaderStats();
    setInterval(loadHeaderStats, 10000);

    // Start Clock
    startClock();

    // Start Diagnostics
    pulseCheck();
    setInterval(pulseCheck, 5000);

    // Bind Mindmap Toggle
    const mmToggle = document.getElementById('mm-toggle-bar');
    if (mmToggle) {
      mmToggle.onclick = () => {
        const list = document.getElementById('soul-map-list');
        const canvas = document.getElementById('soul-map-canvas-container');
        const isCanvas = canvas.style.display === 'block';

        list.style.display = isCanvas ? 'block' : 'none';
        canvas.style.display = isCanvas ? 'none' : 'block';

        mmToggle.querySelector('.growth-label span:nth-child(2)').textContent = isCanvas ? 'Open Soul Mindmap' : 'Back to Soul Map';
      };
    }

  } catch (e) {
    statusEl.textContent = 'Kernel Offline';
    statusEl.style.color = '#ef4444';
    console.error("Dashboard Init Error:", e);
  }
}

function startClock() {
  const clockEl = document.getElementById('clock');
  if (!clockEl) return;
  setInterval(() => {
    clockEl.textContent = new Date().toLocaleTimeString('en-GB', { hour12: false });
  }, 1000);
}

async function loadHeaderStats() {
  const statsBar = document.getElementById('stats-bar');
  const nameEl = document.getElementById('agent-name');
  if (!statsBar) return;

  try {
    const biosResp = await fetch('/v1/plugins/bios/needs');
    if (!biosResp.ok) throw new Error("Bios unreachable");
    const bios = await biosResp.json();

    const idResp = await fetch('/v1/plugins/identity/soul');
    if (!idResp.ok) throw new Error("Identity unreachable");
    const identity = await idResp.json();

    // Update Name
    if (identity.tree && identity.tree[0]) {
      const namePart = identity.tree[0].children.find(c => c.text.includes('I am'));
      if (namePart) nameEl.textContent = namePart.text.replace('I am', '').trim();
    }

    // Update Stats Bar (Legacy Style)
    if (bios.needs && statsBar) {
      const stats = statsBar.querySelectorAll('.stat .num');
      if (stats.length >= 6) {
        // Mapping to the labels: Experiences, Reflections, Web Searches, World News, Core, Mutable
        stats[0].textContent = identity.reflection_count || 0;
        stats[1].textContent = identity.reflection_count || 0;
        stats[2].textContent = identity.search_count || 0;
        stats[3].textContent = identity.news_count || 0;
        stats[4].textContent = identity.core_count || 20;
        stats[5].textContent = identity.mutable_count || 10;
      }
    }
  } catch (e) {
    console.error("Header Stats Error:", e);
  }
}

// Data Pulse Diagnostics
async function pulseCheck() {
  const endpoints = [
    { name: 'Plugins', url: '/v1/plugins' },
    { name: 'Bios', url: '/v1/plugins/bios/needs' },
    { name: 'Identity', url: '/v1/plugins/identity/soul' },
    { name: 'Hardware', url: '/v1/plugins/hardware/stats' },
    { name: 'Proposals', url: '/v1/plugins/identity/proposals' },
    { name: 'Gallery', url: '/v1/plugins/image_gen/gallery' },
    { name: 'Logs', url: '/v1/plugins/diagnostic/logs' }
  ];

  const pulseContainer = document.getElementById('debug-pulse');
  if (!pulseContainer) return;

  const results = await Promise.all(endpoints.map(async (ep) => {
    try {
      const start = performance.now();
      const resp = await fetch(ep.url);
      const end = performance.now();
      return { ...ep, ok: resp.ok, status: resp.status, time: Math.round(end - start) };
    } catch (e) {
      return { ...ep, ok: false, status: 'ERR', time: 0 };
    }
  }));

  pulseContainer.innerHTML = results.map(r => `
    <div style="display: flex; justify-content: space-between; font-size: 0.6rem; color: ${r.ok ? 'var(--growth)' : '#ef4444'}; margin-bottom: 2px;">
      <span>${r.name}:</span>
      <span>${r.time}ms [${r.status}]</span>
    </div>
  `).join('');
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
    if (idResp.ok) {
      const identity = await idResp.json();
      if (identity.success) {
        // Schema Normalization: handle both 'tree' and 'parsed'
        const treeData = identity.tree || identity.parsed || [];
        if (mindmap) mindmap.setData({ soul_tree: treeData });
        renderSoulMapList(treeData);
      }
    }

    // Load Bios (Vitals)
    const biosResp = await fetch('/v1/plugins/bios/needs');
    if (biosResp.ok) {
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
    }

    // Load Hardware (Resonance)
    const hwResp = await fetch('/v1/plugins/hardware/stats');
    if (hwResp.ok) {
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
    }

    // Load Timeline (Evolution Proposals)
    const idPropResp = await fetch('/v1/plugins/identity/proposals');
    if (idPropResp.ok) {
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
    }

    // Load Life Stream (Latest Images)
    const imgResp = await fetch('/v1/plugins/image_gen/gallery');
    if (imgResp.ok) {
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
    }

    // Load Mental Activity (Logs)
    const mentalEl = document.getElementById('mental-content');
    const logsResp = await fetch('/v1/plugins/diagnostic/logs');
    if (logsResp.ok && mentalEl) {
      const logsData = await logsResp.json();
      if (logsData.logs) {
        mentalEl.innerHTML = `
                <div style="display: flex; flex-direction: column; gap: 0.4rem; padding: 0 0.5rem; text-align: left; font-family: 'JetBrains Mono'; font-size: 0.65rem;">
                    ${logsData.logs.reverse().slice(0, 8).map(line => {
          try {
            const entry = JSON.parse(line);
            const msg = entry.message || entry.event || "Neural pulse detected";
            return `<div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-dim);">
                                    <span style="color: var(--accent)">●</span> ${msg}
                                </div>`;
          } catch (e) { return ""; }
        }).join('')}
                </div>
            `;
      }
    }
  } catch (e) {
    console.error("Default view load error:", e);
  }
}

function renderSoulMapList(tree) {
  const listEl = document.getElementById('soul-map-content');
  if (!listEl) return;

  listEl.innerHTML = tree.map(section => `
        <div class="section-block" onclick="this.classList.toggle('active')">
            <div class="section-header">
                <div class="dot" style="background: ${section.color || 'var(--accent)'}"></div>
                ${section.text}
                <span class="arrow">▼</span>
            </div>
            <div class="section-body">
                ${section.children ? section.children.map(child => `
                    <div class="subsection">
                        <div class="subsection-title">${child.text}</div>
                        ${child.children ? child.children.map(bullet => `
                            <div class="bullet">
                                <span class="tag ${bullet.type || 'mutable'}">${(bullet.type || 'mutable').toUpperCase()}</span>
                                <span>${bullet.text}</span>
                            </div>
                        `).join('') : ''}
                    </div>
                `).join('') : ''}
            </div>
        </div>
    `).join('');
}

function switchTab(id, subAction) {
  const buttons = document.querySelectorAll('.tab-btn');
  buttons.forEach(btn => {
    if (subAction) {
      btn.classList.toggle('active', btn.textContent.toLowerCase().trim() === subAction.toLowerCase());
    } else {
      btn.classList.toggle('active', btn.dataset.id === id);
    }
  });

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
    if (subAction) {
      window.dispatchEvent(new CustomEvent('plugin-tab-switch', { detail: { pluginId: id, subAction } }));
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
  loadDefaultView();
});
window.switchTab = switchTab;
