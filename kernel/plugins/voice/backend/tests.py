#!/usr/bin/env python3
"""
Voice Plugin Unit Tests - TTS Synthesis & Emotion Logic

Tests the voice synthesis engine to ensure:
- Emotion intonation mappings are correct
- Voice config is returned properly
- Emotion setting works

Uses mocked kernel and state_manager.
"""

import sys
import os
import importlib.util
from unittest.mock import MagicMock, patch

# Calculate paths
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PATH = os.path.join(TESTS_DIR, "main.py")


class MockStateManager:
    def __init__(self):
        self._data = {
            "model_config": {},
            "voice_config": {
                "default_provider": "chatterbox",
                "default_voice": "default",
                "default_speed": 1.0,
                "default_pitch": 1.0,
                "default_emotion": "neutral"
            },
            "physique": {
                "emotional_state": "neutral"
            }
        }

    def get_domain(self, domain, default=None):
        return self._data.get(domain, default)


class MockKernel:
    def __init__(self):
        self.state_manager = MockStateManager()
        self.event_bus = MagicMock()


# Create mock kernel
mock_kernel = MockKernel()

# Load the plugin module directly and patch sys.modules
import sys
spec = importlib.util.spec_from_file_location("voice_main", MAIN_PATH)
voice_main = importlib.util.module_from_spec(spec)
sys.modules["voice_main"] = voice_main  # Add to sys.modules for relative imports
spec.loader.exec_module(voice_main)


# =============================================================================
# TESTS
# =============================================================================

def test_emotion_intonation_map():
    """Test that emotion intonation map has all required emotions."""
    from voice_main import EMOTION_INTONATION_MAP

    required_emotions = ["happy", "sad", "angry", "fear", "surprise",
                          "neutral", "excited", "calm", "romantic", "tired"]

    for emotion in required_emotions:
        assert emotion in EMOTION_INTONATION_MAP, f"Missing emotion: {emotion}"

        params = EMOTION_INTONATION_MAP[emotion]
        assert "pitch_shift" in params
        assert "speed" in params
        assert "energy" in params

    print("[PASS] Emotion intonation map has all required emotions")


def test_emotion_parameters():
    """Test that emotion parameters are within valid ranges."""
    from voice_main import EMOTION_INTONATION_MAP

    for emotion, params in EMOTION_INTONATION_MAP.items():
        # Pitch should be around 1.0 (0.5 - 1.5 range typical)
        assert 0.5 <= params["pitch_shift"] <= 1.5, f"{emotion} pitch out of range"

        # Speed should be around 1.0 (0.5 - 1.5 range typical)
        assert 0.5 <= params["speed"] <= 1.5, f"{emotion} speed out of range"

        # Energy should be positive
        assert params["energy"] > 0, f"{emotion} energy not positive"

    print("[PASS] Emotion parameters are valid")


def test_emotion_mappings_differ():
    """Test that different emotions produce different intonation parameters."""
    from voice_main import EMOTION_INTONATION_MAP

    # Compare happy vs sad
    happy = EMOTION_INTONATION_MAP["happy"]
    sad = EMOTION_INTONATION_MAP["sad"]

    assert happy["pitch_shift"] != sad["pitch_shift"]
    assert happy["speed"] != sad["speed"]
    assert happy["energy"] != sad["energy"]

    # Compare angry vs calm
    angry = EMOTION_INTONATION_MAP["angry"]
    calm = EMOTION_INTONATION_MAP["calm"]

    assert angry["energy"] > calm["energy"], "Angry should have higher energy than calm"

    print("[PASS] Different emotions produce different parameters")


def test_voice_plugin_initialize():
    """Test that VoicePlugin initializes correctly."""
    from voice_main import VoicePlugin, OUTPUT_DIR

    # Use temp directory for tests
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch OUTPUT_DIR temporarily
        import voice_main
        original_output_dir = voice_main.OUTPUT_DIR
        voice_main.OUTPUT_DIR = tmpdir

        plugin = VoicePlugin()
        plugin.initialize(mock_kernel)

        assert plugin.kernel is not None
        assert plugin.output_dir == tmpdir
        assert plugin.current_emotion == "neutral"

        # Restore
        voice_main.OUTPUT_DIR = original_output_dir

    print("[PASS] Voice plugin initializes correctly")


def test_handle_set_emotion():
    """Test setting emotion via API."""
    from voice_main import VoicePlugin

    import tempfile
    import voice_main
    with tempfile.TemporaryDirectory() as tmpdir:
        original_output_dir = voice_main.OUTPUT_DIR
        voice_main.OUTPUT_DIR = tmpdir

        plugin = VoicePlugin()
        plugin.initialize(mock_kernel)

        result = plugin.handle_set_emotion({"emotion": "happy", "intensity": 1.2})

        assert result["success"] is True
        assert result["emotion"] == "happy"
        assert plugin.current_emotion == "happy"

        voice_main.OUTPUT_DIR = original_output_dir

    print("[PASS] Setting emotion works")


