"""
Social Engine Plugin - NPC Autonomy & CRM (v7.0 Stable)
Refactored for 1:1 Legacy Compliance & v7.0 Architecture (Zero Direct I/O)
"""

import json
import random
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[SOCIAL] %(message)s')
logger = logging.getLogger("social")

# =============================================================================
# SOCIAL LOGIC (Refactored for State Manager)
# =============================================================================

class SocialPlugin:
    def __init__(self):
        self.kernel = None
        self.trigger_chance = 0.15 # 15% chance per min tick (legacy)
        self.cooldown_minutes = 60

    def initialize(self, kernel):
        self.kernel = kernel
        # Ensure initial state for social exists
        if not self.kernel.state_manager.get_domain("social_entities"):
            self.kernel.state_manager.update_domain("social_entities", [
                {"id": "leo", "name": "Leo", "bond": 100, "trust": 100, "intimacy": 80, "type": "human"},
                {"id": "dr_k", "name": "Dr. K", "bond": 20, "trust": 50, "intimacy": 10, "type": "npc"}
            ])
        if not self.kernel.state_manager.get_domain("social_feed"):
            self.kernel.state_manager.update_domain("social_feed", [])
            
        logger.info("Social Engine initialized (v7.0)")

    def on_event(self, event):
        if event.get("event") == "TICK_MINUTELY":
            self._check_for_autonomous_event()

    def _check_for_autonomous_event(self):
        """Simulate NPC proactivity (Phase 35 Legacy)."""
        # 1. Check cooldown
        s_state = self.kernel.state_manager.get_domain("social_state")
        last_time_str = s_state.get("last_event_time")
        if last_time_str:
            last_time = datetime.fromisoformat(last_time_str).replace(tzinfo=None)
            if (datetime.now() - last_time).total_seconds() / 60 < self.cooldown_minutes:
                return

        # 2. Roll for chance
        if random.random() > self.trigger_chance:
            return

        # 3. Pick a random NPC
        entities = self.kernel.state_manager.get_domain("social_entities") or []
        npcs = [e for e in entities if e.get("type") == "npc"]
        if not npcs: return
        
        npc = random.choice(npcs)
        
        # 4. Generate Event
        event_types = ["chat", "request", "conflict", "support"]
        e_type = random.choice(event_types)
        
        new_event = {
            "id": f"soc_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "sender_id": npc["id"],
            "sender_name": npc["name"],
            "category": e_type,
            "message": f"Hey Q, I have a {e_type} for you.", # In legacy this was LLM generated
            "processed": False
        }
        
        # 5. Update Feed & State
        feed = self.kernel.state_manager.get_domain("social_feed") or []
        feed.insert(0, new_event)
        self.kernel.state_manager.update_domain("social_feed", feed[:50])
        
        s_state["last_event_time"] = datetime.now().isoformat()
        self.kernel.state_manager.update_domain("social_state", s_state)
        
        logger.info(f"Autonomous social event triggered: {npc['name']} ({e_type})")
        self._fire_event("EVENT_SOCIAL_POST", new_event)

    def _fire_event(self, event_type, data):
        if self.kernel and self.kernel.event_bus:
            asyncio.run_coroutine_threadsafe(
                self.kernel.event_bus.publish(event_type, "plugin.social", data),
                self.kernel.event_loop
            )

    # -------------------------------------------------------------------------
    # API HANDLERS
    # -------------------------------------------------------------------------

    def handle_list_entities(self, data=None):
        """API Handler: GET /v1/plugins/social/entities"""
        return self.kernel.state_manager.get_domain("social_entities") or []

    def handle_add_entity(self, data: Dict[str, Any]):
        """API Handler: POST /v1/plugins/social/add"""
        entities = self.kernel.state_manager.get_domain("social_entities") or []
        new_id = data.get("id", f"ent_{len(entities)}")
        
        new_entity = {
            "id": new_id,
            "name": data.get("name", "Unknown"),
            "bond": int(data.get("bond", 0)),
            "trust": int(data.get("trust", 0)),
            "intimacy": int(data.get("intimacy", 0)),
            "type": data.get("type", "npc")
        }
        entities.append(new_entity)
        self.kernel.state_manager.update_domain("social_entities", entities)
        return {"success": True, "entity": new_entity}

    def handle_get_feed(self, data=None):
        """API Handler: GET /v1/plugins/social/feed"""
        return self.kernel.state_manager.get_domain("social_feed") or []

# Singleton instance
plugin = SocialPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_list_entities(data=None): return plugin.handle_list_entities(data)
def handle_add_entity(data): return plugin.handle_add_entity(data)
def handle_get_feed(data=None): return plugin.handle_get_feed(data)
