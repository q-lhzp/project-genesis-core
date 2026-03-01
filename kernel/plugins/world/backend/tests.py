#!/usr/bin/env python3
"""
World Plugin Unit Tests - Weather Sync & Lighting Logic

Tests the world engine to ensure:
- Weather simulation generates valid data
- Lighting calculations work correctly
- State persistence functions

Uses mocked kernel and state_manager.
"""

import sys
import os
import importlib.util
from unittest.mock import MagicMock, patch
from datetime import datetime

# Calculate paths
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PATH = os.path.join(TESTS_DIR, "main.py")

# Add tests directory to path for imports
sys.path.insert(0, TESTS_DIR)


class MockStateManager:
    def __init__(self):
        self._data = {
            "world_state": {
                "initialized": True,
                "location": {
                    "city": "Berlin",
                    "latitude": 52.52,
                    "longitude": 13.405,
                    "timezone": "Europe/Berlin"
                },
                "weather": {
                    "temperature": 18.0,
                    "condition": "clear",
                    "humidity": 65,
                    "wind_speed": 12.0,
                    "last_updated": datetime.now().isoformat()
                },
                "lighting": {
                    "sunrise": "06:45",
                    "sunset": "18:30",
                    "is_daytime": True
                },
                "atmosphere": {
                    "fog_density": 0.0,
                    "cloud_cover": 20,
                    "precipitation_chance": 10,
                    "air_quality_index": 35
                },
                "season": "winter"
            }
        }

    def get_domain(self, domain):
        return self._data.get(domain)

    def update_domain(self, domain, data):
        self._data[domain] = data


class MockKernel:
    def __init__(self):
        self.state_manager = MockStateManager()
        self.model_config = {}
        self.event_bus = MagicMock()


# Create mock kernel
mock_kernel = MockKernel()

# Load the plugin module directly
spec = importlib.util.spec_from_file_location("world_main", MAIN_PATH)
world_main = importlib.util.module_from_spec(spec)
sys.modules["world_main"] = world_main
spec.loader.exec_module(world_main)


# =============================================================================
# TESTS
# =============================================================================

def test_weather_simulator_generates_valid_data():
    """Test that weather simulator generates valid weather data."""
    from world_main import WorldState, WeatherSimulator, WorldPlugin

    state = WorldState(mock_kernel.state_manager)
    sim = WeatherSimulator(state, {})

    weather = sim.simulate_weather()

    # Verify required fields exist
    assert "temperature" in weather
    assert "condition" in weather
    assert "humidity" in weather
    assert "wind_speed" in weather
    assert "pressure" in weather
    assert "visibility" in weather
    assert "uv_index" in weather
    assert "feels_like" in weather

    # Verify value ranges
    assert -20 <= weather["temperature"] <= 50, f"Temperature out of range: {weather['temperature']}"
    assert 0 <= weather["humidity"] <= 100, f"Humidity out of range: {weather['humidity']}"
    assert weather["condition"] in WeatherSimulator.CONDITIONS, f"Invalid condition: {weather['condition']}"

    # Update world_state to verify persistence
    mock_kernel.state_manager.update_domain("world_state", state.get())

    print("[PASS] Weather simulator generates valid data")


def test_weather_condition_transition():
    """Test that weather conditions transition realistically."""
    from world_main import WorldState, WeatherSimulator

    state = WorldState(mock_kernel.state_manager)
    sim = WeatherSimulator(state, {})

    # Start with clear weather
    state._state["weather"]["condition"] = "clear"

    # Simulate multiple times
    conditions = set()
    for _ in range(10):
        weather = sim.simulate_weather()
        conditions.add(weather["condition"])

    # Should have valid conditions
    for c in conditions:
        assert c in WeatherSimulator.CONDITIONS

    # Verify world_state was updated
    current_state = mock_kernel.state_manager.get_domain("world_state")
    assert current_state is not None

    print("[PASS] Weather condition transitions work")


def test_lighting_engine_calculates_sun_times():
    """Test that lighting engine calculates sunrise/sunset correctly."""
    from world_main import WorldState, LightingEngine

    state = WorldState(mock_kernel.state_manager)
    engine = LightingEngine(state)

    lighting = engine.calculate_lighting()

    # Verify required fields
    assert "sunrise" in lighting
    assert "sunset" in lighting
    assert "is_daytime" in lighting
    assert "moon_phase" in lighting
    assert "golden_hour_morning" in lighting
    assert "golden_hour_evening" in lighting
    assert "moon_illumination" in lighting

    # Verify time format (HH:MM)
    assert ":" in lighting["sunrise"]
    assert ":" in lighting["sunset"]

    # Update lighting in world_state
    state.update_lighting(lighting)
    updated_state = mock_kernel.state_manager.get_domain("world_state")
    assert updated_state["lighting"]["sunrise"] == lighting["sunrise"]

    print("[PASS] Lighting engine calculates sun times")


