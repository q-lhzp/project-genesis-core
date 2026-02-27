/**
 * Genesis Core Dashboard - Core Plugin Loader (v0.1.0)
 */

const API_BASE = ""; // Relative to host

async function initDashboard() {
  const statusEl = document.getElementById('kernel-status');
  const menuEl = document.getElementById('sidebar-menu');
  const contentEl = document.getElementById('content-area');

  try {
    // 1. Fetch active plugins
    const resp = await fetch('/v1/plugins');
    const plugins = await resp.json();
    
    statusEl.textContent = `Kernel Online (v0.1.0) - ${plugins.length} Plugins`;
    statusEl.style.color = '#10b981';

    // 2. Load Plugins
    plugins.forEach(plugin => {
      if (!plugin.ui) return;

      // Create Sidebar Button
      const btn = document.createElement('button');
      btn.className = 'tab-btn';
      btn.innerHTML = `<span>${plugin.ui.icon || '🧩'}</span> ${plugin.name}`;
      btn.onclick = () => switchTab(plugin.id);
      menuEl.appendChild(btn);

      // Create Content Container
      const view = document.createElement('div');
      view.id = `view-${plugin.id}`;
      view.className = 'plugin-view';
      view.innerHTML = `<h2>${plugin.name}</h2><div id="plugin-root-${plugin.id}">Loading UI...</div>`;
      contentEl.appendChild(view);

      // Load Assets
      if (plugin.ui.entry) {
        const script = document.createElement('script');
        script.src = `/plugins/${plugin.id}/frontend/${plugin.ui.entry}`;
        // Support modules if specified
        if (plugin.ui.is_module) script.type = 'module';
        document.body.appendChild(script);
      }
    });

  } catch (e) {
    statusEl.textContent = 'Kernel Offline';
    statusEl.style.color = '#ef4444';
    console.error("Dashboard Init Error:", e);
  }
}

function switchTab(id) {
  // Update Buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.textContent.includes(id)) btn.classList.add('active');
  });

  // Update Views
  document.querySelectorAll('.plugin-view').forEach(view => {
    view.classList.remove('active');
  });
  
  const target = document.getElementById(`view-${id}`) || document.getElementById('default-view');
  if (target) target.classList.add('active');
}

document.addEventListener('DOMContentLoaded', initDashboard);
window.switchTab = switchTab;
