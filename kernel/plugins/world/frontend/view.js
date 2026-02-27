/**
 * World Engine Frontend - View Module (v1.0.0)
 */

async function initWorldUI() {
  const root = document.getElementById('plugin-root-world-engine');
  if (!root) return;

  root.innerHTML = `
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:2rem;">
      <div class="panel-card">
        <h3>☁️ Current Weather</h3>
        <div id="world-weather" style="display:grid; gap:1rem;">
          Loading weather...
        </div>
      </div>
      
      <div class="panel-card">
        <h3>☀️ Lighting & Sun</h3>
        <div id="world-lighting" style="display:grid; gap:1rem;">
          Loading lighting...
        </div>
      </div>

      <div class="panel-card" style="grid-column: span 2;">
        <h3>🌍 Atmosphere & Season</h3>
        <div id="world-atmosphere" style="display:flex; justify-content:space-around; align-items:center; padding:1rem;">
          Loading atmosphere...
        </div>
      </div>
    </div>
  `;

  updateWorldDisplay();
  setInterval(updateWorldDisplay, 30000);
}

async function updateWorldDisplay() {
  try {
    const resp = await fetch('/v1/plugins/world/state');
    const data = await resp.json();
    
    if (data.success) {
      const w = data.world.weather;
      const l = data.world.lighting;
      const a = data.world.atmosphere;

      // 1. Weather
      const weatherEl = document.getElementById('world-weather');
      weatherEl.innerHTML = `
        <div style="font-size:2.5rem; text-align:center;">${getWeatherEmoji(w.condition)}</div>
        <div style="text-align:center; font-size:1.2rem; font-weight:bold; text-transform:capitalize;">${w.condition.replace('_', ' ')}</div>
        <div style="display:flex; justify-content:space-around; margin-top:1rem;">
          <div>Temp: <strong>${w.temperature}°C</strong></div>
          <div>Feels: <strong>${w.feels_like}°C</strong></div>
        </div>
        <div style="font-size:0.8rem; color:#888; margin-top:0.5rem;">Wind: ${w.wind_speed} km/h | Humidity: ${w.humidity}%</div>
      `;

      // 2. Lighting
      const lightingEl = document.getElementById('world-lighting');
      lightingEl.innerHTML = `
        <div style="display:flex; justify-content:space-between;">
          <span>Sunrise: 🌅 ${l.sunrise}</span>
          <span>Sunset: 🌇 ${l.sunset}</span>
        </div>
        <div style="margin-top:1.5rem; text-align:center;">
          <div style="font-size:1.5rem;">${l.moon_phase.replace('_', ' ')}</div>
          <div style="font-size:0.8rem; color:#888;">Moon Illumination: ${l.moon_illumination}%</div>
        </div>
        <div style="margin-top:1rem; padding:0.5rem; background:${l.is_daytime ? '#7c6ff033' : '#161625'}; border-radius:4px; text-align:center;">
          ${l.is_daytime ? '☀️ DAYTIME' : '🌙 NIGHTTIME'}
        </div>
      `;

      // 3. Atmosphere
      const atmosphereEl = document.getElementById('world-atmosphere');
      atmosphereEl.innerHTML = `
        <div style="text-align:center;">
          <div style="font-size:0.7rem; color:#888;">SEASON</div>
          <strong>${data.world.season.toUpperCase()}</strong>
        </div>
        <div style="text-align:center;">
          <div style="font-size:0.7rem; color:#888;">CLOUDS</div>
          <strong>${a.cloud_cover}%</strong>
        </div>
        <div style="text-align:center;">
          <div style="font-size:0.7rem; color:#888;">RAIN CHANCE</div>
          <strong>${a.precipitation_chance}%</strong>
        </div>
        <div style="text-align:center;">
          <div style="font-size:0.7rem; color:#888;">AIR QUALITY</div>
          <strong style="color:${a.air_quality_index < 50 ? '#10b981' : '#f0a050'}">${a.air_quality_index}</strong>
        </div>
      `;
    }
  } catch (e) { console.error("World UI Error:", e); }
}

function getWeatherEmoji(condition) {
  const map = {
    'clear': '☀️',
    'partly_cloudy': '⛅',
    'cloudy': '☁️',
    'overcast': '🌥️',
    'rain': '🌧️',
    'light_rain': '🌦️',
    'heavy_rain': '⛈️',
    'snow': '❄️',
    'fog': '🌫️',
    'storm': '⚡'
  };
  return map[condition] || '🌍';
}

setTimeout(initWorldUI, 100);
