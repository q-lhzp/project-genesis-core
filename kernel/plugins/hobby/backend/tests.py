#!/usr/bin/env python3
"""
Hobby Plugin Unit Tests - Interests & Research Logic

Tests the hobby engine to ensure:
- Research insights are generated correctly
- Interests can be added and removed
- Curiosity score updates properly

Uses mocked kernel and state_manager.
"""

import sys
import os
import importlib.util
from unittest.mock import MagicMock
from datetime import datetime

# Calculate paths
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PATH = os.path.join(TESTS_DIR, "main.py")


class MockStateManager:
    def __init__(self):
        self._data = {
            "interests": {
                "interests": [],
                "hobbies": [],
                "research_insights": [],
                "last_research_at": None,
                "curiosity_score": 50
            }
        }

    def get_domain(self, domain):
        return self._data.get(domain)

    def update_domain(self, domain, data):
        self._data[domain] = data


class MockKernel:
    def __init__(self):
        self.state_manager = MockStateManager()
        self.workspace = "/home/leo/Schreibtisch"
        self.publish_event = MagicMock()


# Create mock kernel
mock_kernel = MockKernel()

# Load the plugin module directly
spec = importlib.util.spec_from_file_location("hobby_main", MAIN_PATH)
hobby_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hobby_main)

# Import constants for testing
RESEARCH_TOPICS = hobby_main.RESEARCH_TOPICS
HobbyPlugin = hobby_main.HobbyPlugin


# =============================================================================
# TESTS
# =============================================================================

def test_research_insight_generation():
    """Test that research insights are generated correctly."""
    plugin = HobbyPlugin()
    plugin.kernel = mock_kernel

    # Generate insight
    plugin._generate_research_insight()

    # Get updated interests
    interests = mock_kernel.state_manager.get_domain("interests")

    # Verify insight was added
    assert len(interests["research_insights"]) > 0, "Research insight should be added"

    insight = interests["research_insights"][-1]

    # Verify insight structure
    assert "id" in insight
    assert "timestamp" in insight
    assert "topic" in insight
    assert "text" in insight
    assert "category" in insight

    # Verify ID format
    assert insight["id"].startswith("INS-")

    print("[PASS] Research insight generation works")


def test_add_interest():
    """Test adding a new interest."""
    plugin = HobbyPlugin()
    plugin.kernel = mock_kernel

    # Add interest
    result = plugin.handle_add_interest({
        "name": "Quantum Computing",
        "type": "interest",
        "category": "technology",
        "intensity": 7
    })

    assert result["status"] == "success"
    assert result.get("interest", {}).get("name") == "Quantum Computing"

    # Verify in state
    interests = mock_kernel.state_manager.get_domain("interests")
    names = [i["name"] for i in interests.get("interests", [])]
    assert "Quantum Computing" in names

    print("[PASS] Adding interest works")


def test_add_duplicate_interest_rejected():
    """Test that duplicate interests are rejected."""
    plugin = HobbyPlugin()
    plugin.kernel = mock_kernel

    # Add first interest
    plugin.handle_add_interest({
        "name": "Robotics",
        "type": "interest"
    })

    # Try to add duplicate
    result = plugin.handle_add_interest({
        "name": "Robotics",
        "type": "interest"
    })

    assert result["status"] == "error"
    assert "already exists" in result.get("message", "")

    print("[PASS] Duplicate interests are rejected")


def test_curiosity_score_update():
    """Test that curiosity score updates when adding interests."""
    plugin = HobbyPlugin()
    plugin.kernel = mock_kernel

    # Set initial score
    mock_kernel.state_manager._data["interests"]["curiosity_score"] = 50

    # Add interest
    plugin.handle_add_interest({
        "name": "AI Ethics",
        "type": "interest"
    })

    # Verify score increased
    interests = mock_kernel.state_manager.get_domain("interests")
    assert interests["curiosity_score"] > 50

    print("[PASS] Curiosity score updates correctly")


def test_remove_interest():
    """Test removing an interest."""
    plugin = HobbyPlugin()
    plugin.kernel = mock_kernel

    # Add interest first
    plugin.handle_add_interest({
        "name": "Biotechnology",
        "type": "interest"
    })

    # Remove it
    result = plugin.handle_remove_interest({
        "name": "Biotechnology",
        "type": "interest"
    })

    assert result["status"] == "success"

    # Verify removed
    interests = mock_kernel.state_manager.get_domain("interests")
    names = [i["name"] for i in interests.get("interests", [])]
    assert "Biotechnology" not in names

    print("[PASS] Removing interest works")


def test_research_topic_selection():
    """Test that research topics are selected from valid list."""
    # Verify topics exist
    assert len(RESEARCH_TOPICS) > 0

    # Verify they are strings
    for topic in RESEARCH_TOPICS:
        assert isinstance(topic, str)
        assert len(topic) > 0

    print("[PASS] Research topics are valid")


def test_handle_get_interests():
    """Test get interests API handler."""
    plugin = HobbyPlugin()
    plugin.kernel = mock_kernel

    result = plugin.handle_get_interests()

    assert result["status"] == "success"
    assert "interests" in result
    assert "hobbies" in result
    assert "research_insights" in result
    assert "curiosity_score" in result

    print("[PASS] Get interests API works")


def test_handle_trigger_insight():
    """Test manual insight trigger."""
    plugin = HobbyPlugin()
    plugin.kernel = mock_kernel

    result = plugin.handle_trigger_insight()

    assert result["status"] == "success"
    assert result.get("insight") is not None

    print("[PASS] Manual insight trigger works")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all Hobby plugin tests."""
    print("=" * 60)
    print("HOBBY PLUGIN - INTERESTS & RESEARCH TESTS")
    print("=" * 60)

    tests = [
        test_research_insight_generation,
        test_add_interest,
        test_add_duplicate_interest_rejected,
        test_curiosity_score_update,
        test_remove_interest,
        test_research_topic_selection,
        test_handle_get_interests,
        test_handle_trigger_insight,
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
        print("\n[SUCCESS] All Hobby plugin tests passed!")
        print("[HOBBY TEST] PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
