/**
 * Bios Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initBiosUI() {
  const root = document.getElementById('plugin-root-bios');
  if (!root) return;

  root.innerHTML = `
    <style>
      .bios-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        padding: 1rem;
        font-family: 'DM Sans', sans-serif;
      }
      
      @media (max-width: 800px) {
        .bios-container { grid-template-columns: 1fr; }
      }

      .bios-card {
        background: #12121a;
        border: 1px solid #1e1e30;
        border-radius: 12px;
        padding: 1.5rem;
        position: relative;
      }

      .bios-card h2 {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #6a6a80;
        margin-bottom: 1.2rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid #1e1e30;
      }

      /* Vital Rows (Legacy Style) */
      .vital-row {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.8rem;
      }
      .vital-label {
        width: 80px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        text-transform: uppercase;
        color: #6a6a80;
        text-align: right;
      }
      .vital-bar-bg {
        flex: 1;
        height: 6px;
        background: #1a1a28;
        border-radius: 3px;
        overflow: hidden;
      }
      .vital-bar {
        height: 100%;
        border-radius: 3px;
        transition: width 1s cubic-bezier(0.1, 0.7, 0.1, 1);
      }
      .vital-value {
        width: 30px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #eeeef4;
        text-align: right;
      }

      /* Action Buttons */
      .action-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 0.6rem;
        margin-top: 1.5rem;
      }
      .action-btn {
        background: #1a1a28;
        border: 1px solid #1e1e30;
        color: #c8c8d8;
        padding: 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
      }
      .action-btn:hover {
        background: #7c6ff0;
        color: white;
        border-color: #7c6ff0;
      }

      /* Sensations */
      .sensation-list {
        margin-top: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }
      .sensation-item {
        font-size: 0.8rem;
        color: #f0a050;
        font-style: italic;
        padding-left: 0.8rem;
        border-left: 2px solid #f0a050;
      }

      /* Cycle Info */
      .cycle-info {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-top: 1rem;
      }
      .cycle-stat {
        text-align: center;
        background: #0a0a0f;
        padding: 0.8rem;
        border-radius: 8px;
        border: 1px solid #1e1e30;
      }
      .cycle-val {
        display: block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.2rem;
        font-weight: 700;
        color: #7c6ff0;
      }
      .cycle-lab {
        font-size: 0.6rem;
        text-transform: uppercase;
        color: #6a6a80;
        letter-spacing: 0.1em;
      }
    </style>
    
    <div class="bios-container">
      <!-- Vitals Card -->
      <div class="bios-card">
        <h2>Physical Integrity</h2>
        <div id="vitals-grid">
          <!-- Rendered by JS -->
        </div>
        <div class="action-grid">
          <button class="action-btn" onclick="triggerBiosAction('eat')">🍕 Eat</button>
          <button class="action-btn" onclick="triggerBiosAction('drink')">💧 Drink</button>
          <button class="action-btn" onclick="triggerBiosAction('sleep')">😴 Sleep</button>
          <button class="action-btn" onclick="triggerBiosAction('toilet')">🚽 Toilet</button>
          <button class="action-btn" onclick="triggerBiosAction('shower')">🚿 Shower</button>
          <button class="action-btn" onclick="triggerBiosAction('rest')">🛋️ Rest</button>
          <button class="action-btn" onclick="triggerBiosAction('pleasure')">💖 Pleasure</button>
        </div>
      </div>

      <!-- Cognitive & Sensory Card -->
      <div class="bios-card">
        <h2>Sensory Perception</h2>
        <div id="sensation-list" class="sensation-list">
          <!-- Rendered by JS -->
        </div>
        
        <h2 style="margin-top: 2rem;">Hormonal Cycle</h2>
        <div id="cycle-display" class="cycle-info">
          <!-- Rendered by JS -->
        </div>
      </div>
    </div>
  `;

  // Start Update Loop
  updateBiosDisplay();
  setInterval(updateBiosDisplay, 5000);
}

function vitalColor(value, key) {
  if (key === 'energy') {
    if (value < 10) return '#e05050';
    if (value < 30) return '#f0a050';
    if (value < 60) return '#e0d050';
    return '#50c878';
  }
  if (value > 90) return '#e05050';
  if (value > 75) return '#f0a050';
  if (value > 40) return '#e0d050';
  return '#50c878';
}

async function updateBiosDisplay() {
  const grid = document.getElementById('vitals-grid');
  const sensations = document.getElementById('sensation-list');
  const cycle = document.getElementById('cycle-display');
  if (!grid) return;

  try {
    const resp = await fetch('/v1/plugins/bios/needs');
    const data = await resp.json();
    
    if (!data.needs) return;

    // 1. Render Vitals
    const needKeys = ['energy', 'hunger', 'thirst', 'bladder', 'bowel', 'hygiene', 'stress', 'arousal', 'libido'];
    grid.innerHTML = needKeys.map(k => {
      const v = data.needs[k] ?? 0;
      const color = vitalColor(v, k);
      return `
        <div class="vital-row">
          <span class="vital-label">${k}</span>
          <div class="vital-bar-bg">
            <div class="vital-bar" style="width:${v}%;background:${color};box-shadow: 0 0 8px ${color}44"></div>
          </div>
          <span class="vital-value">${Math.round(v)}</span>
        </div>
      `;
    }).join('');

    // 2. Render Sensations
    if (data.sensations && data.sensations.length > 0) {
      sensations.innerHTML = data.sensations.map(s => `
        <div class="sensation-item">${s}</div>
      `).join('');
    } else {
      sensations.innerHTML = '<div style="color:#6a6a80; font-size:0.75rem; font-style:italic;">No significant physical sensations.</div>';
    }

    // 3. Render Cycle
    if (data.cycle) {
      cycle.innerHTML = `
        <div class="cycle-stat">
          <span class="cycle-val">Day ${data.cycle.day}</span>
          <span class="cycle-lab">Cycle Progress</span>
        </div>
        <div class="cycle-stat">
          <span class="cycle-val" style="font-size: 0.9rem; text-transform: capitalize;">${data.cycle.phase}</span>
          <span class="cycle-lab">Current Phase</span>
        </div>
      `;
    }

    // 4. Reflex Lock Warning
    if (data.reflex_lock) {
      grid.style.borderColor = '#e05050';
      grid.style.boxShadow = '0 0 15px rgba(224, 80, 80, 0.2)';
    } else {
      grid.style.borderColor = 'transparent';
      grid.style.boxShadow = 'none';
    }

  } catch (e) {
    console.error("Update Error:", e);
  }
}

async function triggerBiosAction(action) {
  try {
    await fetch('/v1/plugins/bios/action', {
      method: 'POST',
      body: JSON.stringify({ action, intensity: 1.0 })
    });
    // Optimistic update
    setTimeout(updateBiosDisplay, 500);
  } catch (e) {
    console.error("Action Error:", e);
  }
}

// Initialize
setTimeout(initBiosUI, 100);
window.triggerBiosAction = triggerBiosAction;
