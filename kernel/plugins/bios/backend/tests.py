#!/usr/bin/env python3
"""
Bios Plugin Unit Tests - Metabolism Decay Logic

Tests the metabolism decay behavior to ensure:
- Energy decreases over time
- Hunger increases over time

Uses mocked kernel and state_manager.
"""

import sys
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import importlib.util

# Calculate paths
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PATH = os.path.join(TESTS_DIR, "main.py")

# Mock kernel and state_manager before importing the plugin
class MockStateManager:
    def __init__(self):
        self._physique = {
            "needs": {
                "energy": 100.0,
                "hunger": 0.0,
                "thirst": 0.0,
                "bladder": 0.0,
                "bowel": 0.0,
                "hygiene": 100.0,
                "stress": 0.0,
                "arousal": 0.0,
                "libido": 0.0
            },
            "last_tick": None
        }
        self._lifecycle = {"life_stage": "adult"}
        self._cycle = {"current_day": 1}

    def get_domain(self, domain):
        if domain == "physique":
            return self._physique
        elif domain == "lifecycle":
            return self._lifecycle
        elif domain == "cycle":
            return self._cycle
        return None

    def update_domain(self, domain, data):
        if domain == "physique":
            self._physique = data


class MockKernel:
    def __init__(self):
        self.state_manager = MockStateManager()


# Create mock kernel
mock_kernel = MockKernel()

# Load the plugin module directly
spec = importlib.util.spec_from_file_location("bios_main", MAIN_PATH)
bios_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bios_main)

# Override the plugin's kernel reference
bios_main.plugin.kernel = mock_kernel

# Store initial values for comparison
INITIAL_ENERGY = 100.0
INITIAL_HUNGER = 0.0


def test_metabolism_energy_decays():
    """Test that energy decreases over time."""
    # Set last_tick to 1 hour ago
    mock_kernel.state_manager._physique["last_tick"] = (datetime.now() - timedelta(hours=1)).isoformat()

    # Run metabolism update
    bios_main.plugin._update_metabolism()

    # Get updated needs
    needs = mock_kernel.state_manager._physique["needs"]
    energy = needs.get("energy")

    print(f"[TEST] Energy after 1 hour: {energy:.2f} (started at {INITIAL_ENERGY})")

    assert energy < INITIAL_ENERGY, f"Energy should decrease but got {energy} >= {INITIAL_ENERGY}"
    assert energy > 0, f"Energy should be positive but got {energy}"
    print("[PASS] Energy decays over time")


def test_metabolism_hunger_increases():
    """Test that hunger increases over time."""
    # Reset state
    mock_kernel.state_manager._physique["needs"]["hunger"] = 0.0
    mock_kernel.state_manager._physique["needs"]["energy"] = 100.0
    mock_kernel.state_manager._physique["last_tick"] = (datetime.now() - timedelta(hours=1)).isoformat()

    # Run metabolism update
    bios_main.plugin._update_metabolism()

    # Get updated needs
    needs = mock_kernel.state_manager._physique["needs"]
    hunger = needs.get("hunger")

    print(f"[TEST] Hunger after 1 hour: {hunger:.2f} (started at {INITIAL_HUNGER})")

    assert hunger > INITIAL_HUNGER, f"Hunger should increase but got {hunger} <= {INITIAL_HUNGER}"
    assert hunger <= 100, f"Hunger should be <= 100 but got {hunger}"
    print("[PASS] Hunger increases over time")


def test_metabolism_needs_stay_in_bounds():
    """Test that needs values stay within valid bounds (0-100)."""
    # Reset to extreme values
    mock_kernel.state_manager._physique["needs"]["energy"] = 100.0
    mock_kernel.state_manager._physique["needs"]["hunger"] = 0.0
    mock_kernel.state_manager._physique["needs"]["stress"] = 50.0
    mock_kernel.state_manager._physique["last_tick"] = (datetime.now() - timedelta(hours=10)).isoformat()

    # Run metabolism update multiple times
    for _ in range(5):
        bios_main.plugin._update_metabolism()

    needs = mock_kernel.state_manager._physique["needs"]

    for key, value in needs.items():
        assert 0 <= value <= 100, f"Need '{key}' out of bounds: {value}"

    print("[PASS] All needs stay within bounds (0-100)")


def test_metabolism_no_change_on_rapid_ticks():
    """Test that rapid ticks (< 1 minute) don't cause changes."""
    mock_kernel.state_manager._physique["needs"]["energy"] = 100.0
    mock_kernel.state_manager._physique["needs"]["hunger"] = 0.0
    # Set last_tick to just now
    mock_kernel.state_manager._physique["last_tick"] = datetime.now().isoformat()

    initial_energy = mock_kernel.state_manager._physique["needs"]["energy"]
    initial_hunger = mock_kernel.state_manager._physique["needs"]["hunger"]

    # Run metabolism update
    bios_main.plugin._update_metabolism()

    energy = mock_kernel.state_manager._physique["needs"]["energy"]
    hunger = mock_kernel.state_manager._physique["needs"]["hunger"]

    # Should be unchanged (or very minimal change)
    assert abs(energy - initial_energy) < 0.1, f"Energy changed too much on rapid tick: {energy} vs {initial_energy}"
    print("[PASS] No significant change on rapid ticks (< 1 minute)")


def main():
    """Run all BIOS metabolism tests."""
    print("=" * 60)
    print("BIOS PLUGIN - METABOLISM DECAY TESTS")
    print("=" * 60)

    tests = [
        test_metabolism_energy_decays,
        test_metabolism_hunger_increases,
        test_metabolism_needs_stay_in_bounds,
        test_metabolism_no_change_on_rapid_ticks,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            print(f"\n>>> Running: {test.__name__}")
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n[SUCCESS] All BIOS metabolism tests passed!")
        print("[BIOS TEST] PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
