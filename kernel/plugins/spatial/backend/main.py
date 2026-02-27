"""
Spatial Plugin - Interior, Inventory & Wardrobe Management
Handles spatial awareness, object interactions, and clothing system.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[SPATIAL] %(message)s')
logger = logging.getLogger("spatial")

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================

DEFAULT_INTERIOR = {
    "rooms": [],
    "current_room": None,
    "entity_position": {"x": 0, "y": 0, "z": 0},
    "entity_rotation": {"x": 0, "y": 0, "z": 0, "w": 1},
    "last_updated": None
}

DEFAULT_INVENTORY = {
    "items": [],
    "held_item": None,
    "categories": ["electronics", "books", "consumables", "hobby", "tools", "media", "other"],
    "last_updated": None
}

DEFAULT_WARDROBE = {
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

# =============================================================================
# PLUGIN CLASS
# =============================================================================

class SpatialPlugin:
    def __init__(self):
        self.kernel = None

    def initialize(self, kernel):
        """Initialize plugin and connect to kernel."""
        self.kernel = kernel
        self._ensure_domains_exist()
        logger.info("SpatialPlugin initialized and connected to Kernel")

    def _ensure_domains_exist(self):
        """Ensure all spatial domains exist in state manager."""
        if not self.kernel.state_manager.get_domain("interior"):
            self.kernel.state_manager.update_domain("interior", DEFAULT_INTERIOR.copy())

        if not self.kernel.state_manager.get_domain("inventory"):
            self.kernel.state_manager.update_domain("inventory", DEFAULT_INVENTORY.copy())

        if not self.kernel.state_manager.get_domain("wardrobe"):
            self.kernel.state_manager.update_domain("wardrobe", DEFAULT_WARDROBE.copy())

    def on_event(self, event):
        """Handle incoming events."""
        event_type = event.get("event", "")

        if event_type == "ENTITY_MOVE":
            self._handle_entity_move(event)
        elif event_type == "ENTITY_DRESS":
            self._handle_entity_dress(event)
        elif event_type == "TICK_MINUTELY":
            self._on_tick_minutely(event)

    def _handle_entity_move(self, event: Dict[str, Any]):
        """Handle entity movement to new room/furniture."""
        interior = self.kernel.state_manager.get_domain("interior")
        if not interior:
            return

        target_room = event.get("room_id")
        target_furniture = event.get("furniture_id")
        position = event.get("position")
        rotation = event.get("rotation")

        if target_room:
            # Verify room exists
            rooms = interior.get("rooms", [])
            room_exists = any(r.get("id") == target_room for r in rooms)

            if room_exists:
                interior["current_room"] = target_room
                logger.info(f"Entity moved to room: {target_room}")
            else:
                logger.warning(f"Room not found: {target_room}")
                return

        if target_furniture and position:
            # Verify furniture exists in current room
            rooms = interior.get("rooms", [])
            current_room = interior.get("current_room")

            for room in rooms:
                if room.get("id") == current_room:
                    furniture = room.get("furniture", [])
                    furniture_exists = any(f.get("id") == target_furniture for f in furniture)

                    if furniture_exists:
                        interior["entity_position"] = position
                        if rotation:
                            interior["entity_rotation"] = rotation
                        logger.info(f"Entity positioned at furniture: {target_furniture}")
                        break

        interior["last_updated"] = datetime.now().isoformat()
        self.kernel.state_manager.update_domain("interior", interior)

    def _handle_entity_dress(self, event: Dict[str, Any]):
        """Handle entity clothing changes."""
        wardrobe = self.kernel.state_manager.get_domain("wardrobe")
        if not wardrobe:
            return

        action = event.get("action", "wear")
        category = event.get("category")
        item_id = event.get("item_id")
        outfit_name = event.get("outfit_name")

        if action == "wear" and category and item_id:
            self._wear_item(wardrobe, category, item_id)
        elif action == "remove" and category:
            self._remove_item(wardrobe, category, item_id)
        elif action == "change_outfit" and outfit_name:
            self._change_outfit(wardrobe, outfit_name)

        wardrobe["last_updated"] = datetime.now().isoformat()
        self.kernel.state_manager.update_domain("wardrobe", wardrobe)

    def _wear_item(self, wardrobe: Dict, category: str, item_id: str):
        """Wear an item from wardrobe inventory."""
        category_items = wardrobe.get("inventory", {}).get(category, [])

        # Find item
        item = None
        for i in category_items:
            if i.get("id") == item_id:
                item = i
                break

        if not item:
            logger.warning(f"Item not found in wardrobe: {item_id} in {category}")
            return

        # Update worn items
        worn = wardrobe.get("worn_items", {})
        worn[category] = item
        wardrobe["worn_items"] = worn

        logger.info(f"Wearing item: {item.get('name')} ({category})")

    def _remove_item(self, wardrobe: Dict, category: str, item_id: Optional[str] = None):
        """Remove an item from current outfit."""
        worn = wardrobe.get("worn_items", {})

        if item_id:
            # Remove specific item
            if category in worn and worn[category].get("id") == item_id:
                del worn[category]
                logger.info(f"Removed item: {item_id} from {category}")
        elif category in worn:
            # Remove entire category
            removed = worn.pop(category)
            logger.info(f"Removed {removed.get('name')} from {category}")

        wardrobe["worn_items"] = worn

    def _change_outfit(self, wardrobe: Dict, outfit_name: str):
        """Apply a saved outfit."""
        outfits = wardrobe.get("outfits", {})

        if outfit_name not in outfits:
            logger.warning(f"Outfit not found: {outfit_name}")
            return

        outfit_items = outfits[outfit_name]
        worn = {}

        # Apply each item from outfit
        wardrobe_inventory = wardrobe.get("inventory", {})

        for category, item_name in outfit_items.items():
            category_items = wardrobe_inventory.get(category, [])
            for item in category_items:
                if item.get("name") == item_name:
                    worn[category] = item
                    break

        wardrobe["worn_items"] = worn
        wardrobe["current_outfit"] = outfit_name

        logger.info(f"Changed outfit to: {outfit_name}")

    def _on_tick_minutely(self, event: Dict[str, Any]):
        """Handle minute tick events."""
        # Could implement furniture interaction timers, etc.
        pass

    # =========================================================================
    # API HANDLERS
    # =========================================================================

    def handle_get_interior(self) -> Dict[str, Any]:
        """Get current interior state."""
        interior = self.kernel.state_manager.get_domain("interior")
        return interior or DEFAULT_INTERIOR.copy()

    def handle_get_inventory(self) -> Dict[str, Any]:
        """Get current inventory state."""
        inventory = self.kernel.state_manager.get_domain("inventory")
        return inventory or DEFAULT_INVENTORY.copy()

    def handle_get_wardrobe(self) -> Dict[str, Any]:
        """Get current wardrobe state."""
        wardrobe = self.kernel.state_manager.get_domain("wardrobe")
        return wardrobe or DEFAULT_WARDROBE.copy()

    def handle_update_component(self, component: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic handler for updating spatial components."""
        valid_components = ["interior", "inventory", "wardrobe"]

        if component not in valid_components:
            return {"success": False, "error": f"Invalid component: {component}"}

        try:
            current = self.kernel.state_manager.get_domain(component)
            if current:
                current.update(data)
                current["last_updated"] = datetime.now().isoformat()
                self.kernel.state_manager.update_domain(component, current)
                return {"success": True, "component": component}
            else:
                return {"success": False, "error": f"Domain not found: {component}"}
        except Exception as e:
            logger.error(f"Error updating component {component}: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # INVENTORY MANAGEMENT
    # =========================================================================

    def add_inventory_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Add item to inventory."""
        inventory = self.kernel.state_manager.get_domain("inventory")
        if not inventory:
            inventory = DEFAULT_INVENTORY.copy()

        items = inventory.get("items", [])

        # Generate ID if not provided
        if "id" not in item:
            item["id"] = f"item_{uuid.uuid4().hex[:8]}"

        items.append(item)
        inventory["items"] = items
        inventory["last_updated"] = datetime.now().isoformat()

        self.kernel.state_manager.update_domain("inventory", inventory)

        logger.info(f"Added item to inventory: {item.get('name')}")
        return {"success": True, "item_id": item.get("id")}

    def remove_inventory_item(self, item_id: str) -> Dict[str, Any]:
        """Remove item from inventory."""
        inventory = self.kernel.state_manager.get_domain("inventory")
        if not inventory:
            return {"success": False, "error": "Inventory not found"}

        items = inventory.get("items", [])
        original_count = len(items)

        items = [i for i in items if i.get("id") != item_id]

        if len(items) == original_count:
            return {"success": False, "error": f"Item not found: {item_id}"}

        inventory["items"] = items
        inventory["last_updated"] = datetime.now().isoformat()

        # Clear held item if it was the removed one
        if inventory.get("held_item") == item_id:
            inventory["held_item"] = None

        self.kernel.state_manager.update_domain("inventory", inventory)

        logger.info(f"Removed item from inventory: {item_id}")
        return {"success": True}

    def hold_item(self, item_id: str) -> Dict[str, Any]:
        """Set item as currently held."""
        inventory = self.kernel.state_manager.get_domain("inventory")
        if not inventory:
            return {"success": False, "error": "Inventory not found"}

        items = inventory.get("items", [])
        item_exists = any(i.get("id") == item_id for i in items)

        if not item_exists:
            return {"success": False, "error": f"Item not found: {item_id}"}

        inventory["held_item"] = item_id
        inventory["last_updated"] = datetime.now().isoformat()

        self.kernel.state_manager.update_domain("inventory", inventory)

        logger.info(f"Holding item: {item_id}")
        return {"success": True}

    # =========================================================================
    # WARDROBE MANAGEMENT
    # =========================================================================

    def add_wardrobe_item(self, category: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Add item to wardrobe category."""
        wardrobe = self.kernel.state_manager.get_domain("wardrobe")
        if not wardrobe:
            wardrobe = DEFAULT_WARDROBE.copy()

        inventory = wardrobe.get("inventory", {})

        if category not in inventory:
            return {"success": False, "error": f"Invalid category: {category}"}

        # Generate ID if not provided
        if "id" not in item:
            item["id"] = f"{category}_{uuid.uuid4().hex[:8]}"

        inventory[category].append(item)
        wardrobe["inventory"] = inventory
        wardrobe["last_updated"] = datetime.now().isoformat()

        self.kernel.state_manager.update_domain("wardrobe", wardrobe)

        logger.info(f"Added item to wardrobe: {item.get('name')} ({category})")
        return {"success": True, "item_id": item.get("id")}

    def remove_wardrobe_item(self, category: str, item_id: str) -> Dict[str, Any]:
        """Remove item from wardrobe category."""
        wardrobe = self.kernel.state_manager.get_domain("wardrobe")
        if not wardrobe:
            return {"success": False, "error": "Wardrobe not found"}

        inventory = wardrobe.get("inventory", {})

        if category not in inventory:
            return {"success": False, "error": f"Invalid category: {category}"}

        items = inventory[category]
        original_count = len(items)

        items = [i for i in items if i.get("id") != item_id]

        if len(items) == original_count:
            return {"success": False, "error": f"Item not found: {item_id}"}

        inventory[category] = items
        wardrobe["inventory"] = inventory
        wardrobe["last_updated"] = datetime.now().isoformat()

        # Remove from worn items if currently worn
        worn = wardrobe.get("worn_items", {})
        if category in worn and worn[category].get("id") == item_id:
            del worn[category]
            wardrobe["worn_items"] = worn

        self.kernel.state_manager.update_domain("wardrobe", wardrobe)

        logger.info(f"Removed item from wardrobe: {item_id} ({category})")
        return {"success": True}

    def save_outfit(self, name: str, item_names: Dict[str, str]) -> Dict[str, Any]:
        """Save current outfit configuration."""
        wardrobe = self.kernel.state_manager.get_domain("wardrobe")
        if not wardrobe:
            return {"success": False, "error": "Wardrobe not found"}

        outfits = wardrobe.get("outfits", {})
        outfits[name] = item_names
        wardrobe["outfits"] = outfits

        logger.info(f"Saved outfit: {name}")
        return {"success": True}

    def delete_outfit(self, name: str) -> Dict[str, Any]:
        """Delete a saved outfit."""
        wardrobe = self.kernel.state_manager.get_domain("wardrobe")
        if not wardrobe:
            return {"success": False, "error": "Wardrobe not found"}

        outfits = wardrobe.get("outfits", {})

        if name not in outfits:
            return {"success": False, "error": f"Outfit not found: {name}"}

        del outfits[name]
        wardrobe["outfits"] = outfits

        # Clear current outfit if it was deleted
        if wardrobe.get("current_outfit") == name:
            wardrobe["current_outfit"] = None

        self.kernel.state_manager.update_domain("wardrobe", wardrobe)

        logger.info(f"Deleted outfit: {name}")
        return {"success": True}


# =============================================================================
# GLOBAL EXPORTS
# =============================================================================

# Global instance for the loader
plugin = SpatialPlugin()


def initialize(kernel):
    """Initialize the plugin with kernel reference."""
    plugin.initialize(kernel)


def on_event(event):
    """Handle incoming events."""
    plugin.on_event(event)


def handle_get_interior():
    """API: Get interior state."""
    return plugin.handle_get_interior()


def handle_get_inventory():
    """API: Get inventory state."""
    return plugin.handle_get_inventory()


def handle_get_wardrobe():
    """API: Get wardrobe state."""
    return plugin.handle_get_wardrobe()


def handle_update_component(component: str, data: Dict[str, Any]):
    """API: Update spatial component."""
    return plugin.handle_update_component(component, data)
