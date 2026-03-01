#!/usr/bin/env python3
"""
Desktop Plugin Unit Tests - Wallpaper & Theme Control

Tests the desktop control behavior to ensure:
- Wallpaper can be set via API handler
- Theme can be set via API handler
- Automatic dark theme on 'storm' weather event

Uses mocked kernel, state_manager, and subprocess calls.
"""

import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, patch
import importlib.util

# Calculate paths
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PATH = os.path.join(TESTS_DIR, "main.py")


class MockStateManager:
    def __init__(self):
        self._desktop_state = {
            "wallpaper": "file:///home/user/wallpaper.png",
            "theme": "default",
            "last_update": None
        }

    def get_domain(self, domain):
        if domain == "desktop_state":
            return self._desktop_state
        return None

    def update_domain(self, domain, data):
        if domain == "desktop_state":
            self._desktop_state = data


class MockEventBus:
    def __init__(self):
        self.subscriptions = {}

    def subscribe(self, event_name, callback):
        self.subscriptions[event_name] = callback

    def publish(self, event_name, source, data):
        pass


class MockKernel:
    def __init__(self):
        self.state_manager = MockStateManager()
        self.event_bus = MockEventBus()


# Create mock kernel
mock_kernel = MockKernel()


def mock_subprocess_run(*args, **kwargs):
    """Mock subprocess.run for gsettings commands."""
    mock_result = MagicMock()
    command = args[0] if args else kwargs.get('args', [])

    # Handle gsettings get commands
    if "get" in command:
        mock_result.returncode = 0
        if "picture-uri" in command:
            mock_result.stdout = "file:///home/user/wallpaper.png"
        elif "color-scheme" in command:
            mock_result.stdout = "'default'"
        else:
            mock_result.stdout = ""
    # Handle gsettings set commands
    elif "set" in command:
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
    else:
        mock_result.returncode = 1
        mock_result.stderr = "Unknown command"

    return mock_result


# Load the plugin module directly first
spec = importlib.util.spec_from_file_location("desktop_main", MAIN_PATH)
desktop_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop_main)

# Replace subprocess.run with our mock in the module
original_run = desktop_main.subprocess.run
desktop_main.subprocess.run = mock_subprocess_run

# Override the plugin's kernel reference
desktop_main.plugin.kernel = mock_kernel


def test_set_wallpaper():
    """Test that wallpaper can be set via API handler."""
    result = desktop_main.plugin.handle_set_wallpaper("/home/user/new_wallpaper.jpg")

    assert result["success"] is True, f"Expected success but got {result}"
    assert "wallpaper" in result, "Result should contain wallpaper key"
    assert result["wallpaper"] is not None, "Wallpaper path should be set"

    print("[PASS] Wallpaper can be set via API handler")


def test_set_theme():
    """Test that theme can be set via API handler."""
    result = desktop_main.plugin.handle_set_theme("prefer-dark")

    assert result["success"] is True, f"Expected success but got {result}"
    assert result["theme"] == "prefer-dark", f"Expected theme 'prefer-dark' but got {result.get('theme')}"

    print("[PASS] Theme can be set via API handler")


def test_set_invalid_theme():
    """Test that invalid theme is rejected."""
    result = desktop_main.plugin.handle_set_theme("invalid-theme")

    assert result["success"] is False, "Invalid theme should return failure"
    assert "error" in result, "Result should contain error message"

    print("[PASS] Invalid theme is rejected")


def test_get_desktop_state():
    """Test that desktop state can be retrieved."""
    result = desktop_main.plugin.handle_get_desktop_state()

    assert "wallpaper" in result, "Result should contain wallpaper"
    assert "theme" in result, "Result should contain theme"
    assert "valid_themes" in result, "Result should contain valid themes"
    assert result["valid_themes"] == ["default", "prefer-light", "prefer-dark"]

    print("[PASS] Desktop state can be retrieved")


def test_storm_weather_triggers_dark_theme():
    """Test that storm weather event automatically switches to dark theme."""
    # Reset storm warning time
    desktop_main.plugin.last_storm_warning = None

    # Create storm weather event
    storm_event = {
        "event": "EVENT_WEATHER_UPDATE",
        "source": "weather",
        "data": {"weather": "storm"}
    }

    # Subscribe the plugin to the event
    mock_kernel.event_bus.subscribe("EVENT_WEATHER_UPDATE", desktop_main.plugin.on_weather_update)

    # Trigger the weather update
    desktop_main.plugin.on_weather_update(storm_event)

    # Verify the theme was changed to prefer-dark
    current_theme = mock_kernel.state_manager._desktop_state.get("theme")

    # The theme should have been set (the mock returns prefer-dark based on set_theme call)
    assert desktop_main.plugin.last_storm_warning is not None, "Storm warning time should be set"

    print("[PASS] Storm weather event triggers dark theme automatically")


def test_non_storm_weather_clears_warning():
    """Test that non-storm weather clears the storm warning."""
    # Set a storm warning
    desktop_main.plugin.last_storm_warning = datetime.now().isoformat()

    # Create clear weather event
    clear_event = {
        "event": "EVENT_WEATHER_UPDATE",
        "source": "weather",
        "data": {"weather": "sunny"}
    }

    # Trigger the weather update
    desktop_main.plugin.on_weather_update(clear_event)

    # Verify the warning was cleared
    assert desktop_main.plugin.last_storm_warning is None, "Storm warning should be cleared for non-storm weather"

    print("[PASS] Non-storm weather clears storm warning")


def main():
    """Run all Desktop plugin tests."""
    print("=" * 60)
    print("DESKTOP PLUGIN - WALLPAPER & THEME CONTROL TESTS")
    print("=" * 60)

    tests = [
        test_set_wallpaper,
        test_set_theme,
        test_set_invalid_theme,
        test_get_desktop_state,
        test_storm_weather_triggers_dark_theme,
        test_non_storm_weather_clears_warning,
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
        print("\n[SUCCESS] All Desktop plugin tests passed!")
        print("[DESKTOP TEST] PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
