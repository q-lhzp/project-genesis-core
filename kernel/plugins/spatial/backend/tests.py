#!/usr/bin/env python3
"""
Spatial Plugin Unit Tests - Interior, Inventory & Wardrobe Logic

Tests the spatial engine to ensure:
- Inventory management works correctly
- Wardrobe items can be added and worn
- Outfits can be saved and applied

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

# Add tests directory to path for imports
sys.path.insert(0, TESTS_DIR)


class MockStateManager:
    def __init__(self):
        self._data = {
            "interior": {
                "rooms": [],
                "current_room": None,
                "entity_position": {"x": 0, "y": 0, "z": 0},
                "entity_rotation": {"x": 0, "y": 0, "z": 0, "w": 1},
                "last_updated": None
            },
            "inventory": {
                "items": [],
                "held_item": None,
                "categories": ["electronics", "books", "consumables", "hobby", "tools", "media", "other"],
                "last_updated": None
            },
            "wardrobe": {
                "inventory": {
                    "underwear": [],
                    "tops": [],
                    "bottoms": [],
                    "socks": [],
                    "shoes": [],
                    "accessories": [],
                    "jewelry": [],
                    "outerwear": [],
                    "objects": []
                },
                "outfits": {},
                "current_outfit": None,
                "worn_items": {},
                "last_updated": None
            }
        }

    def get_domain(self, domain):
        return self._data.get(domain)

    def update_domain(self, domain, data):
        self._data[domain] = data


class MockKernel:
    def __init__(self):
        self.state_manager = MockStateManager()
        self.publish_event = MagicMock()


# Create mock kernel
mock_kernel = MockKernel()


def reset_mock_kernel():
    """Reset the mock kernel state for fresh tests."""
    mock_kernel.state_manager._data = {
        "interior": {
            "rooms": [],
            "current_room": None,
            "entity_position": {"x": 0, "y": 0, "z": 0},
            "entity_rotation": {"x": 0, "y": 0, "z": 0, "w": 1},
            "last_updated": None
        },
        "inventory": {
            "items": [],
            "held_item": None,
            "categories": ["electronics", "books", "consumables", "hobby", "tools", "media", "other"],
            "last_updated": None
        },
        "wardrobe": {
            "inventory": {
                "underwear": [],
                "tops": [],
                "bottoms": [],
                "socks": [],
                "shoes": [],
                "accessories": [],
                "jewelry": [],
                "outerwear": [],
                "objects": []
            },
            "outfits": {},
            "current_outfit": None,
            "worn_items": {},
            "last_updated": None
        }
    }

# Load the plugin module directly
spec = importlib.util.spec_from_file_location("main", MAIN_PATH)
spatial_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spatial_main)

# Alias as main module for imports
sys.modules['main'] = spatial_main


# =============================================================================
# TESTS
# =============================================================================

def test_add_inventory_item():
    """Test adding an item to inventory."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    item = {
        "name": "Laptop",
        "category": "electronics",
        "description": "Work laptop"
    }

    result = plugin.add_inventory_item(item)

    assert result["success"] is True
    assert "item_id" in result

    # Verify in state
    inventory = mock_kernel.state_manager.get_domain("inventory")
    assert len(inventory["items"]) == 1
    assert inventory["items"][0]["name"] == "Laptop"

    print("[PASS] Adding inventory item works")


def test_remove_inventory_item():
    """Test removing an item from inventory."""
    reset_mock_kernel()
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Add item first
    item = {"name": "Phone", "category": "electronics"}
    result = plugin.add_inventory_item(item)
    item_id = result["item_id"]

    # Remove it
    result = plugin.remove_inventory_item(item_id)

    assert result["success"] is True

    # Verify removed
    inventory = mock_kernel.state_manager.get_domain("inventory")
    assert len(inventory["items"]) == 0

    print("[PASS] Removing inventory item works")


