/**
 * Identity Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initIdentityUI() {
  const root = document.getElementById('plugin-root-identity');
  if (!root) return;

  root.innerHTML = `
    <style>
      .id-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        padding: 1rem;
        font-family: 'DM Sans', sans-serif;
      }
      
      @media (max-width: 1000px) {
        .id-container { grid-template-columns: 1fr; }
      }

      .id-card {
        background: #12121a;
        border: 1px solid #1e1e30;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
      }

      .id-card h2 {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #6a6a80;
        margin-bottom: 1.2rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid #1e1e30;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      /* Soul Tree (Legacy Style) */
      .soul-section { margin-bottom: 1rem; }
      .soul-section-title { color: #f0a050; font-size: 0.9rem; font-weight: bold; margin-bottom: 0.5rem; }
      .soul-subsection { margin-left: 1rem; margin-bottom: 0.5rem; }
      .soul-subsection-title { color: #7c6ff0; font-size: 0.8rem; margin-bottom: 0.3rem; }
      .soul-bullet {
        margin-left: 1.5rem;
        font-size: 0.8rem;
        color: #c8c8d8;
        line-height: 1.4;
        margin-bottom: 0.2rem;
        position: relative;
      }
      .soul-bullet::before { content: '•'; position: absolute; left: -1rem; color: #5a5a70; }
      .tag-core { color: #e05050; font-size: 0.6rem; font-weight: bold; margin-left: 0.4rem; vertical-align: middle; }
      .tag-mutable { color: #50c878; font-size: 0.6rem; font-weight: bold; margin-left: 0.4rem; vertical-align: middle; }

      /* Proposals */
      .prop-item {
        background: #0a0a0f;
        border: 1px solid #1e1e30;
        padding: 0.8rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
        border-left: 3px solid #7c6ff0;
      }
      .prop-id { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #6a6a80; }
      .prop-text { font-size: 0.8rem; margin-top: 0.4rem; line-height: 1.4; }

      /* Buttons */
      .btn-run {
        background: #7c6ff0;
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.75rem;
        font-weight: bold;
        transition: all 0.2s;
      }
      .btn-run:hover { background: #6a5ae0; transform: translateY(-1px); }
    </style>
    
    <div class="id-container">
      <!-- Soul Map Column -->
      <div>
        <div class="id-card">
          <h2>Soul Map <span>SOUL.md</span></h2>
          <div id="soul-tree-display">
            <!-- Rendered by JS -->
          </div>
        </div>
      </div>

      <!-- Evolution Column -->
      <div>
        <div class="id-card" style="border-left: 4px solid #50c878;">
          <h2>Pipeline Control <button class="btn-run" onclick="runPipeline()">🚀 Run Evolution</button></h2>
          <div id="pipeline-status" style="font-size: 0.8rem; color: #6a6a80; font-style: italic;">
            Ready for next evolution cycle.
          </div>
        </div>

        <div class="id-card">
          <h2>Pending Proposals <span id="prop-count" style="color: #7c6ff0;">0</span></h2>
          <div id="proposals-display">
            <!-- Rendered by JS -->
          </div>
        </div>
      </div>
    </div>
  `;

  // Start Update Loop
  updateIdentityDisplay();
  setInterval(updateIdentityDisplay, 15000);
}

async function updateIdentityDisplay() {
  const treeDisplay = document.getElementById('soul-tree-display');
  const propDisplay = document.getElementById('proposals-display');
  const propCount = document.getElementById('prop-count');

  if (!treeDisplay) return;

  try {
    // 1. Fetch Soul
    const sResp = await fetch('/v1/plugins/identity/soul');
    const sData = await sResp.json();
    
    if (sData.tree) {
      treeDisplay.innerHTML = sData.tree.map(section => `
        <div class="soul-section">
          <div class="soul-section-title">${section.text}</div>
          ${section.children.map(child => {
            if (child.type === 'subsection') {
              return `
                <div class="soul-subsection">
                  <div class="soul-subsection-title">${child.text}</div>
                  ${child.children.map(b => `
                    <div class="soul-bullet">${b.text} <span class="tag-${b.tag.toLowerCase()}">[${b.tag}]</span></div>
                  `).join('')}
                </div>
              `;
            } else {
              return `<div class="soul-bullet">${child.text} <span class="tag-${child.tag.toLowerCase()}">[${child.tag}]</span></div>`;
            }
          }).join('')}
        </div>
      `).join('');
    }

    // 2. Fetch Proposals
    const pResp = await fetch('/v1/plugins/identity/proposals');
    const pData = await pResp.json();
    
    if (pData.pending) {
      propCount.textContent = pData.pending.length;
      if (pData.pending.length > 0) {
        propDisplay.innerHTML = pData.pending.map(p => `
          <div class="prop-item">
            <div class="prop-id">${p.id} • ${p.change_type.toUpperCase()}</div>
            <div class="prop-text">${p.proposed_content || p.summary}</div>
          </div>
        `).join('');
      } else {
        propDisplay.innerHTML = '<div style="color:#6a6a80; font-size:0.75rem; font-style:italic;">No pending evolution proposals.</div>';
      }
    }

  } catch (e) {
    console.error("Identity Update Error:", e);
  }
}

async function runPipeline() {
  const status = document.getElementById('pipeline-status');
  status.textContent = "Pipeline running... INGESTING experiences...";
  
  try {
    const resp = await fetch('/v1/plugins/identity/pipeline/run', { method: 'POST' });
    const data = await resp.json();
    if (data.success) {
      status.textContent = "Pipeline triggered successfully. See logs for details.";
      setTimeout(updateIdentityDisplay, 2000);
    }
  } catch (e) {
    status.textContent = "Error: " + e.message;
  }
}

// Initialize
setTimeout(initIdentityUI, 100);
window.runPipeline = runPipeline;
