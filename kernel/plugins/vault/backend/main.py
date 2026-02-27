"""
Vault Plugin - Economy & Trading Engine
Ported from project-genesis/skills/soul-evolution/tools/vault_bridge.py
"""

import json
import time
import logging
import urllib.request
import urllib.error
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
        return self.state_manager.get_domain("vault_state")

    def save_state(self, state):
        state["last_updated"] = datetime.now().isoformat()
        self.state_manager.update_domain("vault_state", state)

class KrakenBridge(BaseBridge):
    def get_status(self):
        state = self.get_state()
        return {
            "success": True,
            "mode": state.get("mode", "paper"),
            "balances": state.get("balances", {}),
            "positions": state.get("positions", {}),
            "transactions": state.get("transactions", [])[:10]
        }

    def execute_trade(self, symbol, amount, trade_type):
        if not self.paper:
            return {"success": False, "error": "Live trading not yet enabled in Core"}
        
        state = self.get_state()
        symbol = symbol.upper()
        price = 50000.0 if symbol == "BTC" else 100.0 # Mock price for now
        total = amount * price

        if trade_type == "buy":
            usd = state.get("balances", {}).get("USD", 0)
            if usd < total: return {"success": False, "error": "Insufficient funds"}
            state["balances"]["USD"] = usd - total
            state["balances"][symbol] = state["balances"].get(symbol, 0) + amount
        elif trade_type == "sell":
            bal = state.get("balances", {}).get(symbol, 0)
            if bal < amount: return {"success": False, "error": "Insufficient assets"}
            state["balances"]["USD"] = state["balances"].get("USD", 0) + total
            state["balances"][symbol] = bal - amount

        # Log Transaction
        tx = {"id": f"tx_{int(time.time())}", "timestamp": datetime.now().isoformat(), "symbol": symbol, "amount": amount, "price": price, "type": trade_type}
        state.setdefault("transactions", []).insert(0, tx)
        self.save_state(state)
        
        # Publish Event
        import asyncio
        if self.kernel and self.kernel.event_bus:
            # We use ensure_future because this is a sync handler called from the API thread
            asyncio.run_coroutine_threadsafe(
                self.kernel.event_bus.publish("EVENT_TRADE_EXECUTED", "plugin.vault", tx),
                asyncio.get_event_loop()
            )
            
        return {"success": True, "transaction": tx}

# =============================================================================
# PLUGIN CLASS
# =============================================================================

class VaultPlugin:
    def __init__(self):
        self.kernel = None
        self.bridge = None

    def initialize(self, kernel):
        self.kernel = kernel
        # Auto-detect bridge from state
        state = self.kernel.state_manager.get_domain("vault_state")
        paper = state.get("mode", "paper") == "paper"
        self.bridge = KrakenBridge(self.kernel.state_manager, paper=paper)
        logger.info("VaultPlugin initialized with KrakenBridge")

    def on_event(self, event):
        if event.get("event") == "TICK_HOURLY":
            logger.info("Hourly pulse: Checking market status...")

    def handle_status(self):
        return self.bridge.get_status()

    def handle_trade(self, data):
        symbol = data.get("symbol")
        amount = float(data.get("amount", 0))
        trade_type = data.get("type", "buy")
        if not symbol or amount <= 0:
            return {"success": False, "error": "Invalid params"}
        return self.bridge.execute_trade(symbol, amount, trade_type)

# Global instance for loader
plugin = VaultPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_status(): return plugin.handle_status()
def handle_trade(data): return plugin.handle_trade(data)
