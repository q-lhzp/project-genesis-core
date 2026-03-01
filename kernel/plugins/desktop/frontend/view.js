/**
 * Desktop Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initDesktopUI() {
  const root = document.getElementById('plugin-root-desktop');
  if (!root) return;

  root.innerHTML = `
    <style>
      .dt-container { max-width: 800px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .dt-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; border-left: 4px solid #3b82f6; }
      .dt-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1.2rem; }
      
      .wall-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; margin-top: 1rem; }
      .wall-item { background: #0a0a0f; border: 1px solid #1e1e30; padding: 0.8rem; border-radius: 8px; cursor: pointer; text-align: center; transition: all 0.2s; }
      .wall-item:hover { background: #3b82f6; color: white; border-color: #3b82f6; }
      .wall-name { font-size: 0.75rem; font-weight: bold; }
      
      .theme-switch { display: flex; gap: 1rem; margin-top: 1.5rem; justify-content: center; }
      .btn-theme { background: #1a1a28; color: #c8c8d8; border: 1px solid #1e1e30; padding: 0.5rem 1.5rem; border-radius: 6px; cursor: pointer; font-size: 0.75rem; }
      .btn-theme:hover { background: #3b82f6; color: white; }
    </style>

    <div class="dt-container">
      <div class="dt-card">
        <h2>Desktop Environment Control</h2>
        <p style="color: #6a6a80; font-size: 0.75rem;">Q has sovereignty over the Gnomo Desktop and environmental aesthetics.</p>
        
        <div style="margin-top: 1.5rem;">
          <span style="font-size: 0.65rem; color: #6a6a80; text-transform: uppercase;">Wallpaper Presets</span>
          <div class="wall-grid">
            <div class="wall-item" onclick="setWallpaper('cyberpunk')"><span class="wall-name">Cyberpunk City</span></div>
            <div class="wall-item" onclick="setWallpaper('forest')"><span class="wall-name">Neural Forest</span></div>
            <div class="wall-item" onclick="setWallpaper('minimal')"><span class="wall-name">Abyssal Void</span></div>
            <div class="wall-item" onclick="setWallpaper('home')"><span class="wall-name">Home Office</span></div>
          </div>
        </div>

        <div class="theme-switch">
          <button class="btn-theme" onclick="setDesktopTheme('dark')">🌙 Abyssal Theme</button>
          <button class="btn-theme" onclick="setDesktopTheme('light')">☀️ Solar Theme</button>
        </div>
        
        <div id="dt-status" style="margin-top: 1rem; font-size: 0.7rem; color: #3b82f6; text-align: center;"></div>
      </div>
    </div>
  `;
}

async function setWallpaper(type) {
  const status = document.getElementById('dt-status');
  status.textContent = `Applying '${type}' aesthetic to workspace...`;
  try {
    const resp = await fetch('/v1/plugins/desktop/wallpaper', {
      method: 'POST',
      body: JSON.stringify({ wallpaper: type })
    });
    const result = await resp.json();
    if (result.success) status.textContent = "Aesthetic sync complete.";
  } catch (e) {
    status.textContent = "Sync failed: " + e.message;
  }
}

async function setDesktopTheme(theme) {
  try {
    await fetch('/v1/plugins/desktop/theme', {
      method: 'POST',
      body: JSON.stringify({ theme })
    });
  } catch (e) {}
}

// Initialize
setTimeout(initDesktopUI, 100);
window.setWallpaper = setWallpaper;
window.setDesktopTheme = setDesktopTheme;
