/**
 * Inspector Plugin - UI Component
 * Provides visualization of agent prompts and injected data.
 */

async function initInspectorUI() {
    const root = document.getElementById('plugin-root-inspector');
    if (!root) return;

    root.innerHTML = `
    <div class="inspector-container">
      <div class="inspector-header">
        <div>
          <h2 class="inspector-title">Agent Prompt Surveillance</h2>
          <p class="inspector-meta">Real-time analysis of LLM interactions and somatic injections</p>
        </div>
        <button class="primary" onclick="refreshInspector()">Refresh Prompts</button>
      </div>
      
      <div id="inspector-results" class="inspector-results">
        <div class="loading-state">
          <span class="pulse">Initializing Neural Link...</span>
        </div>
      </div>
    </div>
  `;

    // Inject styles
    if (!document.getElementById('inspector-styles')) {
        const style = document.createElement('style');
        style.id = 'inspector-styles';
        style.textContent = `
            .inspector-container {
                display: flex;
                flex-direction: column;
                gap: 1.5rem;
                height: 100%;
                overflow: hidden;
            }
            .inspector-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                padding-bottom: 1rem;
                border-bottom: 1px solid var(--border);
            }
            .inspector-title {
                font-family: 'Inter', sans-serif;
                font-size: 1.1rem;
                font-weight: 600;
                margin: 0;
                letter-spacing: -0.02em;
            }
            .inspector-meta {
                font-size: 0.7rem;
                color: var(--text-dim);
                margin: 0.2rem 0 0 0;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .inspector-results {
                flex: 1;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 1rem;
                padding-right: 0.5rem;
            }
            /* Scrollbar */
            .inspector-results::-webkit-scrollbar { width: 4px; }
            .inspector-results::-webkit-scrollbar-track { background: transparent; }
            .inspector-results::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

            .prompt-card {
                background: rgba(255,255,255,0.03);
                border: 1px solid var(--border);
                border-radius: 12px;
                overflow: hidden;
                transition: all 0.3s ease;
            }
            .prompt-card:hover {
                border-color: var(--accent);
                background: rgba(255,255,255,0.05);
            }
            .prompt-card-header {
                padding: 1rem;
                background: rgba(255,255,255,0.02);
                border-bottom: 1px solid var(--border);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .agent-info {
                display: flex;
                align-items: center;
                gap: 0.8rem;
            }
            .agent-badge {
                padding: 0.2rem 0.6rem;
                background: var(--accent);
                color: #000;
                border-radius: 4px;
                font-size: 0.65rem;
                font-weight: 800;
                font-family: 'JetBrains Mono', monospace;
            }
            .timestamp {
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.65rem;
                color: var(--text-dim);
            }
            .injected-data-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                gap: 0.5rem;
                padding: 1rem;
                background: rgba(0,0,0,0.2);
            }
            .injected-tag {
                font-size: 0.65rem;
                font-family: 'JetBrains Mono', monospace;
                padding: 0.3rem 0.5rem;
                background: rgba(255,255,255,0.05);
                border: 1px solid var(--border);
                border-radius: 4px;
                display: flex;
                justify-content: space-between;
            }
            .injected-label { color: var(--text-dim); }
            .injected-value { color: var(--accent); font-weight: 600; }
            
            .prompt-content {
                padding: 1.2rem;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8rem;
                line-height: 1.6;
                white-space: pre-wrap;
                color: #ccc;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .loading-state {
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 4rem;
                color: var(--accent);
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8rem;
            }
            .pulse { animation: diag-pulse 1.5s infinite; }
            @keyframes diag-pulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }
            
            .empty-state {
                text-align: center;
                padding: 4rem;
                border: 1px dashed var(--border);
                border-radius: 12px;
                color: var(--text-dim);
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8rem;
            }
        `;
        document.head.appendChild(style);
    }

    await refreshInspector();
}

async function refreshInspector() {
    const results = document.getElementById('inspector-results');
    if (!results) return;

    try {
        const resp = await fetch('/v1/plugins/inspector/prompts');
        const data = await resp.json();

        if (Object.keys(data).length === 0) {
            results.innerHTML = `
                <div class="empty-state">
                    <p>No prompts captured in this session.</p>
                    <p style="font-size: 0.6rem; margin-top: 0.5rem;">Interactions with LLM agents will be logged here.</p>
                </div>
            `;
            return;
        }

        results.innerHTML = Object.entries(data).map(([agentId, entry]) => `
            <div class="prompt-card">
              <div class="prompt-card-header">
                <div class="agent-info">
                  <span class="agent-badge">${agentId.toUpperCase()}</span>
                  <span class="timestamp">${new Date(entry.timestamp).toLocaleString()}</span>
                </div>
                <div style="font-size: 0.6rem; color: var(--accent);">STREAMS: ACTIVE</div>
              </div>
              
              <div class="injected-data-grid">
                ${Object.entries(entry.injected_data).map(([key, val]) => `
                  <div class="injected-tag">
                    <span class="injected-label">${key}:</span>
                    <span class="injected-value">${typeof val === 'number' ? val + '%' : val}</span>
                  </div>
                `).join('')}
              </div>
              
              <div class="prompt-content">${escapeHtml(entry.prompt)}</div>
            </div>
        `).join('');

    } catch (e) {
        results.innerHTML = `<div class="status-fail">ERROR: Failed to fetch prompt history (${e.message})</div>`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Global Export
window.refreshInspector = refreshInspector;

// Initialize
setTimeout(initInspectorUI, 100);
