"""
Spatial Engine Plugin - Interior, Items & Locations (v7.0 Stable)
Refactored for 1:1 Legacy Compliance & v7.0 Architecture
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[SPATIAL] %(message)s')
logger = logging.getLogger("spatial")

# =============================================================================
# SPATIAL LOGIC
# =============================================================================

class SpatialPlugin:
    def __init__(self):
        self.kernel = None

    def initialize(self, kernel):
        self.kernel = kernel
        
        # Initial State: Interior
        if not self.kernel.state_manager.get_domain("interior"):
            self.kernel.state_manager.update_domain("interior", {
                "rooms": [
                    {"id": "home_office", "name": "Home Office", "items": ["PC", "Desk", "Chair"]},
                    {"id": "living_room", "name": "Living Room", "items": ["Sofa", "TV", "Bookshelf"]},
                    {"id": "bedroom", "name": "Bedroom", "items": ["Bed", "Wardrobe"]}
                ]
            })
            
        # Initial State: Wardrobe
        if not self.kernel.state_manager.get_domain("wardrobe"):
            self.kernel.state_manager.update_domain("wardrobe", {
                "outfits": [
                    {"id": "casual", "name": "Casual Comfort", "parts": ["T-Shirt", "Jeans"]},
                    {"id": "professional", "name": "Neural Tech", "parts": ["Suit", "Glasses"]}
                ],
                "current_outfit": "casual"
            })
            
        logger.info("Spatial Engine initialized (v7.0)")

    def on_event(self, event):
        pass

    def handle_get_interior(self, data=None):
        return self.kernel.state_manager.get_domain("interior") or {}

    def handle_get_inventory(self, data=None):
        return self.kernel.state_manager.get_domain("inventory") or {"items": []}

    def handle_get_wardrobe(self, data=None):
        return self.kernel.state_manager.get_domain("wardrobe") or {}

    def handle_update_component(self, data: Dict[str, Any]):
        component = data.get("component")
        value = data.get("value")
        if not component: return {"success": False, "error": "No component"}
        
        self.kernel.state_manager.update_domain(component, value)
        return {"success": True}

# Singleton instance
plugin = SpatialPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_get_interior(data=None): return plugin.handle_get_interior(data)
def handle_get_inventory(data=None): return plugin.handle_get_inventory(data)
def handle_get_wardrobe(data=None): return plugin.handle_get_wardrobe(data)
def handle_update_component(data): return plugin.handle_update_component(data)
