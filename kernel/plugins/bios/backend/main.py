"""
Bios Plugin - Metabolism & Hormone Cycle Simulation
Ported from project-genesis/src/simulation/metabolism.ts
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='[BIOS] %(message)s')
logger = logging.getLogger("bios")

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================

LIFE_STAGE_MULTIPLIERS = {
    "infant": {"energy": 2.5, "hunger": 2.0, "thirst": 1.8, "hygiene": 1.5, "stress": 0.8, "bladder": 2.5, "bowel": 2.0, "arousal": 0, "libido": 0},
    "child": {"energy": 1.8, "hunger": 1.8, "thirst": 1.5, "hygiene": 1.3, "stress": 1.0, "bladder": 2.0, "bowel": 1.8, "arousal": 0, "libido": 0},
    "teen": {"energy": 1.5, "hunger": 1.5, "thirst": 1.3, "hygiene": 1.2, "stress": 1.5, "bladder": 1.5, "bowel": 1.3, "arousal": 1.2, "libido": 1.5},
    "adult": {"energy": 1.0, "hunger": 1.0, "thirst": 1.0, "hygiene": 1.0, "stress": 1.0, "bladder": 1.0, "bowel": 1.0, "arousal": 1.0, "libido": 1.0},
    "middle_adult": {"energy": 0.85, "hunger": 0.9, "thirst": 0.9, "hygiene": 0.95, "stress": 1.1, "bladder": 1.1, "bowel": 1.0, "arousal": 0.7, "libido": 0.6},
    "senior": {"energy": 0.6, "hunger": 0.7, "thirst": 0.75, "hygiene": 0.8, "stress": 0.9, "bladder": 1.3, "bowel": 1.1, "arousal": 0.3, "libido": 0.2},
}

# Hormone curves for 28-day cycle
HORMONE_ESTROGEN = [20, 22, 25, 28, 30, 35, 42, 50, 60, 70, 80, 90, 95, 100, 85, 65, 50, 45, 55, 65, 70, 68, 60, 50, 40, 32, 25, 20]
HORMONE_PROGESTERONE = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 8, 15, 30, 50, 65, 80, 90, 100, 95, 85, 70, 55, 40, 20, 8]
HORMONE_LH = [10, 10, 10, 12, 12, 14, 16, 18, 22, 30, 45, 70, 95, 100, 40, 15, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
HORMONE_FSH = [35, 40, 50, 55, 60, 65, 70, 65, 55, 45, 40, 50, 70, 80, 40, 25, 20, 18, 16, 15, 14, 13, 12, 12, 15, 20, 25, 30]

CYCLE_PHASE_MODIFIERS = {
    "menstruation": {"energy": -12, "hunger": 5, "stress": 8, "libido": -3},
    "follicular": {"energy": 5, "stress": -5, "libido": 2},
    "ovulation": {"energy": 8, "arousal": 15, "stress": -8, "libido": 10},
    "luteal": {"energy": -8, "hunger": 12, "stress": 10, "libido": -2},
}

DEFAULT_RATES = {
    "energy": 4, "hunger": 6, "thirst": 10, "bladder": 8, "bowel": 3,
    "hygiene": 2, "stress": 3, "arousal": 5, "libido": 2,
}

NEEDS_KEYS = ["energy", "hunger", "thirst", "bladder", "bowel", "hygiene", "stress", "arousal", "libido"]

# =============================================================================
# PLUGIN CLASS
# =============================================================================

class BiosPlugin:
    def __init__(self):
        self.kernel = None

    def initialize(self, kernel):
        self.kernel = kernel
        logger.info("BiosPlugin initialized and connected to Kernel")

    def on_event(self, event):
        if event.get("event") == "TICK_MINUTELY":
            self._update_metabolism()

    def _update_metabolism(self):
        physique = self.kernel.state_manager.get_domain("physique")
        if not physique: return

        # Calculate time delta (Ensure both are naive for comparison)
        last_tick_str = physique.get("last_tick", datetime.now().isoformat())
        last_tick = datetime.fromisoformat(last_tick_str).replace(tzinfo=None)
        now = datetime.now()
        diff_hours = (now - last_tick).total_seconds() / 3600
        if diff_hours < 0.005: return

        # Load lifecycle & cycle
        lifecycle = self.kernel.state_manager.get_domain("lifecycle") or {"life_stage": "adult"}
        cycle = self.kernel.state_manager.get_domain("cycle") or {"current_day": 1}
        
        stage = lifecycle.get("life_stage", "adult")
        mults = LIFE_STAGE_MULTIPLIERS.get(stage, LIFE_STAGE_MULTIPLIERS["adult"])
        needs = physique.get("needs", {})

        # 1. Base Decay
        for k in NEEDS_KEYS:
            rate = DEFAULT_RATES.get(k, 4)
            m = mults.get(k, 1.0)
            delta = rate * m * diff_hours
            if k == "energy": needs[k] = max(0, needs.get(k, 100) - delta)
            else: needs[k] = min(100, needs.get(k, 0) + delta)

        # 2. Cycle Modifiers
        phase = self._get_phase(cycle.get("current_day", 1))
        c_mods = CYCLE_PHASE_MODIFIERS.get(phase, {})
        for k, val in c_mods.items():
            if k in needs:
                needs[k] = max(0, min(100, needs[k] + val * diff_hours * 0.1))

        # Update State
        physique["needs"] = needs
        physique["last_tick"] = datetime.now().isoformat()
        self.kernel.state_manager.update_domain("physique", physique)

    def _get_phase(self, day):
        if day <= 5: return "menstruation"
        if day <= 13: return "follicular"
        if day <= 15: return "ovulation"
        return "luteal"

    def handle_needs(self):
        return self.kernel.state_manager.get_domain("physique").get("needs", {})

# Global instance for the loader
plugin = BiosPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_needs(): return plugin.handle_needs()
