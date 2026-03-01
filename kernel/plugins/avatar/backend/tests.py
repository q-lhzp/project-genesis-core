#!/usr/bin/env python3
"""
Avatar Plugin Unit Tests - BlendShapes Expression Logic
Tests the embodiment engine that maps biological needs to visual expressions.
"""

import sys
import os
import importlib.util
from datetime import datetime
from unittest.mock import MagicMock

# Calculate paths
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PATH = os.path.join(TESTS_DIR, "main.py")


class MockStateManager:
    """Mock state manager with physique and avatar_state domains."""
    def __init__(self):
        self._physique = {
            "needs": {
                "energy": 100.0,
                "hunger": 0.0,
                "thirst": 0.0,
                "stress": 0.0,
                "arousal": 0.0,
            },
            "last_tick": None
        }
        self._avatar_state = {}

    def get_domain(self, domain):
        if domain == "physique":
            return self._physique
        elif domain == "avatar_state":
            return self._avatar_state
        elif domain == "avatar_config":
            return {"vrm_path": "/shared/media/avatar/q_avatar.vrm"}
        return None

    def update_domain(self, domain, data):
        if domain == "avatar_state":
            self._avatar_state = data


class MockKernel:
    """Mock kernel with state_manager."""
    def __init__(self):
        self.state_manager = MockStateManager()


# Create mock kernel
mock_kernel = MockKernel()

# Load the plugin module directly
spec = importlib.util.spec_from_file_location("avatar_main", MAIN_PATH)
avatar_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(avatar_main)

# Override the plugin's kernel reference
avatar_main.plugin.kernel = mock_kernel


def test_blendshapes_stress_mapping():
    """Test that high stress (>60) generates angry expression."""
    # Reset state
    mock_kernel.state_manager._physique["needs"]["stress"] = 80.0
    mock_kernel.state_manager._avatar_state = {}

    # Run expression update
    avatar_main.plugin._update_expressions()

    # Get blend shapes
    state = mock_kernel.state_manager._avatar_state
    blend_shapes = state.get("blend_shapes", {})
    angry = blend_shapes.get("angry", 0.0)

    print(f"[TEST] Stress=80, Angry blend shape: {angry:.2f}")

    assert angry > 0, f"Angry should be > 0 when stress is 80, got {angry}"
    assert angry <= 1.0, f"Angry should be <= 1.0, got {angry}"
    print("[PASS] High stress generates angry expression")


def test_blendshapes_hunger_mapping():
    """Test that high hunger (>70) generates sad expression."""
    # Reset state
    mock_kernel.state_manager._physique["needs"]["hunger"] = 85.0
    mock_kernel.state_manager._physique["needs"]["stress"] = 0.0
    mock_kernel.state_manager._avatar_state = {}

    # Run expression update
    avatar_main.plugin._update_expressions()

    # Get blend shapes
    state = mock_kernel.state_manager._avatar_state
    blend_shapes = state.get("blend_shapes", {})
    sad = blend_shapes.get("sad", 0.0)

    print(f"[TEST] Hunger=85, Sad blend shape: {sad:.2f}")

    assert sad > 0, f"Sad should be > 0 when hunger is 85, got {sad}"
    assert sad <= 1.0, f"Sad should be <= 1.0, got {sad}"
    print("[PASS] High hunger generates sad expression")


def test_blendshapes_low_stress_relaxed():
    """Test that low stress generates relaxed expression."""
    # Reset state
    mock_kernel.state_manager._physique["needs"]["stress"] = 10.0
    mock_kernel.state_manager._avatar_state = {}

    # Run expression update
    avatar_main.plugin._update_expressions()

    # Get blend shapes
    state = mock_kernel.state_manager._avatar_state
    blend_shapes = state.get("blend_shapes", {})
    relaxed = blend_shapes.get("relaxed", 0.0)

    print(f"[TEST] Stress=10, Relaxed blend shape: {relaxed:.2f}")

    assert relaxed > 0, f"Relaxed should be > 0 when stress is low, got {relaxed}"
    print("[PASS] Low stress generates relaxed expression")


def test_blendshapes_stay_in_bounds():
    """Test that blend shapes stay within valid bounds (0-1)."""
    # Test with extreme values
    mock_kernel.state_manager._physique["needs"]["stress"] = 100.0
    mock_kernel.state_manager._physique["needs"]["hunger"] = 100.0
    mock_kernel.state_manager._avatar_state = {}

    # Run expression update
    avatar_main.plugin._update_expressions()

    # Get blend shapes
    state = mock_kernel.state_manager._avatar_state
    blend_shapes = state.get("blend_shapes", {})

    for key, value in blend_shapes.items():
        assert 0 <= value <= 1.0, f"Blend shape '{key}' out of bounds: {value}"

    print("[PASS] All blend shapes stay within bounds (0-1.0)")


def test_handle_pose():
    """Test pose handler updates avatar state."""
    # Reset state
    mock_kernel.state_manager._avatar_state = {}

    # Call handle_pose
    result = avatar_main.plugin.handle_pose({"pose": "sitting"})

    # Check result
    assert result.get("success") == True, f"Pose should succeed: {result}"

    # Check state
    state = mock_kernel.state_manager._avatar_state
    assert state.get("pose") == "sitting", f"Pose should be 'sitting', got {state.get('pose')}"

    print("[PASS] Pose handler updates avatar state correctly")


def main():
    """Run all AVATAR plugin tests."""
    print("=" * 60)
    print("AVATAR PLUGIN - BLENDSHAPES EXPRESSION TESTS")
    print("=" * 60)

    tests = [
        test_blendshapes_stress_mapping,
        test_blendshapes_hunger_mapping,
        test_blendshapes_low_stress_relaxed,
        test_blendshapes_stay_in_bounds,
        test_handle_pose,
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
        print("\n[SUCCESS] All AVATAR expression tests passed!")
        print("[AVATAR TEST] PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
