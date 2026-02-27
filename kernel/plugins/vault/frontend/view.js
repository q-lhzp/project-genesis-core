/**
 * Vault Plugin Frontend - View Module (v1.0.0)
 */

async function initVaultUI() {
  const root = document.getElementById('plugin-root-vault-engine');
  if (!root) return;

  root.innerHTML = `
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:2rem;">
      <div class="panel-card">
        <h3>💰 Balances</h3>
        <div id="vault-balances" style="display:grid; gap:0.5rem;">Loading...</div>
      </div>
      <div class="panel-card">
        <h3>📈 Quick Trade (Paper)</h3>
        <div style="display:grid; gap:1rem;">
          <input type="text" id="trade-symbol" placeholder="BTC" style="padding:0.5rem; background:#0a0a12; color:#fff; border:1px solid #2a2a3a;">
          <input type="number" id="trade-amount" placeholder="0.1" step="0.01" style="padding:0.5rem; background:#0a0a12; color:#fff; border:1px solid #2a2a3a;">
          <div style="display:flex; gap:0.5rem;">
            <button onclick="executeTrade('buy')" style="flex:1; background:#10b981; color:#fff; border:none; padding:0.75rem; cursor:pointer;">BUY</button>
            <button onclick="executeTrade('sell')" style="flex:1; background:#ef4444; color:#fff; border:none; padding:0.75rem; cursor:pointer;">SELL</button>
          </div>
        </div>
      </div>
      <div class="panel-card" style="grid-column: span 2;">
        <h3>📜 Recent Transactions</h3>
        <div id="vault-transactions" style="font-family:monospace; font-size:0.8rem; background:#0a0a12; padding:1rem; border-radius:4px;">No transactions.</div>
      </div>
    </div>
  `;

  updateVaultDisplay();
  setInterval(updateVaultDisplay, 10000);
}

async function updateVaultDisplay() {
  try {
    const resp = await fetch('/v1/plugins/vault/status');
    const data = await resp.json();
    
    if (data.success) {
      const balEl = document.getElementById('vault-balances');
      balEl.innerHTML = Object.entries(data.balances).map(([cur, val]) => `
        <div style="display:flex; justify-content:space-between;">
          <strong>${cur}:</strong>
          <span>${val.toFixed(cur === 'USD' ? 2 : 4)}</span>
        </div>
      `).join('');

      const txEl = document.getElementById('vault-transactions');
      txEl.innerHTML = (data.transactions || []).map(tx => `
        <div style="margin-bottom:0.25rem;">
          [${tx.timestamp.slice(11,19)}] ${tx.type.toUpperCase()} ${tx.amount} ${tx.symbol} @ $${tx.price}
        </div>
      `).join('') || 'No transactions yet.';
    }
  } catch (e) { console.error("Vault UI Error:", e); }
}

async function executeTrade(type) {
  const symbol = document.getElementById('trade-symbol').value;
  const amount = document.getElementById('trade-amount').value;
  if (!symbol || !amount) return;

  try {
    const resp = await fetch('/v1/plugins/vault/trade', {
      method: 'POST',
      body: JSON.stringify({ symbol, amount, type })
    });
    const res = await resp.json();
    if (res.success) {
      updateVaultDisplay();
      alert("Trade successful!");
    } else {
      alert("Error: " + res.error);
    }
  } catch (e) { console.error("Trade Error:", e); }
}

setTimeout(initVaultUI, 100);
window.executeTrade = executeTrade;
