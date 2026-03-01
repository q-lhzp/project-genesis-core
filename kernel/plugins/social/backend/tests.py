#!/usr/bin/env python3
"""
Social Plugin Unit Tests - NPC CRM, Reputation & Feed Logic
Tests the social intelligence engine that drives social extroversion.
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
    """Mock state manager with social and presence_state domains."""
    def __init__(self):
        self._social = {
            "entities": []
        }
        self._presence_state = {
            "feed": []
        }

    def get_domain(self, domain):
        if domain == "social":
            return self._social
        elif domain == "presence_state":
            return self._presence_state
        return None

    def update_domain(self, domain, data):
        if domain == "social":
            self._social = data
        elif domain == "presence_state":
            self._presence_state = data


class MockKernel:
    """Mock kernel with state_manager."""
    def __init__(self):
        self.state_manager = MockStateManager()


# Create mock kernel
mock_kernel = MockKernel()

# Load the plugin module directly
spec = importlib.util.spec_from_file_location("social_main", MAIN_PATH)
social_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(social_main)

# Override the plugin's kernel reference
social_main.plugin.kernel = mock_kernel


def test_add_entity():
    """Test adding a new NPC entity to social CRM."""
    # Reset state
    mock_kernel.state_manager._social = {"entities": []}

    # Add entity
    result = social_main.plugin.handle_add_entity({
        "name": "Alice",
        "type": "friend",
        "relationship": 80
    })

    print(f"[TEST] Add entity result: {result}")

    assert result.get("success") == True, f"Add entity should succeed: {result}"
    assert "id" in result, "Result should contain entity id"

    # Check state
    social = mock_kernel.state_manager._social
    entities = social.get("entities", [])
    assert len(entities) == 1, f"Should have 1 entity, got {len(entities)}"
    assert entities[0].get("name") == "Alice", "Entity name should be Alice"

    print("[PASS] Add entity creates new NPC in CRM")


def test_add_multiple_entities():
    """Test adding multiple entities with unique IDs."""
    # Reset state
    mock_kernel.state_manager._social = {"entities": []}

    # Add multiple entities
    result1 = social_main.plugin.handle_add_entity({"name": "Bob", "type": "colleague"})
    result2 = social_main.plugin.handle_add_entity({"name": "Charlie", "type": "friend"})

    social = mock_kernel.state_manager._social
    entities = social.get("entities", [])

    assert len(entities) == 2, f"Should have 2 entities, got {len(entities)}"
    assert result1.get("id") != result2.get("id"), "Each entity should have unique ID"

    print("[PASS] Multiple entities get unique IDs")


def test_trade_social_impact():
    """Test that trade execution creates social post."""
    # Reset state
    mock_kernel.state_manager._presence_state = {"feed": []}

    initial_feed_count = len(mock_kernel.state_manager._presence_state.get("feed", []))

    # Simulate trade event
    event = {
        "event": "EVENT_TRADE_EXECUTED",
        "data": {"symbol": "BTC", "amount": 0.01, "type": "buy"}
    }

    social_main.plugin.on_event(event)

    # Check feed was updated
    presence = mock_kernel.state_manager._presence_state
    feed = presence.get("feed", [])

    assert len(feed) > initial_feed_count, "Feed should have new post"

    latest_post = feed[0]
    assert "BTC" in latest_post.get("content", ""), "Post should mention BTC"
    assert latest_post.get("impact") == "positive", "Trade post should be positive"

    print(f"[TEST] Trade post created: {latest_post.get('content')}")
    print("[PASS] Trade events create social posts")


def test_hourly_tick_simulates_activity():
    """Test that hourly tick triggers social simulation."""
    # Reset state
    mock_kernel.state_manager._presence_state = {"feed": []}

    # Simulate hourly tick
    event = {"event": "TICK_HOURLY"}

    # Should not raise exception
    try:
        social_main.plugin.on_event(event)
        print("[PASS] Hourly tick handled without errors")
    except Exception as e:
        print(f"[FAIL] Hourly tick raised error: {e}")
        raise


def test_list_entities():
    """Test listing all social entities."""
    # Set up state
    mock_kernel.state_manager._social = {
        "entities": [
            {"id": "npc_1", "name": "Alice", "type": "friend"},
            {"id": "npc_2", "name": "Bob", "type": "colleague"}
        ]
    }

    result = social_main.plugin.handle_list_entities()

    assert "entities" in result, "Result should contain entities"
    assert len(result["entities"]) == 2, f"Should have 2 entities: {result}"

    print("[PASS] List entities returns all NPCs")


def main():
    """Run all SOCIAL plugin tests."""
    print("=" * 60)
    print("SOCIAL PLUGIN - NPC CRM & FEED TESTS")
    print("=" * 60)

    tests = [
        test_add_entity,
        test_add_multiple_entities,
        test_trade_social_impact,
        test_hourly_tick_simulates_activity,
        test_list_entities,
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
        print("\n[SUCCESS] All SOCIAL CRM tests passed!")
        print("[SOCIAL TEST] PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
