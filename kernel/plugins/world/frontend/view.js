/**
 * World Engine Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initWorldUI() {
  const root = document.getElementById('plugin-root-world');
  if (!root) return;

  root.innerHTML = `
    <style>
      .world-container { max-width: 800px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; text-align: center; }
      .world-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 2rem; position: relative; overflow: hidden; }
      
      .weather-icon { font-size: 4rem; margin-bottom: 1rem; filter: drop-shadow(0 0 15px rgba(124, 111, 240, 0.3)); }
      .weather-status { font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; font-weight: bold; text-transform: uppercase; color: #eeeef4; letter-spacing: 0.1em; }
      
      .world-stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 2rem; border-top: 1px solid #1e1e30; padding-top: 1.5rem; }
      .w-stat-box { display: flex; flex-direction: column; gap: 0.3rem; }
      .w-stat-val { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; color: #7c6ff0; font-weight: bold; }
      .w-stat-lab { font-size: 0.65rem; color: #6a6a80; text-transform: uppercase; letter-spacing: 0.05em; }
      
      .lighting-badge { display: inline-block; margin-top: 1.5rem; padding: 0.4rem 1rem; border-radius: 20px; background: rgba(124, 111, 240, 0.1); color: #7c6ff0; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; border: 1px solid rgba(124, 111, 240, 0.3); }
    </style>

    <div class="world-container">
      <div class="world-card">
        <div id="world-icon" class="weather-icon">🌤️</div>
        <div id="world-status" class="weather-status">Synchronizing...</div>
        
        <div id="world-lighting" class="lighting-badge">Daylight</div>

        <div class="world-stats">
          <div class="w-stat-box">
            <span id="world-season" class="w-stat-val">-</span>
            <span class="w-stat-lab">Season</span>
          </div>
          <div class="w-stat-box">
            <span id="world-temp" class="w-stat-val">-°C</span>
            <span class="w-stat-lab">Temperature</span>
          </div>
          <div class="w-stat-box">
            <span id="world-updated" class="w-stat-val">-</span>
            <span class="w-stat-lab">Last Sync</span>
          </div>
        </div>
      </div>
    </div>
  `;

  updateWorldDisplay();
  setInterval(updateWorldDisplay, 30000);
}

const WEATHER_ICONS = {
  sunny: '☀️',
  cloudy: '☁️',
  rainy: '🌧️',
  stormy: '⛈️',
  snowy: '❄️',
  clear: '🌙'
};

async function updateWorldDisplay() {
  const icon = document.getElementById('world-icon');
  const status = document.getElementById('world-status');
  const lighting = document.getElementById('world-lighting');
  const season = document.getElementById('world-season');
  const temp = document.getElementById('world-temp');
  const updated = document.getElementById('world-updated');

  if (!status) return;

  try {
    const resp = await fetch('/v1/plugins/world/state');
    const data = await resp.json();

    if (!data.weather) return;

    icon.textContent = WEATHER_ICONS[data.weather] || '🌤️';
    status.textContent = data.weather;
    lighting.textContent = data.lighting || 'Daylight';
    season.textContent = data.season;
    temp.textContent = (data.temperature || 0) + '°C';
    
    if (data.last_update) {
      const time = data.last_update.split('T')[1].split('.')[0];
      updated.textContent = time;
    }

  } catch (e) {
    console.error("World Update Error:", e);
  }
}

// Initialize
setTimeout(initWorldUI, 100);
