"""
Vault Plugin - Economy & Trading Engine (v7.0 Stable)
Ported 1:1 from project-genesis Legacy (vault_bridge.py)
"""

import json
import time
import logging
import urllib.request
import urllib.error
import hmac
import hashlib
import base64
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='[VAULT] %(message)s')
logger = logging.getLogger("vault")

# =============================================================================
# TRADING BRIDGES
# =============================================================================

class BaseBridge:
    def __init__(self, state_manager, paper=True):
        self.state_manager = state_manager
        self.paper = paper

    def get_state(self):
        return self.state_manager.get_domain("vault_state") or {
            "mode": "paper",
            "balances": {"USD": 10000.0},
            "positions": {},
            "transactions": []
        }

    def save_state(self, state):
        state["last_updated"] = datetime.now().isoformat()
        self.state_manager.update_domain("vault_state", state)

class KrakenBridge(BaseBridge):
    def __init__(self, state_manager, api_key="", api_secret="", paper=True):
        super().__init__(state_manager, paper)
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.kraken.com"

    def get_status(self):
        state = self.get_state()
        return {
            "success": True,
            "mode": state.get("mode", "paper"),
            "provider": "kraken",
            "balances": state.get("balances", {}),
            "positions": state.get("positions", {}),
            "transactions": state.get("transactions", [])[:20]
        }

    def get_price(self, symbol: str):
        symbol_map = {
            "BTC": "XXBTZUSD", "ETH": "XETHZUSD", "SOL": "SOLUSD",
            "XRP": "XXRPZUSD", "ADA": "ADAUSD", "DOGE": "XDGUSD"
        }
        pair = symbol_map.get(symbol.upper(), f"{symbol}USD")
        
        # Real price fetch (public API)
        try:
            url = f"{self.base_url}/0/public/Ticker?pair={pair}"
            with urllib.request.urlopen(url, timeout=5) as response: # SAFE: External API fetch
                data = json.loads(response.read().decode())
                if data.get("error"):
                    raise Exception(str(data["error"]))
                # Kraken ticker response is complex, get the last trade price
                result = data["result"]
                pair_key = list(result.keys())[0]
                price = float(result[pair_key]["c"][0])
                return {"success": True, "price": price}
        except Exception as e:
            logger.error(f"Price fetch error for {symbol}: {e}")
            # Fallback to mock price if offline
            mock_prices = {"BTC": 60000, "ETH": 3000, "SOL": 150}
            return {"success": True, "price": mock_prices.get(symbol.upper(), 100.0), "mock": True}

    def execute_trade(self, symbol, amount, trade_type):
        state = self.get_state()
        symbol = symbol.upper()
        
        price_data = self.get_price(symbol)
        if not price_data["success"]: return price_data
        price = price_data["price"]
        total = amount * price

        if trade_type == "buy":
            usd = state.get("balances", {}).get("USD", 0)
            if usd < total: return {"success": False, "error": "Insufficient funds"}
            state["balances"]["USD"] = usd - total
            state["balances"][symbol] = state["balances"].get(symbol, 0) + amount
            
            # Position tracking
            pos = state.get("positions", {}).get(symbol, {"amount": 0, "avg_price": 0})
            new_amount = pos["amount"] + amount
            pos["avg_price"] = (pos["avg_price"] * pos["amount"] + price * amount) / new_amount
            pos["amount"] = new_amount
            state.setdefault("positions", {})[symbol] = pos

        elif trade_type == "sell":
            bal = state.get("balances", {}).get(symbol, 0)
            if bal < amount: return {"success": False, "error": "Insufficient assets"}
            state["balances"]["USD"] = state["balances"].get("USD", 0) + total
            state["balances"][symbol] = bal - amount
            
            # Update position
            if symbol in state.get("positions", {}):
                state["positions"][symbol]["amount"] -= amount
                if state["positions"][symbol]["amount"] <= 0:
                    del state["positions"][symbol]

        # Log Transaction
        tx = {
            "id": f"tx_{int(time.time())}", 
            "timestamp": datetime.now().isoformat(), 
            "symbol": symbol, 
            "amount": amount, 
            "price": price, 
            "total": total,
            "type": trade_type,
            "mode": "paper" if self.paper else "live"
        }
        state.setdefault("transactions", []).insert(0, tx)
        self.save_state(state)
        
        return {"success": True, "transaction": tx}

class AlpacaBridge(BaseBridge):
    def __init__(self, state_manager, api_key="", api_secret="", paper=True):
        super().__init__(state_manager, paper)
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"

    def get_status(self):
        state = self.get_state()
        return {
            "success": True,
            "mode": state.get("mode", "paper"),
            "provider": "alpaca",
            "balances": state.get("balances", {}),
            "positions": state.get("positions", {}),
            "transactions": state.get("transactions", [])[:20]
        }

# =============================================================================
# PLUGIN CLASS
# =============================================================================

class VaultPlugin:
    def __init__(self):
        self.kernel = None
        self.bridge = None

    def initialize(self, kernel):
        self.kernel = kernel
        # Load config from state
        vstate = self.kernel.state_manager.get_domain("vault_state")
        mconfig = self.kernel.state_manager.get_domain("model_config")
        
        provider = vstate.get("api_provider", "kraken")
        paper = vstate.get("mode", "paper") == "paper"
        
        api_key = mconfig.get("vault_api_key", "")
        api_secret = mconfig.get("vault_api_secret", "")

        if provider == "alpaca":
            self.bridge = AlpacaBridge(self.kernel.state_manager, api_key, api_secret, paper)
        else:
            self.bridge = KrakenBridge(self.kernel.state_manager, api_key, api_secret, paper)
            
        logger.info(f"VaultPlugin initialized with {provider.capitalize()}Bridge")

    def on_event(self, event):
        if event.get("event") == "TICK_HOURLY":
            logger.info("Economy Pulse: Syncing balances...")

    def handle_status(self):
        return self.bridge.get_status()

    def handle_trade(self, data):
        symbol = data.get("symbol", "").upper()
        amount = float(data.get("amount", 0))
        trade_type = data.get("type", "buy")
        if not symbol or amount <= 0:
            return {"success": False, "error": "Invalid trade parameters"}
        return self.bridge.execute_trade(symbol, amount, trade_type)

    def handle_config(self, data):
        """Update vault configuration."""
        vstate = self.kernel.state_manager.get_domain("vault_state")
        if "mode" in data: vstate["mode"] = data["mode"]
        if "api_provider" in data: vstate["api_provider"] = data["api_provider"]
        self.kernel.state_manager.update_domain("vault_state", vstate)
        
        # Re-init bridge
        self.initialize(self.kernel)
        return {"success": True, "config": vstate}

# Global instance for loader
plugin = VaultPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_status(): return plugin.handle_status()
def handle_trade(data): return plugin.handle_trade(data)
def handle_config(data): return plugin.handle_config(data)
