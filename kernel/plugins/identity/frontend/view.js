/**
 * Identity & Evolution Frontend - View Module (v1.0.0)
 */

async function initIdentityUI() {
  const root = document.getElementById('plugin-root-identity-engine');
  if (!root) return;

  root.innerHTML = `
    <div style="display:grid; grid-template-columns: 1.5fr 1fr; gap:2rem;">
      <div class="panel-card">
        <h3>📄 SOUL.md (Mutable Identity)</h3>
        <div id="soul-content" style="background:#0a0a12; padding:1.5rem; border-radius:8px; border:1px solid #2a2a3a; height:600px; overflow-y:auto; font-family:'Courier New', monospace; white-space:pre-wrap; font-size:0.9rem;">
          Loading Q's identity...
        </div>
      </div>
      
      <div style="display:grid; gap:1.5rem; align-content:start;">
        <div class="panel-card">
          <h3>🧬 Evolution Pipeline</h3>
          <div id="pipeline-status" style="margin-bottom:1rem; font-size:0.85rem; color:#888;">
            Ready for next reflection cycle.
          </div>
          <button onclick="runEvolutionPipeline()" style="width:100%; padding:0.75rem; background:#7c6ff0; color:#fff; border:none; border-radius:4px; cursor:pointer; font-weight:bold;">🚀 Run Manual Pipeline</button>
        </div>

        <div class="panel-card">
          <h3>📜 Pending Proposals</h3>
          <div id="pending-proposals" style="display:grid; gap:0.75rem; font-size:0.85rem;">
            No pending changes.
          </div>
        </div>
      </div>
    </div>
  `;

  updateIdentityDisplay();
}

async function updateIdentityDisplay() {
  try {
    // 1. Load Soul
    const soulResp = await fetch('/v1/plugins/identity/soul');
    const soulData = await soulResp.json();
    const soulEl = document.getElementById('soul-content');
    if (soulData.exists) {
      soulEl.textContent = soulData.content;
    } else {
      soulEl.innerHTML = '<div style="color:#ef4444;">SOUL.md not found. Use Genesis Lab to bootstrap.</div>';
    }

    // 2. Load Proposals
    const propResp = await fetch('/v1/plugins/identity/proposals');
    const propData = await propResp.json();
    const propEl = document.getElementById('pending-proposals');
    propEl.innerHTML = (propData.pending || []).map(p => `
      <div style="background:#0a0a12; padding:0.75rem; border-radius:6px; border-left:3px solid #f0a050;">
        <strong>${p.change_type.toUpperCase()}:</strong> ${p.proposed_content.slice(0, 50)}...
      </div>
    `).join('') || 'No pending changes.';

  } catch (e) { console.error("Identity UI Error:", e); }
}

async function runEvolutionPipeline() {
  const statusEl = document.getElementById('pipeline-status');
  statusEl.textContent = "Pipeline executing... INGESTING... REFLECTING...";
  statusEl.style.color = "var(--accent)";

  try {
    const resp = await fetch('/v1/plugins/identity/pipeline/run', { method: 'POST' });
    const result = await resp.json();
    
    if (result.steps_completed) {
      statusEl.textContent = `Success: ${result.proposals_applied} changes applied.`;
      statusEl.style.color = "#10b981";
      updateIdentityDisplay();
    } else {
      statusEl.textContent = `Skipped: ${result.reason}`;
      statusEl.style.color = "#f0a050";
    }
  } catch (e) { 
    statusEl.textContent = "Pipeline Error: " + e.message;
    statusEl.style.color = "#ef4444";
  }
}

setTimeout(initIdentityUI, 100);
window.runEvolutionPipeline = runEvolutionPipeline;