def test_lighting_moon_phase_calculation():
    """Test moon phase calculation."""
    from world_main import WorldState, LightingEngine

    state = WorldState(mock_kernel.state_manager)
    engine = LightingEngine(state)

    now = datetime.now()
    phase, illumination = engine._calculate_moon(now)

    valid_phases = ["new_moon", "waxing_crescent", "first_quarter", "waxing_gibbous",
                    "full_moon", "waning_gibbous", "last_quarter", "waning_crescent"]

    assert phase in valid_phases, f"Invalid moon phase: {phase}"
    assert 0 <= illumination <= 100, f"Illumination out of range: {illumination}"

    # Verify moon data is stored in world_state
    state._state["lighting"]["moon_phase"] = phase
    state._state["lighting"]["moon_illumination"] = illumination
    state._save_to_manager()
    current = mock_kernel.state_manager.get_domain("world_state")
    assert current["lighting"]["moon_phase"] == phase

    print("[PASS] Moon phase calculation works")


def test_world_state_updates():
    """Test that WorldState properly updates weather data."""
    from world_main import WorldState

    state = WorldState(mock_kernel.state_manager)

    # Update weather
    new_weather = {
        "temperature": 25.0,
        "condition": "clear"
    }
    state.update_weather(new_weather)

    # Verify update in state object
    current = state.get()
    assert current["weather"]["temperature"] == 25.0
    assert current["weather"]["condition"] == "clear"
    assert "last_updated" in current["weather"]

    # Verify persistence in state_manager (world_state updated correctly)
    persisted = mock_kernel.state_manager.get_domain("world_state")
    assert persisted["weather"]["temperature"] == 25.0
    assert persisted["weather"]["condition"] == "clear"

    print("[PASS] World state updates work correctly")


def test_world_plugin_initialization():
    """Test that WorldPlugin initializes correctly with kernel."""
    from world_main import WorldPlugin

    # Create fresh mock kernel with complete state
    test_kernel = MockKernel()

    plugin = WorldPlugin()

    # Initialize with mock kernel directly
    plugin.initialize(test_kernel)

    # Verify plugin is initialized
    assert plugin.world_state is not None, "WorldState not initialized"
    assert plugin.weather_sim is not None, "WeatherSimulator not initialized"
    assert plugin.lighting_engine is not None, "LightingEngine not initialized"
    assert plugin.atmosphere_engine is not None, "AtmosphereEngine not initialized"

    # Verify world_state was persisted to state_manager
    persisted = test_kernel.state_manager.get_domain("world_state")
    assert persisted is not None, "world_state not persisted"
    assert "weather" in persisted, "weather not in world_state"
    assert "lighting" in persisted, "lighting not in world_state"

    print("[PASS] WorldPlugin initializes correctly")


def test_world_plugin_tick_event():
    """Test that WorldPlugin responds to tick events."""
    from world_main import WorldPlugin, initialize

    # Create fresh mock kernel
    test_kernel = MockKernel()
    plugin = WorldPlugin()
    plugin.initialize(test_kernel)

    # Get initial state
    initial_weather = plugin.world_state.get()["weather"]

    # Fire TICK_HOURLY event
    event = {"event": "TICK_HOURLY"}
    plugin.on_event(event)

    # Verify state was updated
    updated_weather = plugin.world_state.get()["weather"]

    # Weather should have been updated (may be same or different due to simulation)
    assert "temperature" in updated_weather
    assert "condition" in updated_weather

    # Verify state persisted to state_manager
    persisted = test_kernel.state_manager.get_domain("world_state")
    assert persisted["weather"]["last_updated"] is not None

    print("[PASS] WorldPlugin handles tick events correctly")


def test_season_detection():
    """Test season detection based on current month."""
    from world_main import WeatherSimulator

    # Create a mock state
    mock_state = MagicMock()
    mock_state.get.return_value = {"weather": {"temperature": 15.0}}

    sim = WeatherSimulator(mock_state, {})

    # Test get_current_season returns valid season
    season = sim.get_current_season()
    valid_seasons = ["winter", "spring", "summer", "autumn"]
    assert season in valid_seasons, f"Invalid season: {season}"

    print("[PASS] Season detection works")


def test_atmosphere_engine():
    """Test atmosphere calculation based on weather."""
    from world_main import WorldState, AtmosphereEngine

    state = WorldState(mock_kernel.state_manager)
    engine = AtmosphereEngine(state)

    # Set rainy weather
    state._state["weather"]["condition"] = "rain"

    atmosphere = engine.calculate_atmosphere()

    # Verify required fields
    assert "fog_density" in atmosphere
    assert "cloud_cover" in atmosphere
    assert "precipitation_chance" in atmosphere
    assert "air_quality_index" in atmosphere

    # Rain should have high precipitation chance
    assert atmosphere["precipitation_chance"] >= 70

    print("[PASS] Atmosphere engine works")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all World plugin tests."""
    print("=" * 60)
    print("WORLD PLUGIN - WEATHER & LIGHTING TESTS")
    print("=" * 60)

    tests = [
        test_weather_simulator_generates_valid_data,
        test_weather_condition_transition,
        test_lighting_engine_calculates_sun_times,
        test_lighting_moon_phase_calculation,
        test_world_state_updates,
        test_season_detection,
        test_atmosphere_engine,
        test_world_plugin_initialization,
        test_world_plugin_tick_event,
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
        print("\n[SUCCESS] All World plugin tests passed!")
        print("[WORLD TEST] PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
