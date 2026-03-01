/**
 * Spatial Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initSpatialUI() {
  const root = document.getElementById('plugin-root-spatial');
  if (!root) return;

  root.innerHTML = `
    <style>
      .sp-container { max-width: 1200px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .sp-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
      .sp-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1.2rem; }
      
      .room-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }
      .room-item { background: #0a0a0f; border: 1px solid #1e1e30; padding: 1rem; border-radius: 10px; border-top: 3px solid #7c6ff0; }
      .room-name { font-weight: bold; color: #eeeef4; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
      .item-list { font-size: 0.75rem; color: #6a6a80; list-style: none; padding: 0; }
      .item-list li { margin-bottom: 0.2rem; }
      
      .wardrobe-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
      .outfit-item { background: #0a0a0f; border: 1px solid #1e1e30; padding: 1rem; border-radius: 10px; cursor: pointer; transition: all 0.2s; }
      .outfit-item:hover { border-color: #7c6ff0; transform: translateY(-2px); }
      .outfit-active { border-color: #50c878; border-width: 2px; }
    </style>

    <div class="sp-container">
      <div class="sp-card">
        <h2>Neural Interior / Rooms</h2>
        <div id="room-display" class="room-grid">
          <p style="color: #6a6a80; font-size: 0.8rem;">Loading interior mapping...</p>
        </div>
      </div>

      <div class="wardrobe-grid">
        <div class="sp-card">
          <h2>Wardrobe / Outfits</h2>
          <div id="wardrobe-display">
            <!-- Outfits -->
          </div>
        </div>
        <div class="sp-card">
          <h2>Inventory / Items</h2>
          <div id="inventory-display" style="font-size: 0.8rem; color: #6a6a80; font-style: italic;">
            No items in local storage.
          </div>
        </div>
      </div>
    </div>
  `;

  updateSpatialDisplay();
}

async function updateSpatialDisplay() {
  const rDisplay = document.getElementById('room-display');
  const wDisplay = document.getElementById('wardrobe-display');

  if (!rDisplay) return;

  try {
    // 1. Rooms
    const rResp = await fetch('/v1/plugins/spatial/interior');
    const rData = await rResp.json();
    if (rData.rooms) {
      rDisplay.innerHTML = rData.rooms.map(r => `
        <div class="room-item">
          <div class="room-name">📍 ${r.name}</div>
          <ul class="item-list">
            ${r.items.map(i => `<li>• ${i}</li>`).join('')}
          </ul>
        </div>
      `).join('');
    }

    // 2. Wardrobe
    const wResp = await fetch('/v1/plugins/spatial/wardrobe');
    const wData = await wResp.json();
    if (wData.outfits) {
      wDisplay.innerHTML = wData.outfits.map(o => `
        <div class="outfit-item ${wData.current_outfit === o.id ? 'outfit-active' : ''}" onclick="setOutfit('${o.id}')">
          <div style="font-weight:bold; color:#eeeef4;">${o.name}</div>
          <div style="font-size:0.7rem; color:#6a6a80; margin-top:0.3rem;">${o.parts.join(', ')}</div>
        </div>
      `).join('');
    }

  } catch (e) {
    console.error("Spatial Update Error:", e);
  }
}

async function setOutfit(id) {
  try {
    const resp = await fetch('/v1/plugins/spatial/wardrobe');
    const data = await resp.json();
    data.current_outfit = id;
    await fetch('/v1/plugins/spatial/update', {
      method: 'POST',
      body: JSON.stringify({ component: 'wardrobe', value: data })
    });
    updateSpatialDisplay();
  } catch (e) {}
}

// Initialize
setTimeout(initSpatialUI, 100);
window.setOutfit = setOutfit;
