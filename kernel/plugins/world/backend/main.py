"""
World Engine Plugin - Atmospheric & Environmental Simulation (v7.0 Stable)
Refactored for 1:1 Legacy Compliance & v7.0 Architecture (Zero Direct I/O)
"""

import json
import random
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[WORLD] %(message)s')
logger = logging.getLogger("world")

# =============================================================================
# WORLD LOGIC (Refactored for State Manager)
# =============================================================================

class WorldPlugin:
    def __init__(self):
        self.kernel = None

    def initialize(self, kernel):
        self.kernel = kernel
        # Ensure initial state for world exists
        if not self.kernel.state_manager.get_domain("world_state"):
            self.kernel.state_manager.update_domain("world_state", {
                "season": "spring",
                "weather": "sunny",
                "temperature": 18,
                "lighting": "daylight",
                "last_update": datetime.now().isoformat()
            })
        logger.info("World Engine initialized (v7.0)")

    def on_event(self, event):
        if event.get("event") == "TICK_HOURLY":
            self._sync_with_real_world()

    def _sync_with_real_world(self):
        """1:1 Legacy Port of syncWorldWithRealWorld."""
        month = datetime.now().month
        if 3 <= month <= 5: season = "spring"
        elif 6 <= month <= 8: season = "summer"
        elif 9 <= month <= 11: season = "autumn"
        else: season = "winter"

        # Estimated Weather
        rand = random.random()
        if season == "summer":
            weather, temp = (("sunny", 25 + int(rand * 10)) if rand > 0.3 else ("cloudy", 20))
        elif season == "winter":
            weather, temp = (("snowy", -2 - int(rand * 5)) if rand > 0.5 else ("cloudy", 2))
        elif season == "autumn":
            weather, temp = (("rainy", 10) if rand > 0.4 else ("stormy", 8))
        else:
            weather, temp = ("sunny", 18)

        # Lighting based on hour
        hour = datetime.now().hour
        if 6 <= hour < 18: lighting = "daylight"
        elif 18 <= hour < 22: lighting = "sunset"
        elif 22 <= hour or hour < 6: lighting = "night"
        else: lighting = "daylight"

        new_state = {
            "season": season,
            "weather": weather,
            "temperature": temp,
            "lighting": lighting,
            "last_update": datetime.now().isoformat()
        }
        
        self.kernel.state_manager.update_domain("world_state", new_state)
        logger.info(f"World sync: {season}, {weather}, {temp}°C, {lighting}")
        self._fire_event("EVENT_WEATHER_UPDATE", new_state)

    def _fire_event(self, event_type, data):
        if self.kernel and self.kernel.event_bus:
            asyncio.run_coroutine_threadsafe(
                self.kernel.event_bus.publish(event_type, "plugin.world", data),
                self.kernel.event_loop
            )

    # -------------------------------------------------------------------------
    # API HANDLERS
    # -------------------------------------------------------------------------

    def handle_get_state(self, data=None):
        return self.kernel.state_manager.get_domain("world_state") or {}

    def handle_get_weather(self, data=None):
        state = self.handle_get_state()
        return {"weather": state.get("weather"), "temp": state.get("temperature")}

    def handle_get_lighting(self, data=None):
        state = self.handle_get_state()
        return {"lighting": state.get("lighting")}

    def handle_set_location(self, data: Dict[str, Any]):
        """Special handling for location changes (Spatial sync)."""
        loc = data.get("location", "home")
        # In v7.0, we update the physique/spatial domain
        physique = self.kernel.state_manager.get_domain("physique") or {}
        physique["current_location"] = loc
        self.kernel.state_manager.update_domain("physique", physique)
        return {"success": True, "location": loc}

# Singleton instance
plugin = WorldPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_get_state(data=None): return plugin.handle_get_state(data)
def handle_get_weather(data=None): return plugin.handle_get_weather(data)
def handle_get_lighting(data=None): return plugin.handle_get_lighting(data)
def handle_set_location(data): return plugin.handle_set_location(data)
