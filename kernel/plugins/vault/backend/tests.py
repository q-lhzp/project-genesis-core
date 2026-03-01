#!/usr/bin/env python3
"""
Vault Plugin Unit Test - Basic Trade Execution (Paper Mode)
"""

import sys
import os

# Add project root to path (parent of kernel/)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from kernel.plugins.vault.backend.main import VaultPlugin, KrakenBridge


class MockStateManager:
    """Mock state manager with vault_state."""
    def __init__(self):
        self._vault_state = {
            "mode": "paper",
            "balances": {
                "USD": 1000.0,
                "BTC": 0.0
            },
            "transactions": []
        }

    def get_domain(self, domain):
        if domain == "vault_state":
            return self._vault_state
        return None

    def update_domain(self, domain, data):
        if domain == "vault_state":
            self._vault_state = data


class MockKernel:
    """Mock kernel with state_manager."""
    def __init__(self):
        self.state_manager = MockStateManager()
        self.event_bus = None


def main():
    """Run the VAULT plugin test."""
    # Setup mock kernel
    mock_kernel = MockKernel()

    # Create VaultPlugin and initialize with mock kernel
    plugin = VaultPlugin()
    plugin.kernel = mock_kernel
    plugin.bridge = KrakenBridge(mock_kernel.state_manager, paper=True)
    plugin.bridge.kernel = mock_kernel

    # Store initial state
    initial_usd = mock_kernel.state_manager._vault_state["balances"]["USD"]
    initial_btc = mock_kernel.state_manager._vault_state["balances"]["BTC"]
    initial_tx_count = len(mock_kernel.state_manager._vault_state.get("transactions", []))

    # Call handle_trade with buy action for BTC
    result = plugin.handle_trade({
        "symbol": "BTC",
        "amount": 0.01,
        "type": "buy"
    })

    # Get updated state
    new_usd = mock_kernel.state_manager._vault_state["balances"]["USD"]
    new_btc = mock_kernel.state_manager._vault_state["balances"]["BTC"]
    transactions = mock_kernel.state_manager._vault_state.get("transactions", [])
    new_tx_count = len(transactions)

    # Assertions
    assert result.get("success") == True, f"Trade should succeed: {result}"
    assert new_usd < initial_usd, f"USD balance should decrease: {initial_usd} -> {new_usd}"
    assert new_btc > initial_btc, f"BTC balance should increase: {initial_btc} -> {new_btc}"
    assert new_tx_count > initial_tx_count, "Transaction should be added to history"

    # Print result
    print(f"[VAULT TEST] Initial USD: {initial_usd}, New USD: {new_usd}")
    print(f"[VAULT TEST] Initial BTC: {initial_btc}, New BTC: {new_btc}")
    print(f"[VAULT TEST] Transactions: {initial_tx_count} -> {new_tx_count}")
    print("[VAULT TEST] PASSED")

    sys.exit(0)


if __name__ == "__main__":
    main()