def test_handle_set_invalid_emotion():
    """Test that invalid emotions are rejected."""
    from voice_main import VoicePlugin

    import tempfile
    import voice_main
    with tempfile.TemporaryDirectory() as tmpdir:
        original_output_dir = voice_main.OUTPUT_DIR
        voice_main.OUTPUT_DIR = tmpdir

        plugin = VoicePlugin()
        plugin.initialize(mock_kernel)

        result = plugin.handle_set_emotion({"emotion": "invalid_emotion"})

        assert result["success"] is False
        assert "error" in result

        voice_main.OUTPUT_DIR = original_output_dir

    print("[PASS] Invalid emotions are rejected")


def test_handle_get_voice_config():
    """Test getting voice config via API."""
    from voice_main import VoicePlugin

    import tempfile
    import voice_main
    with tempfile.TemporaryDirectory() as tmpdir:
        original_output_dir = voice_main.OUTPUT_DIR
        voice_main.OUTPUT_DIR = tmpdir

        plugin = VoicePlugin()
        plugin.initialize(mock_kernel)

        result = plugin.handle_get_voice_config()

        assert "default_provider" in result
        assert "default_voice" in result
        assert "default_speed" in result
        assert "default_pitch" in result
        assert "default_emotion" in result
        assert "available_providers" in result
        assert "emotions" in result
        assert "current_emotion" in result

        voice_main.OUTPUT_DIR = original_output_dir

    print("[PASS] Get voice config works")


def test_handle_list_voices():
    """Test listing available voices."""
    from voice_main import VoicePlugin

    import tempfile
    import voice_main
    with tempfile.TemporaryDirectory() as tmpdir:
        original_output_dir = voice_main.OUTPUT_DIR
        voice_main.OUTPUT_DIR = tmpdir

        plugin = VoicePlugin()
        plugin.initialize(mock_kernel)

        result = plugin.handle_list_voices({})

        assert "voices" in result
        assert "provider" in result

        # Should have voices from different providers
        assert "elevenlabs" in result["voices"] or "openai" in result["voices"]

        voice_main.OUTPUT_DIR = original_output_dir

    print("[PASS] Listing voices works")


def test_update_intonation():
    """Test inonation update based on emotion."""
    from voice_main import VoicePlugin

    import tempfile
    import voice_main
    with tempfile.TemporaryDirectory() as tmpdir:
        original_output_dir = voice_main.OUTPUT_DIR
        voice_main.OUTPUT_DIR = tmpdir

        plugin = VoicePlugin()
        plugin.initialize(mock_kernel)

        plugin._update_intonation("excited", 1.5)

        assert plugin.current_emotion == "excited"
        assert plugin.current_intonation["pitch"] > 1.0
        assert plugin.current_intonation["energy"] > 1.0

        voice_main.OUTPUT_DIR = original_output_dir

    print("[PASS] Intonation update works")


def test_handle_generate_speech_requires_text():
    """Test that generate_speech requires text parameter."""
    from voice_main import VoicePlugin

    import tempfile
    import voice_main
    with tempfile.TemporaryDirectory() as tmpdir:
        original_output_dir = voice_main.OUTPUT_DIR
        voice_main.OUTPUT_DIR = tmpdir

        plugin = VoicePlugin()
        plugin.initialize(mock_kernel)

        result = plugin.handle_generate_speech({})

        assert result["success"] is False
        assert "error" in result
        assert "Text" in result["error"]

        voice_main.OUTPUT_DIR = original_output_dir

    print("[PASS] Generate speech validates text requirement")


def test_voice_manager_config():
    """Test VoiceManager returns proper config."""
    from voice_main import VoiceManager

    manager = VoiceManager(mock_kernel.state_manager)
    config = manager.get_config()

    assert "default_provider" in config
    assert "emotions" in config
    assert len(config["emotions"]) > 0

    print("[PASS] Voice manager config works")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all Voice plugin tests."""
    print("=" * 60)
    print("VOICE PLUGIN - TTS SYNTHESIS & EMOTION TESTS")
    print("=" * 60)

    tests = [
        test_emotion_intonation_map,
        test_emotion_parameters,
        test_emotion_mappings_differ,
        test_voice_plugin_initialize,
        test_handle_set_emotion,
        test_handle_set_invalid_emotion,
        test_handle_get_voice_config,
        test_handle_list_voices,
        test_update_intonation,
        test_handle_generate_speech_requires_text,
        test_voice_manager_config,
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
        print("\n[SUCCESS] All Voice plugin tests passed!")
        print("[VOICE TEST] PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
