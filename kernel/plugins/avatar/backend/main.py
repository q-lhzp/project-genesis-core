"""
Avatar Plugin - Embodiment & Expression Engine
Translates biological needs into visual BlendShapes.
"""

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='[AVATAR] %(message)s')
logger = logging.getLogger("avatar")

class AvatarPlugin:
    def __init__(self):
        self.kernel = None

    def initialize(self, kernel):
        self.kernel = kernel
        logger.info("Embodiment Engine initialized")

    def on_event(self, event):
        """React to ticks or critical needs to update expressions."""
        if event.get("event") == "TICK_MINUTELY":
            self._update_expressions()

    def _update_expressions(self):
        physique = self.kernel.state_manager.get_domain("physique")
        if not physique or "needs" not in physique: return

        needs = physique["needs"]
        state = self.kernel.state_manager.get_domain("avatar_state") or {}
        
        # Mapping Logic: Needs -> Expressions
        blend_shapes = {
            "joy": 0.0,
            "angry": max(0.0, (needs.get("stress", 0) - 60) / 40) if needs.get("stress", 0) > 60 else 0.0,
            "sad": max(0.0, (needs.get("hunger", 0) - 70) / 30) if needs.get("hunger", 0) > 70 else 0.0,
            "relaxed": max(0.0, (100 - needs.get("stress", 0)) / 100),
            "surprised": 0.0
        }

        # Update State
        state["blend_shapes"] = blend_shapes
        state["last_update"] = datetime.now().isoformat()
        self.kernel.state_manager.update_domain("avatar_state", state)

    def handle_config(self):
        config = self.kernel.state_manager.get_domain("avatar_config")
        # Ensure paths are correct for the new structure
        config["vrm_path"] = "/shared/media/avatar/q_avatar.vrm"
        return config

    def handle_pose(self, data):
        state = self.kernel.state_manager.get_domain("avatar_state")
        state["pose"] = data.get("pose", "idle")
        self.kernel.state_manager.update_domain("avatar_state", state)
        return {"success": True}

# Global instance for loader
plugin = AvatarPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_config(): return plugin.handle_config()
def handle_pose(data): return plugin.handle_pose(data)
