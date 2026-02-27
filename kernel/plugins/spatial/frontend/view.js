/**
 * Spatial & Items Frontend - View Module (v1.0.0)
 */

async function initSpatialUI() {
  const root = document.getElementById('plugin-root-spatial-engine');
  if (!root) return;

  root.innerHTML = `
    <div class="spatial-dashboard" style="display:grid; gap:2rem;">
      <div class="tabs-container" style="display:flex; gap:1rem; border-bottom:1px solid #2a2a3a; padding-bottom:0.5rem;">
        <button class="s-tab active" onclick="switchSpatialSubTab('interior')">🏠 Interior</button>
        <button class="s-tab" onclick="switchSpatialSubTab('inventory')">🎒 Inventory</button>
        <button class="s-tab" onclick="switchSpatialSubTab('wardrobe')">👔 Wardrobe</button>
      </div>
      
      <div id="spatial-sub-view" style="min-height:400px;">
        <!-- Sub-views will be rendered here -->
      </div>
    </div>
  `;

  switchSpatialSubTab('interior');
}

async function switchSpatialSubTab(tab) {
  // UI update for tabs
  document.querySelectorAll('.s-tab').forEach(btn => {
    btn.classList.remove('active');
    btn.style.color = '#888';
    btn.style.background = 'transparent';
    if (btn.innerText.toLowerCase().includes(tab)) {
      btn.classList.add('active');
      btn.style.color = 'var(--accent)';
      btn.style.background = '#161625';
    }
  });

  const container = document.getElementById('spatial-sub-view');
  container.innerHTML = `<div style="color:var(--accent); text-align:center; padding:2rem;">Loading ${tab}...</div>`;

  try {
    const resp = await fetch(`/v1/plugins/spatial/${tab}`);
    const data = await resp.json();
    
    if (tab === 'interior') renderInteriorSub(data, container);
    else if (tab === 'inventory') renderInventorySub(data, container);
    else if (tab === 'wardrobe') renderWardrobeSub(data, container);
  } catch (e) {
    container.innerHTML = `<div style="color:#ef4444;">Error loading ${tab}.</div>`;
  }
}

function renderInteriorSub(data, container) {
  container.innerHTML = `
    <div class="panel-card">
      <h3>Current Environment: ${data.current_room || 'N/A'}</h3>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1rem;">
        <div>
          <strong>Position:</strong> X:${data.entity_position.x} Y:${data.entity_position.y} Z:${data.entity_position.z}
        </div>
        <div>
          <strong>Rooms Discovered:</strong> ${data.rooms?.length || 0}
        </div>
      </div>
      <div style="margin-top:1.5rem;">
        <h4>Furniture in Room:</h4>
        <div id="furniture-list">${(data.rooms?.find(r => r.id === data.current_room)?.furniture || []).map(f => `<li>${f.name}</li>`).join('') || 'Empty room.'}</div>
      </div>
    </div>
  `;
}

function renderInventorySub(data, container) {
  container.innerHTML = `
    <div class="panel-card">
      <h3>Entity Inventory</h3>
      <div id="item-grid" style="display:grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap:1rem;">
        ${(data.items || []).map(item => `
          <div style="background:#0a0a12; padding:1rem; border-radius:8px; border:1px solid #2a2a3a; text-align:center;">
            <div style="font-size:1.5rem;">📦</div>
            <strong>${item.name}</strong>
            <div style="font-size:0.7rem; color:#666; margin-top:0.25rem;">${item.category}</div>
          </div>
        `).join('') || 'Inventory empty.'}
      </div>
    </div>
  `;
}

function renderWardrobeSub(data, container) {
  container.innerHTML = `
    <div class="panel-card">
      <h3>Wardrobe & Appearance</h3>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:2rem;">
        <div>
          <h4>Current Outfit: ${data.current_outfit || 'Custom'}</h4>
          <div id="worn-list" style="display:grid; gap:0.5rem;">
            ${Object.entries(data.worn_items || {}).map(([cat, item]) => `
              <div style="display:flex; justify-content:space-between; font-size:0.9rem;">
                <span style="color:#888;">${cat}:</span>
                <strong>${item.name}</strong>
              </div>
            `).join('')}
          </div>
        </div>
        <div>
          <h4>Saved Outfits</h4>
          <div id="outfit-list">${Object.keys(data.outfits || {}).map(o => `<li>${o}</li>`).join('') || 'None.'}</div>
        </div>
      </div>
    </div>
  `;
}

setTimeout(initSpatialUI, 100);
window.switchSpatialSubTab = switchSpatialSubTab;
