/**
 * ImageGen Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initImageGenUI() {
  const root = document.getElementById('plugin-root-image_gen');
  if (!root) return;

  root.innerHTML = `
    <style>
      .img-container { max-width: 1200px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .img-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
      .img-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1rem; }
      
      /* Generate Form */
      .gen-form { display: flex; flex-direction: column; gap: 1rem; }
      .gen-input { width: 100%; background: #0a0a0f; color: #c8c8d8; border: 1px solid #1e1e30; border-radius: 8px; padding: 0.8rem; font-size: 0.9rem; }
      .gen-row { display: grid; grid-template-columns: 1fr 1fr auto; gap: 1rem; align-items: center; }
      
      .btn-gen { background: #7c6ff0; color: white; border: none; padding: 0.8rem 2rem; border-radius: 8px; cursor: pointer; font-weight: bold; transition: all 0.2s; }
      .btn-gen:hover { background: #6a5ae0; transform: translateY(-1px); box-shadow: 0 5px 15px rgba(124, 111, 240, 0.3); }
      .btn-gen:disabled { opacity: 0.5; cursor: not-allowed; }

      /* Photo Stream */
      .photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 1rem; }
      .photo-item { background: #0a0a0f; border: 1px solid #1e1e30; border-radius: 10px; overflow: hidden; transition: transform 0.2s; }
      .photo-item:hover { transform: scale(1.02); }
      .photo-img { width: 100%; height: 200px; object-fit: cover; border-bottom: 1px solid #1e1e30; cursor: pointer; }
      .photo-meta { padding: 0.8rem; font-size: 0.7rem; color: #6a6a80; line-height: 1.4; }
      .photo-prompt { color: #eeeef4; font-style: italic; display: block; margin-top: 0.3rem; }
    </style>

    <div class="img-container">
      <div class="img-card" style="border-left: 4px solid #7c6ff0;">
        <h2>Neural Imaging Interface</h2>
        <div class="gen-form">
          <textarea id="gen-prompt" class="gen-input" placeholder="Describe the neural projection..." rows="3"></textarea>
          <div class="gen-row">
            <div>
              <label style="font-size:0.6rem; color:#6a6a80; text-transform:uppercase;">Provider</label>
              <select id="gen-provider" class="gen-input" style="padding: 0.4rem;">
                <option value="venice">Venice.ai (Turbo)</option>
                <option value="grok">xAI Grok (Pro)</option>
              </select>
            </div>
            <div style="display:flex; flex-direction:column; gap:0.5rem; margin-top:0.5rem;">
              <div style="display:flex; align-items:center; gap:0.5rem;">
                <input type="checkbox" id="gen-face-id" checked>
                <label for="gen-face-id" style="font-size:0.75rem; color:#eeeef4;">Apply Face-ID (Prompt)</label>
              </div>
              <div style="display:flex; align-items:center; gap:0.5rem;">
                <input type="checkbox" id="gen-face-swap">
                <label for="gen-face-swap" style="font-size:0.75rem; color:#7c6ff0; font-weight:bold;">Apply Physical Face-Swap (AI)</label>
              </div>
            </div>
            <button id="btn-generate" class="btn-gen" onclick="generateNeuralImage()">Visualize</button>
          </div>
          <div id="gen-status" style="font-size: 0.75rem; color: #7c6ff0;"></div>
        </div>
      </div>

      <div class="img-card">
        <h2>Life Stream / Photo History</h2>
        <div id="photo-stream" class="photo-grid">
          <p style="color: #6a6a80; font-size: 0.8rem;">No images generated yet.</p>
        </div>
      </div>
    </div>
  `;

  updateGalleryDisplay();
}

async function updateGalleryDisplay() {
  const stream = document.getElementById('photo-stream');
  if (!stream) return;

  try {
    const resp = await fetch('/v1/plugins/image_gen/gallery');
    const images = await resp.json();

    if (images && images.length > 0) {
      stream.innerHTML = images.map(img => `
        <div class="photo-item">
          <img src="${img.url}" class="photo-img" onclick="window.open(this.src)">
          <div class="photo-meta">
            <span>${img.timestamp.split('T')[0]} • ${img.provider.toUpperCase()}</span>
            <span class="photo-prompt">${img.prompt.slice(0, 100)}...</span>
          </div>
        </div>
      `).join('');
    }
  } catch (e) {
    console.error("Gallery Update Error:", e);
  }
}

async function generateNeuralImage() {
  const prompt = document.getElementById('gen-prompt').value;
  const provider = document.getElementById('gen-provider').value;
  const faceId = document.getElementById('gen-face-id').checked;
  const faceSwap = document.getElementById('gen-face-swap').checked;
  const status = document.getElementById('gen-status');
  const btn = document.getElementById('btn-generate');

  if (!prompt) return;

  btn.disabled = true;
  status.textContent = "Initiating neural projection... please wait.";

  try {
    const resp = await fetch('/v1/plugins/image_gen/generate', {
      method: 'POST',
      body: JSON.stringify({ prompt, provider, apply_face_id: faceId, apply_face_swap: faceSwap })
    });
    const result = await resp.json();
    
    if (result.success) {
      status.textContent = "Projection complete.";
      document.getElementById('gen-prompt').value = "";
      updateGalleryDisplay();
    } else {
      status.textContent = "Error: " + result.error;
    }
  } catch (e) {
    status.textContent = "API Error: " + e.message;
  } finally {
    btn.disabled = false;
  }
}

// Initialize
setTimeout(initImageGenUI, 100);
window.generateNeuralImage = generateNeuralImage;
