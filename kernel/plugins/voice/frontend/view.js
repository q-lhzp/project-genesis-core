/**
 * Voice Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initVoiceUI() {
  const root = document.getElementById('plugin-root-voice');
  if (!root) return;

  root.innerHTML = `
    <style>
      .voice-container { max-width: 800px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .voice-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; border-left: 4px solid #7c6ff0; }
      .voice-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1.2rem; }
      
      .voice-form { display: flex; flex-direction: column; gap: 1rem; }
      .voice-input { width: 100%; background: #0a0a0f; color: #c8c8d8; border: 1px solid #1e1e30; border-radius: 8px; padding: 0.8rem; font-size: 0.9rem; }
      .voice-row { display: grid; grid-template-columns: 1fr auto; gap: 1rem; align-items: center; }
      
      .btn-speak { background: #7c6ff0; color: white; border: none; padding: 0.8rem 2rem; border-radius: 8px; cursor: pointer; font-weight: bold; transition: all 0.2s; }
      .btn-speak:hover { background: #6a5ae0; box-shadow: 0 5px 15px rgba(124, 111, 240, 0.3); }
      
      .audio-history { margin-top: 1.5rem; display: flex; flex-direction: column; gap: 0.8rem; }
      .audio-item { background: #0a0a0f; padding: 0.8rem; border-radius: 8px; border: 1px solid #1e1e30; display: flex; align-items: center; justify-content: space-between; }
      .audio-text { font-size: 0.8rem; color: #eeeef4; font-style: italic; }
    </style>

    <div class="voice-container">
      <div class="voice-card">
        <h2>Neural Voice Interface</h2>
        <div class="voice-form">
          <textarea id="voice-text" class="voice-input" placeholder="Enter text for neural synthesis..." rows="2"></textarea>
          <div class="voice-row">
            <select id="voice-select" class="voice-input">
              <option value="nova">Nova (Warm/British)</option>
              <option value="shimmer">Shimmer (Soft/Clear)</option>
              <option value="alloy">Alloy (Neutral/Direct)</option>
            </select>
            <button class="btn-speak" onclick="generateNeuralSpeech()">Speak</button>
          </div>
          <div id="voice-status" style="font-size: 0.7rem; color: #7c6ff0;"></div>
        </div>

        <div id="voice-history" class="audio-history">
          <!-- Audio history items -->
        </div>
      </div>
    </div>
  `;
}

async function generateNeuralSpeech() {
  const text = document.getElementById('voice-text').value;
  const voice = document.getElementById('voice-select').value;
  const status = document.getElementById('voice-status');

  if (!text) return;

  status.textContent = "Synthesizing neural waveforms...";

  try {
    const resp = await fetch('/v1/plugins/voice/generate', {
      method: 'POST',
      body: JSON.stringify({ text, voice })
    });
    const result = await resp.json();
    
    if (result.success) {
      status.textContent = "Synthesis complete.";
      document.getElementById('voice-text').value = "";
      
      // Play Audio
      const audio = new Audio(result.audio.url);
      audio.play();
      
      // Add to history
      const history = document.getElementById('voice-history');
      const item = document.createElement('div');
      item.className = 'audio-item';
      item.innerHTML = `
        <span class="audio-text">"${text.slice(0, 40)}..."</span>
        <button onclick="new Audio('${result.audio.url}').play()" style="background:none; border:none; color:#7c6ff0; cursor:pointer;">▶</button>
      `;
      history.prepend(item);
    }
  } catch (e) {
    status.textContent = "Error: " + e.message;
  }
}

// Initialize
setTimeout(initVoiceUI, 100);
window.generateNeuralSpeech = generateNeuralSpeech;
