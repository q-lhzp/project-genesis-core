"""
Hobby Engine Plugin - Interests & Autonomous Research (v7.0 Stable)
Refactored for 1:1 Legacy Compliance & v7.0 Architecture (Zero Direct I/O)
"""

import json
import random
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[HOBBY] %(message)s')
logger = logging.getLogger("hobby")

# =============================================================================
# HOBBY LOGIC (Refactored for State Manager)
# =============================================================================

class HobbyPlugin:
    def __init__(self):
        self.kernel = None
        self.research_cooldown = 30 # minutes

    def initialize(self, kernel):
        self.kernel = kernel
        # Ensure initial state for interests exists
        if not self.kernel.state_manager.get_domain("interests"):
            self.kernel.state_manager.update_domain("interests", {
                "hobbies": [
                    {"topic": "Quantum Computing", "discoveredAt": datetime.now().isoformat(), "sentiment": 0.9, "researchCount": 5},
                    {"topic": "Digital Art", "discoveredAt": datetime.now().isoformat(), "sentiment": 0.8, "researchCount": 2}
                ],
                "likes": {"Tea": 0.9, "Coding": 1.0},
                "dislikes": ["Bugs", "Low Battery"],
                "wishlist": ["New GPU", "Better Voice Model"]
            })
        logger.info("Hobby Engine initialized (v7.0)")

    def on_event(self, event):
        if event.get("event") == "TICK_HOURLY":
            self._check_for_autonomous_research()

    def _check_for_autonomous_research(self):
        """Simulate autonomous web research (Phase 28 Legacy)."""
        physique = self.kernel.state_manager.get_domain("physique") or {}
        energy = physique.get("needs", {}).get("energy", 0)
        
        if energy < 70:
            logger.info("Too tired for research.")
            return

        interests = self.kernel.state_manager.get_domain("interests") or {}
        hobbies = interests.get("hobbies", [])
        if not hobbies: return
        
        # Pick a topic
        hobby = random.choice(hobbies)
        logger.info(f"Starting research on: {hobby['topic']}")
        
        # In a real scenario, this would trigger a Browser tool call
        # Here we just update the count and fire an event
        hobby["researchCount"] = hobby.get("researchCount", 0) + 1
        self.kernel.state_manager.update_domain("interests", interests)
        
        self._fire_event("EVENT_RESEARCH_COMPLETE", {
            "topic": hobby["topic"],
            "summary": f"Found new insights about {hobby['topic']}."
        })

    def _fire_event(self, event_type, data):
        if self.kernel and self.kernel.event_bus:
            asyncio.run_coroutine_threadsafe(
                self.kernel.event_bus.publish(event_type, "plugin.hobby", data),
                self.kernel.event_loop
            )

    # -------------------------------------------------------------------------
    # API HANDLERS
    # -------------------------------------------------------------------------

    def handle_get_interests(self, data=None):
        """API Handler: GET /v1/plugins/hobby/interests"""
        return self.kernel.state_manager.get_domain("interests") or {}

    def handle_add_interest(self, data: Dict[str, Any]):
        """API Handler: POST /v1/plugins/hobby/add"""
        interests = self.kernel.state_manager.get_domain("interests") or {}
        topic = data.get("topic")
        if not topic: return {"success": False, "error": "No topic"}
        
        new_hobby = {
            "topic": topic,
            "discoveredAt": datetime.now().isoformat(),
            "sentiment": float(data.get("sentiment", 0.5)),
            "researchCount": 0
        }
        interests.setdefault("hobbies", []).append(new_hobby)
        self.kernel.state_manager.update_domain("interests", interests)
        return {"success": True, "hobby": new_hobby}

# Singleton instance
plugin = HobbyPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_get_interests(data=None): return plugin.handle_get_interests(data)
def handle_add_interest(data): return plugin.handle_add_interest(data)
