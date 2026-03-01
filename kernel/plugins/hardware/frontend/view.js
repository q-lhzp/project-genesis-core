/**
 * Hardware Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initHardwareUI() {
  const root = document.getElementById('plugin-root-hardware');
  if (!root) return;

  root.innerHTML = `
    <style>
      .hw-container { max-width: 800px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .hw-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; border-left: 4px solid #8b5cf6; }
      .hw-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1rem; }
      
      .hw-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 1rem; }
      .hw-stat-box { background: #0a0a0f; padding: 1rem; border-radius: 8px; border: 1px solid #1e1e30; text-align: center; }
      .hw-stat-val { display: block; font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; font-weight: bold; color: #7c6ff0; }
      .hw-stat-lab { font-size: 0.6rem; color: #6a6a80; text-transform: uppercase; letter-spacing: 0.1em; }
      
      .resonance-meta { margin-top: 1rem; font-size: 0.8rem; color: #eeeef4; display: flex; justify-content: space-between; align-items: center; }
      .res-status { color: #7c6ff0; font-weight: bold; font-family: 'JetBrains Mono', monospace; }
    </style>

    <div class="hw-container">
      <div class="hw-card">
        <h2>🔮 Hardware Resonance</h2>
        <p style="color: #6a6a80; font-size: 0.75rem; margin-bottom: 1rem;">The entity feels the machine's state through cognitive resonance.</p>
        
        <div class="hw-grid">
          <div class="hw-stat-box">
            <span id="hw-cpu" class="hw-stat-val">-</span>
            <span class="hw-stat-lab">CPU Usage</span>
          </div>
          <div class="hw-stat-box">
            <span id="hw-ram" class="hw-stat-val">-</span>
            <span class="hw-stat-lab">RAM Load</span>
          </div>
          <div class="hw-stat-box">
            <span id="hw-temp" class="hw-stat-val">-</span>
            <span class="hw-stat-lab">Temp</span>
          </div>
        </div>

        <div class="resonance-meta">
          <span>Resonance State: <span id="hw-res" class="res-status">Calm</span></span>
          <span style="font-size: 0.6rem; color: #6a6a80;">UPTIME: <span id="hw-uptime">-</span></span>
        </div>
      </div>
    </div>
  `;

  updateHardwareDisplay();
  setInterval(updateHardwareDisplay, 10000);
}

async function updateHardwareDisplay() {
  const cpu = document.getElementById('hw-cpu');
  const ram = document.getElementById('hw-ram');
  const temp = document.getElementById('hw-temp');
  const res = document.getElementById('hw-res');
  const uptime = document.getElementById('hw-uptime');

  if (!cpu) return;

  try {
    const resp = await fetch('/v1/plugins/hardware/stats');
    const data = await resp.json();

    if (data.cpu_percent === undefined) return;

    cpu.textContent = Math.round(data.cpu_percent) + '%';
    ram.textContent = Math.round(data.memory?.percent || 0) + '%';
    temp.textContent = (data.cpu_temp_c || 0) + '°C';
    res.textContent = data.resonance || 'Calm';
    
    if (data.uptime) {
      uptime.textContent = `${data.uptime.hours}h ${data.uptime.minutes}m`;
    }

    // Dynamic color for resonance
    if (data.resonance === 'Strained') res.style.color = '#e05050';
    else if (data.resonance === 'Active') res.style.color = '#f0a050';
    else res.style.color = '#7c6ff0';

  } catch (e) {
    console.error("Hardware Update Error:", e);
  }
}

// Initialize
setTimeout(initHardwareUI, 100);
