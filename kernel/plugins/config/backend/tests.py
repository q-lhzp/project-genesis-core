#!/usr/bin/env python3
"""
Config Plugin Unit Tests - Model Configuration Tests
Tests model fetching and configuration saving.
"""

import sys
import os
import json
import tempfile
import importlib.util
from unittest.mock import MagicMock, patch

# Calculate paths
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PATH = os.path.join(TESTS_DIR, "main.py")


class MockStateManager:
    """Mock state manager."""
    def __init__(self):
        pass

    def get_domain(self, domain):
        return {}

    def update_domain(self, domain, data):
        pass


class MockKernel:
    """Mock kernel with state_manager."""
    def __init__(self):
        self.state_manager = MockStateManager()
        self.workspace = tempfile.mkdtemp()


# Create mock kernel
mock_kernel = MockKernel()

# Load the plugin module directly
spec = importlib.util.spec_from_file_location("config_main", MAIN_PATH)
config_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_main)

# Override the plugin's kernel reference
config_main.plugin.kernel = mock_kernel


def test_fetch_available_models():
    """Test fetching available models from OpenClaw."""
    mock_models = [
        {"name": "claude-opus-4-6", "available": True, "missing": False},
        {"name": "claude-sonnet-4-6", "available": True, "missing": False},
        {"name": "claude-haiku-4-5", "available": True, "missing": False},
    ]

    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"models": mock_models})
        mock_run.return_value = mock_result

        # Clear cache to force fresh fetch
        config_main.plugin._models_cache = None

        models = config_main.plugin.get_available_models()

        assert models is not None, "Should return models list"
        assert len(models) == 3, f"Should have 3 models, got {len(models)}"
        assert models[0]["name"] == "claude-opus-4-6", "First model should be opus"

        print(f"[TEST] Fetched {len(models)} available models")
        print("[PASS] get_available_models() works correctly")


def test_save_model_configuration():
    """Test saving model configuration."""
    # Create temporary config files in temp directory
    temp_dir = mock_kernel.workspace

    # Override config paths
    config_main.AGENT_CONFIG_PATH = os.path.join(temp_dir, "my-agent-config.json")
    config_main.MODEL_CONFIG_PATH = os.path.join(temp_dir, "data", "model_config.json")

    assignments = {
        "Persona": "claude-opus-4-6",
        "Analyst": "claude-sonnet-4-6",
        "Developer": "claude-haiku-4-5",
        "Limbic": "claude-haiku-4-5"
    }

    result = config_main.plugin.save_config(assignments)

    assert result is True, "save_config should return True"

    # Verify agent config was saved
    with open(config_main.AGENT_CONFIG_PATH, "r") as f:
        agent_config = json.load(f)

    assert len(agent_config) == 4, "Should have 4 role assignments"
    assert agent_config[0]["agent"] == "Persona", "First agent should be Persona"
    assert agent_config[0]["model"] == "claude-opus-4-6", "Persona model should be opus"

    # Verify model config was saved
    with open(config_main.MODEL_CONFIG_PATH, "r") as f:
        model_config = json.load(f)

    assert "mac_assignments" in model_config, "Should have mac_assignments"
    assert model_config["mac_assignments"]["persona"] == "claude-opus-4-6", "MAC persona should be set"

    print("[TEST] Saved model configuration to files")
    print("[PASS] save_config() works correctly")


def test_get_role_assignments():
    """Test getting current role assignments."""
    # Use the temp config we just created
    temp_dir = mock_kernel.workspace
    config_main.AGENT_CONFIG_PATH = os.path.join(temp_dir, "my-agent-config.json")

    assignments = config_main.plugin.get_role_assignments()

    assert assignments is not None, "Should return assignments"
    assert "Persona" in assignments, "Should have Persona assignment"
    assert assignments["Persona"] == "claude-opus-4-6", "Persona should use opus"

    print(f"[TEST] Got {len(assignments)} role assignments")
    print("[PASS] get_role_assignments() works correctly")


def test_set_role_model():
    """Test setting a specific role's model."""
    temp_dir = mock_kernel.workspace
    config_main.AGENT_CONFIG_PATH = os.path.join(temp_dir, "my-agent-config.json")

    # Update a role
    result = config_main.plugin.set_role_model("Analyst", "claude-opus-4-6")

    assert result is True, "set_role_model should return True"

    # Verify update
    assignments = config_main.plugin.get_role_assignments()
    assert assignments["Analyst"] == "claude-opus-4-6", "Analyst should now use opus"

    print("[TEST] Updated Analyst to use claude-opus-4-6")
    print("[PASS] set_role_model() works correctly")


def test_config_plugin_initializes():
    """Test that ConfigPlugin initializes correctly."""
    assert config_main.plugin.kernel is not None, "Plugin should have kernel"
    assert hasattr(config_main.plugin, '_models_cache'), "Plugin should have cache"

    print("[PASS] ConfigPlugin initializes correctly")


def main():
    """Run all CONFIG plugin tests."""
    print("=" * 60)
    print("CONFIG PLUGIN - MODEL CONFIGURATION TESTS")
    print("=" * 60)

    tests = [
        test_config_plugin_initializes,
        test_fetch_available_models,
        test_save_model_configuration,
        test_get_role_assignments,
        test_set_role_model,
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
        print("\n[SUCCESS] All CONFIG tests passed!")
        print("[CONFIG TEST] PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