def test_hold_item():
    """Test setting an item as held."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Add item
    item = {"name": "Coffee Mug", "category": "consumables"}
    result = plugin.add_inventory_item(item)
    item_id = result["item_id"]

    # Hold it
    result = plugin.hold_item(item_id)

    assert result["success"] is True

    # Verify held
    inventory = mock_kernel.state_manager.get_domain("inventory")
    assert inventory["held_item"] == item_id

    print("[PASS] Holding item works")


def test_add_wardrobe_item():
    """Test adding an item to wardrobe."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    item = {
        "name": "Blue T-Shirt",
        "color": "blue",
        "brand": "Nike"
    }

    result = plugin.add_wardrobe_item("tops", item)

    assert result["success"] is True
    assert "item_id" in result

    # Verify in state
    wardrobe = mock_kernel.state_manager.get_domain("wardrobe")
    assert len(wardrobe["inventory"]["tops"]) == 1
    assert wardrobe["inventory"]["tops"][0]["name"] == "Blue T-Shirt"

    print("[PASS] Adding wardrobe item works")


def test_wear_item():
    """Test wearing an item from wardrobe."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Add item to wardrobe
    item = {"name": "Black Jeans", "color": "black"}
    result = plugin.add_wardrobe_item("bottoms", item)
    item_id = result["item_id"]

    # Get wardrobe
    wardrobe = mock_kernel.state_manager.get_domain("wardrobe")

    # Wear the item
    plugin._wear_item(wardrobe, "bottoms", item_id)

    assert "bottoms" in wardrobe["worn_items"]
    assert wardrobe["worn_items"]["bottoms"]["name"] == "Black Jeans"

    print("[PASS] Wearing item works")


def test_save_outfit():
    """Test saving an outfit."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Add items to wardrobe first
    plugin.add_wardrobe_item("tops", {"name": "White Shirt"})
    plugin.add_wardrobe_item("bottoms", {"name": "Slacks"})

    # Save outfit
    item_names = {
        "tops": "White Shirt",
        "bottoms": "Slacks"
    }

    result = plugin.save_outfit("Business", item_names)

    assert result["success"] is True

    # Verify saved
    wardrobe = mock_kernel.state_manager.get_domain("wardrobe")
    assert "Business" in wardrobe["outfits"]

    print("[PASS] Saving outfit works")


def test_change_outfit():
    """Test applying a saved outfit."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Add items
    plugin.add_wardrobe_item("tops", {"name": "Hoodie"})
    plugin.add_wardrobe_item("bottoms", {"name": "Jeans"})

    # Save outfit
    plugin.save_outfit("Casual", {"tops": "Hoodie", "bottoms": "Jeans"})

    # Get wardrobe
    wardrobe = mock_kernel.state_manager.get_domain("wardrobe")

    # Change outfit
    plugin._change_outfit(wardrobe, "Casual")

    assert wardrobe["current_outfit"] == "Casual"
    assert "tops" in wardrobe["worn_items"]
    assert wardrobe["worn_items"]["tops"]["name"] == "Hoodie"

    print("[PASS] Changing outfit works")


def test_remove_wardrobe_item():
    """Test removing item from wardrobe."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Add item
    item = {"name": "Sneakers"}
    result = plugin.add_wardrobe_item("shoes", item)
    item_id = result["item_id"]

    # Remove it
    result = plugin.remove_wardrobe_item("shoes", item_id)

    assert result["success"] is True

    # Verify removed
    wardrobe = mock_kernel.state_manager.get_domain("wardrobe")
    assert len(wardrobe["inventory"]["shoes"]) == 0

    print("[PASS] Removing wardrobe item works")


def test_delete_outfit():
    """Test deleting a saved outfit."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Save outfit
    plugin.save_outfit("Test Outfit", {"tops": "Shirt"})

    # Delete it
    result = plugin.delete_outfit("Test Outfit")

    assert result["success"] is True

    # Verify deleted
    wardrobe = mock_kernel.state_manager.get_domain("wardrobe")
    assert "Test Outfit" not in wardrobe["outfits"]

    print("[PASS] Deleting outfit works")


def test_entity_move_room():
    """Test entity movement to a new room (ENTITY_MOVE event)."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Set up rooms in interior
    interior = mock_kernel.state_manager.get_domain("interior")
    interior["rooms"] = [
        {"id": "living_room", "name": "Living Room", "furniture": []},
        {"id": "bedroom", "name": "Bedroom", "furniture": []}
    ]
    mock_kernel.state_manager.update_domain("interior", interior)

    # Send ENTITY_MOVE event
    event = {
        "event": "ENTITY_MOVE",
        "room_id": "bedroom"
    }

    plugin.on_event(event)

    # Verify room change
    interior = mock_kernel.state_manager.get_domain("interior")
    assert interior["current_room"] == "bedroom"

    print("[PASS] Entity move to room works")


