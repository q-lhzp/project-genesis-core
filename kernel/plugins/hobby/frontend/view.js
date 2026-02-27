/**
 * Hobby & Research Frontend - View Module (v1.0.0)
 */

async function initHobbyUI() {
  const root = document.getElementById('plugin-root-hobby-engine');
  if (!root) return;

  root.innerHTML = `
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:2rem;">
      <div class="panel-card">
        <h3>🎨 Interests & Hobbies</h3>
        <div id="interests-list" style="display:grid; gap:0.75rem; max-height:400px; overflow-y:auto;">
          Loading interests...
        </div>
        <button onclick="addNewInterest()" style="margin-top:1.5rem; width:100%; padding:0.5rem; background:var(--accent); color:#fff; border:none; border-radius:4px; cursor:pointer;">+ Add New Interest</button>
      </div>
      
      <div class="panel-card">
        <h3>🔬 Research Insights</h3>
        <div id="research-insights" style="display:grid; gap:1rem; max-height:400px; overflow-y:auto;">
          No recent research activity.
        </div>
        <button onclick="triggerResearch()" style="margin-top:1.5rem; width:100%; padding:0.5rem; background:#161625; color:#fff; border:1px solid #2a2a3a; border-radius:4px; cursor:pointer;">🚀 Manual Research Pulse</button>
      </div>
    </div>
  `;

  updateHobbyDisplay();
  setInterval(updateHobbyDisplay, 20000);
}

async function updateHobbyDisplay() {
  try {
    const resp = await fetch('/v1/plugins/hobby/interests');
    const data = await resp.json();
    
    if (data.status === 'success') {
      // 1. Render Interests/Hobbies
      const listEl = document.getElementById('interests-list');
      const allItems = [...data.interests, ...data.hobbies];
      listEl.innerHTML = allItems.map(i => `
        <div style="background:#0a0a12; padding:0.75rem; border-radius:6px; border:1px solid #2a2a3a; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong>${i.name}</strong>
            <div style="font-size:0.7rem; color:#666; text-transform:uppercase;">${i.category}</div>
          </div>
          <div style="color:var(--accent); font-weight:bold;">${i.intensity}/10</div>
        </div>
      `).join('') || 'No interests recorded yet.';

      // 2. Render Insights
      const insightEl = document.getElementById('research-insights');
      insightEl.innerHTML = (data.research_insights || []).reverse().slice(0, 10).map(insight => `
        <div style="background:#0a0a12; padding:0.75rem; border-radius:6px; border-left:3px solid #10b981;">
          <small style="color:#666;">${new Date(insight.timestamp).toLocaleTimeString()}</small>
          <div style="font-weight:bold; font-size:0.8rem; margin-top:0.25rem; text-transform:uppercase;">${insight.topic}</div>
          <div style="margin-top:0.25rem;">${insight.text}</div>
        </div>
      `).join('') || 'No research insights yet.';
    }
  } catch (e) { console.error("Hobby UI Error:", e); }
}

async function addNewInterest() {
  const name = prompt("Enter interest or hobby name:");
  if (!name) return;
  const type = confirm("Is it a Hobby? (Cancel for Interest)") ? 'hobby' : 'interest';
  
  try {
    await fetch('/v1/plugins/hobby/add', {
      method: 'POST',
      body: JSON.stringify({ name, type, category: 'General', intensity: 5 })
    });
    updateHobbyDisplay();
  } catch (e) {}
}

async function triggerResearch() {
  try {
    await fetch('/v1/plugins/hobby/add', { method: 'POST', body: JSON.stringify({ action: 'trigger_insight' }) }); // Placeholder for manual trigger
    updateHobbyDisplay();
  } catch (e) {}
}

setTimeout(initHobbyUI, 100);
window.addNewInterest = addNewInterest;
window.triggerResearch = triggerResearch;
