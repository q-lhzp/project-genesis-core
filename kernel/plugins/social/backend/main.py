"""
Social Intelligence Plugin - NPC CRM, Reputation & Feed
Reacts to internal events to drive social extroversion.
"""

import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='[SOCIAL] %(message)s')
logger = logging.getLogger("social")

class SocialPlugin:
    def __init__(self):
        self.kernel = None

    def initialize(self, kernel):
        self.kernel = kernel
        logger.info("Social Intelligence Engine initialized")

    def on_event(self, event):
        etype = event.get("event")
        # 1. Periodic Social Simulation
        if etype == "TICK_HOURLY":
            self._simulate_social_activity()
        
        # 2. React to Economic Success (Cross-Domain Event)
        elif etype == "EVENT_TRADE_EXECUTED":
            self._handle_trade_social_impact(event.get("data", {}))

    def _simulate_social_activity(self):
        logger.info("Simulating NPC interactions and reputation drift...")
        # Future: Complex NPC AI routines here

    def _handle_trade_social_impact(self, trade_data):
        """Create a social post when a trade happens."""
        symbol = trade_data.get("symbol", "assets")
        post = {
            "timestamp": datetime.now().isoformat(),
            "type": "status",
            "content": f"Just rebalanced my {symbol} portfolio. The market feels alive today. 📈",
            "impact": "positive"
        }
        self._add_to_feed(post)
        logger.info(f"Auto-posted trade update for {symbol}")

    def _add_to_feed(self, post):
        state = self.kernel.state_manager.get_domain("presence_state") or {"feed": []}
        if "feed" not in state: state["feed"] = []
        state["feed"].insert(0, post)
        self.kernel.state_manager.update_domain("presence_state", state)

    def handle_list_entities(self):
        return self.kernel.state_manager.get_domain("social")

    def handle_add_entity(self, data):
        social = self.kernel.state_manager.get_domain("social")
        if "entities" not in social: social["entities"] = []
        new_id = f"npc_{len(social['entities']) + 1}"
        data["id"] = new_id
        social["entities"].append(data)
        self.kernel.state_manager.update_domain("social", social)
        return {"success": True, "id": new_id}

    def handle_get_feed(self):
        return self.kernel.state_manager.get_domain("presence_state").get("feed", [])

# Global instance for loader
plugin = SocialPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_list_entities(): return plugin.handle_list_entities()
def handle_add_entity(data): return plugin.handle_add_entity(data)
def handle_get_feed(): return plugin.handle_get_feed()