def test_entity_move_with_furniture():
    """Test entity movement to furniture (ENTITY_MOVE event with position)."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Set up room with furniture
    interior = mock_kernel.state_manager.get_domain("interior")
    interior["rooms"] = [
        {"id": "bedroom", "name": "Bedroom", "furniture": [
            {"id": "bed_1", "name": "Bed", "position": {"x": 2, "y": 0, "z": 3}}
        ]}
    ]
    interior["current_room"] = "bedroom"
    mock_kernel.state_manager.update_domain("interior", interior)

    # Move to furniture
    event = {
        "event": "ENTITY_MOVE",
        "room_id": "bedroom",
        "furniture_id": "bed_1",
        "position": {"x": 2.5, "y": 0.5, "z": 3.2}
    }

    plugin.on_event(event)

    # Verify position update
    interior = mock_kernel.state_manager.get_domain("interior")
    assert interior["entity_position"]["x"] == 2.5
    assert interior["entity_position"]["y"] == 0.5
    assert interior["entity_position"]["z"] == 3.2

    print("[PASS] Entity move to furniture works")


def test_entity_dress_event():
    """Test ENTITY_DRESS event for wearing items."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Add item to wardrobe
    result = plugin.add_wardrobe_item("tops", {"name": "Red Shirt"})
    item_id = result["item_id"]

    # Send ENTITY_DRESS event
    event = {
        "event": "ENTITY_DRESS",
        "action": "wear",
        "category": "tops",
        "item_id": item_id
    }

    plugin.on_event(event)

    # Verify worn
    wardrobe = mock_kernel.state_manager.get_domain("wardrobe")
    assert "tops" in wardrobe["worn_items"]
    assert wardrobe["worn_items"]["tops"]["name"] == "Red Shirt"

    print("[PASS] Entity dress event works")


def test_domain_updates():
    """Test that interior, inventory, and wardrobe domains are properly updated."""
    reset_mock_kernel()
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    # Update interior domain
    interior = mock_kernel.state_manager.get_domain("interior")
    interior["current_room"] = "kitchen"
    mock_kernel.state_manager.update_domain("interior", interior)

    # Update inventory domain
    plugin.add_inventory_item({"name": "Test Item"})

    # Update wardrobe domain
    plugin.add_wardrobe_item("tops", {"name": "Test Shirt"})

    # Verify all domains exist and are updated
    interior = mock_kernel.state_manager.get_domain("interior")
    inventory = mock_kernel.state_manager.get_domain("inventory")
    wardrobe = mock_kernel.state_manager.get_domain("wardrobe")

    assert interior is not None
    assert "current_room" in interior
    assert interior["current_room"] == "kitchen"

    assert inventory is not None
    assert len(inventory["items"]) == 1

    assert wardrobe is not None
    assert len(wardrobe["inventory"]["tops"]) == 1

    print("[PASS] All domains (interior, inventory, wardrobe) updated correctly")


def test_handle_get_inventory():
    """Test get inventory API handler."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    result = plugin.handle_get_inventory()

    assert "items" in result
    assert "held_item" in result
    assert "categories" in result

    print("[PASS] Get inventory API works")


def test_handle_get_wardrobe():
    """Test get wardrobe API handler."""
    from main import SpatialPlugin

    plugin = SpatialPlugin()
    plugin.kernel = mock_kernel

    result = plugin.handle_get_wardrobe()

    assert "inventory" in result
    assert "outfits" in result
    assert "worn_items" in result

    print("[PASS] Get wardrobe API works")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all Spatial plugin tests."""
    print("=" * 60)
    print("SPATIAL PLUGIN - INVENTORY & WARDROBE TESTS")
    print("=" * 60)

    tests = [
        test_add_inventory_item,
        test_remove_inventory_item,
        test_hold_item,
        test_add_wardrobe_item,
        test_wear_item,
        test_save_outfit,
        test_change_outfit,
        test_remove_wardrobe_item,
        test_delete_outfit,
        test_handle_get_inventory,
        test_handle_get_wardrobe,
        test_entity_move_room,
        test_entity_move_with_furniture,
        test_entity_dress_event,
        test_domain_updates,
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
        print("\n[SUCCESS] All Spatial plugin tests passed!")
        print("[SPATIAL TEST] PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
