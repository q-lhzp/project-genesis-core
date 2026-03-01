/**
 * Vault Plugin Frontend - View Module (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

async function initVaultUI() {
  const root = document.getElementById('plugin-root-vault');
  if (!root) return;

  root.innerHTML = `
    <style>
      .vault-container { max-width: 1000px; margin: 0 auto; padding: 1.5rem 2rem; font-family: 'DM Sans', sans-serif; }
      .vault-card { background: #12121a; border: 1px solid #1e1e30; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
      .vault-card h2 { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; color: #6a6a80; border-bottom: 1px solid #1e1e30; padding-bottom: 0.8rem; margin-bottom: 1rem; }
      
      .api-config { background: #0a0a0f; padding: 1rem; border-radius: 8px; margin-top: 1rem; border: 1px solid #1e1e30; }
      .config-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem; }
      .vault-input { width: 100%; background: #0a0a0f; color: #c8c8d8; border: 1px solid #1e1e30; border-radius: 4px; padding: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }
      .vault-label { font-size: 0.7rem; color: #6a6a80; text-transform: uppercase; display: block; margin-bottom: 0.2rem; }
      
      .trade-panel { border-left: 4px solid #7c6ff0; }
      .trade-grid { display: grid; grid-template-columns: 1fr 1fr 1fr auto; gap: 0.8rem; align-items: end; }
      
      .portfolio-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
      @media (max-width: 800px) { .portfolio-grid { grid-template-columns: 1fr; } }
      
      .tx-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
      .tx-table th { text-align: left; color: #6a6a80; padding: 0.5rem; border-bottom: 1px solid #1e1e30; }
      .tx-table td { padding: 0.5rem; border-bottom: 1px solid #0a0a0f; }
      .tx-buy { color: #50c878; }
      .tx-sell { color: #e05050; }
      
      .status-pill { padding: 0.2rem 0.6rem; border-radius: 10px; font-size: 0.6rem; font-weight: bold; text-transform: uppercase; }
      .status-paper { background: rgba(124, 111, 240, 0.15); color: #7c6ff0; }
      .status-live { background: rgba(80, 200, 120, 0.15); color: #50c878; }
      
      .btn-save { background: #50c878; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; margin-top: 1rem; }
      .btn-trade { background: #7c6ff0; color: white; border: none; padding: 0.5rem 1.5rem; border-radius: 4px; cursor: pointer; height: 36px; font-weight: bold; }
    </style>

    <div class="vault-container">
      <div class="vault-card" style="border-left: 4px solid #50c878;">
        <h2>The Vault - Real Asset Trading</h2>
        <p style="color: #6a6a80; font-size: 0.85rem;">Currently in <span id="v-status-mode" class="status-pill status-paper">Paper Trading</span> mode via <span id="v-status-provider">Kraken</span>.</p>
        
        <div class="api-config">
          <span class="vault-label">API Configuration</span>
          <div class="config-grid">
            <div>
              <label class="vault-label">Provider</label>
              <select id="v-config-provider" class="vault-input">
                <option value="kraken">Kraken (Crypto)</option>
                <option value="alpaca">Alpaca (Stocks)</option>
              </select>
            </div>
            <div>
              <label class="vault-label">Mode</label>
              <select id="v-config-mode" class="vault-input">
                <option value="paper">Paper Trading (Sandbox)</option>
                <option value="live">Live Trading</option>
              </select>
            </div>
          </div>
          <button class="btn-save" onclick="saveVaultConfig()">💾 Save Configuration</button>
        </div>

        <div class="api-config trade-panel">
          <span class="vault-label">Quick Trade</span>
          <div class="trade-grid">
            <div>
              <label class="vault-label">Symbol</label>
              <input type="text" id="v-trade-symbol" class="vault-input" placeholder="BTC, ETH...">
            </div>
            <div>
              <label class="vault-label">Amount</label>
              <input type="number" id="v-trade-amount" class="vault-input" step="any" placeholder="0.1">
            </div>
            <div>
              <label class="vault-label">Action</label>
              <select id="v-trade-type" class="vault-input">
                <option value="buy">BUY</option>
                <option value="sell">SELL</option>
              </select>
            </div>
            <button class="btn-trade" onclick="executeVaultTrade()">TRADE</button>
          </div>
          <div id="v-trade-msg" style="margin-top: 0.5rem; font-size: 0.75rem;"></div>
        </div>
      </div>

      <div class="portfolio-grid">
        <div class="vault-card">
          <h2>Portfolio</h2>
          <div id="v-portfolio-list" style="font-size: 0.85rem;">Loading assets...</div>
        </div>
        <div class="vault-card">
          <h2>Market Analysis</h2>
          <div style="font-style: italic; font-size: 0.85rem; color: #6a6a80; line-height: 1.4;">
            <p>Wait for market signals or AI-driven insights...</p>
          </div>
        </div>
      </div>

      <div class="vault-card">
        <h2>Recent Transactions</h2>
        <div id="v-tx-list">
          <p style="color: #6a6a80; font-size: 0.8rem;">No transactions recorded.</p>
        </div>
      </div>
    </div>
  `;

  updateVaultDisplay();
  setInterval(updateVaultDisplay, 10000);
}

async function updateVaultDisplay() {
  const portfolio = document.getElementById('v-portfolio-list');
  const txList = document.getElementById('v-tx-list');
  const modePill = document.getElementById('v-status-mode');
  const providerLabel = document.getElementById('v-status-provider');

  if (!portfolio) return;

  try {
    const resp = await fetch('/v1/plugins/vault/status');
    const data = await resp.json();

    if (!data.success) return;

    // 1. Mode & Provider
    modePill.textContent = data.mode + " trading";
    modePill.className = "status-pill " + (data.mode === 'live' ? "status-live" : "status-paper");
    providerLabel.textContent = data.provider.charAt(0).upperCase() + data.provider.slice(1);

    // 2. Portfolio
    let phtml = '<table class="tx-table"><tr><th>Asset</th><th>Balance</th><th>Avg Price</th></tr>';
    for (const [asset, bal] of Object.entries(data.balances)) {
      const pos = data.positions[asset] || { avg_price: '-' };
      phtml += `<tr><td><strong>${asset}</strong></td><td>${bal.toFixed(4)}</td><td>${pos.avg_price}</td></tr>`;
    }
    phtml += '</table>';
    portfolio.innerHTML = phtml;

    // 3. Transactions
    if (data.transactions && data.transactions.length > 0) {
      let thtml = '<table class="tx-table"><tr><th>Date</th><th>Type</th><th>Symbol</th><th>Qty</th><th>Price</th></tr>';
      data.transactions.forEach(tx => {
        const date = tx.timestamp.split('T')[1].split('.')[0];
        thtml += `
          <tr>
            <td style="color:#6a6a80">${date}</td>
            <td class="tx-${tx.type}">${tx.type.toUpperCase()}</td>
            <td>${tx.symbol}</td>
            <td>${tx.amount}</td>
            <td>$${tx.price.toLocaleString()}</td>
          </tr>
        `;
      });
      thtml += '</table>';
      txList.innerHTML = thtml;
    }

  } catch (e) {
    console.error("Vault Update Error:", e);
  }
}

async function saveVaultConfig() {
  const provider = document.getElementById('v-config-provider').value;
  const mode = document.getElementById('v-config-mode').value;
  
  try {
    const resp = await fetch('/v1/plugins/vault/config', {
      method: 'POST',
      body: JSON.stringify({ api_provider: provider, mode: mode })
    });
    const result = await resp.json();
    if (result.success) {
      alert("Vault configuration updated.");
      updateVaultDisplay();
    }
  } catch (e) {
    alert("Error saving config: " + e.message);
  }
}

async function executeVaultTrade() {
  const symbol = document.getElementById('v-trade-symbol').value;
  const amount = document.getElementById('v-trade-amount').value;
  const type = document.getElementById('v-trade-type').value;
  const msg = document.getElementById('v-trade-msg');

  if (!symbol || !amount) {
    msg.innerHTML = '<span style="color:#e05050">Please enter symbol and amount.</span>';
    return;
  }

  msg.innerHTML = '<span style="color:#7c6ff0">Executing trade...</span>';

  try {
    const resp = await fetch('/v1/plugins/vault/trade', {
      method: 'POST',
      body: JSON.stringify({ symbol, amount, type })
    });
    const result = await resp.json();
    if (result.success) {
      msg.innerHTML = '<span style="color:#50c878">Trade successful: ' + result.transaction.id + '</span>';
      updateVaultDisplay();
    } else {
      msg.innerHTML = '<span style="color:#e05050">Error: ' + result.error + '</span>';
    }
  } catch (e) {
    msg.innerHTML = '<span style="color:#e05050">API Error: ' + e.message + '</span>';
  }
}

// Initialize
setTimeout(initVaultUI, 100);
window.saveVaultConfig = saveVaultConfig;
window.executeVaultTrade = executeVaultTrade;
