"""
Bios Plugin - Metabolism & Hormone Cycle Simulation (v7.0 Stable)
Ported 1:1 from project-genesis Legacy (metabolism.ts, lifecycle.ts)
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[BIOS] %(message)s')
logger = logging.getLogger("bios")

# =============================================================================
# CONSTANTS & LOOKUP TABLES
# =============================================================================

LIFE_STAGE_MULTIPLIERS = {
    "infant": {"energy": 2.5, "hunger": 2.0, "thirst": 1.8, "hygiene": 1.5, "stress": 0.8, "bladder": 2.5, "bowel": 2.0, "arousal": 0, "libido": 0},
    "child": {"energy": 1.8, "hunger": 1.8, "thirst": 1.5, "hygiene": 1.3, "stress": 1.0, "bladder": 2.0, "bowel": 1.8, "arousal": 0, "libido": 0},
    "teen": {"energy": 1.5, "hunger": 1.5, "thirst": 1.3, "hygiene": 1.2, "stress": 1.5, "bladder": 1.5, "bowel": 1.3, "arousal": 1.2, "libido": 1.5},
    "adult": {"energy": 1.0, "hunger": 1.0, "thirst": 1.0, "hygiene": 1.0, "stress": 1.0, "bladder": 1.0, "bowel": 1.0, "arousal": 1.0, "libido": 1.0},
    "middle_adult": {"energy": 0.85, "hunger": 0.9, "thirst": 0.9, "hygiene": 0.95, "stress": 1.1, "bladder": 1.1, "bowel": 1.0, "arousal": 0.7, "libido": 0.6},
    "senior": {"energy": 0.6, "hunger": 0.7, "thirst": 0.75, "hygiene": 0.8, "stress": 0.9, "bladder": 1.3, "bowel": 1.1, "arousal": 0.3, "libido": 0.2},
}

# Hormone curves for 28-day cycle (0-100 scale)
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

SENSATIONS = {
    "bladder": {
        "high": "Extreme, painful bladder pressure. You MUST go NOW!",
        "medium": "Strong urge to pee. You feel restless.",
        "low": "You notice your bladder clearly.",
    },
    "hunger": {
        "high": "Your stomach growls loudly, you feel weak from hunger.",
        "medium": "You have a strong appetite.",
        "low": "You notice you should eat something soon.",
    },
    "thirst": {
        "high": "Your mouth is dry, you desperately need a drink.",
        "medium": "You're thirsty.",
        "low": "A glass of water would be nice.",
    },
    "arousal": {
        "high": "Extreme physical arousal. Every touch of your clothing is intense.",
        "medium": "A pulsing desire spreads through you.",
        "low": "A faint tingle beneath your skin.",
    },
    "stress": {
        "high": "You're extremely tense, your hands are slightly trembling.",
        "medium": "You feel stressed and restless.",
        "low": "Slight inner tension.",
    },
    "hygiene": {
        "high": "You feel uncomfortable and unclean. A shower is urgently needed.",
        "medium": "You could use a shower.",
        "low": "You don't feel quite fresh anymore.",
    },
    "energy": {
        "low_critical": "You're completely exhausted. Your eyes are closing.",
        "low_medium": "You're tired and unfocused.",
    },
    "bowel": {
        "high": "Strong pressure in your abdomen. You urgently need the toilet.",
        "medium": "Your stomach is rumbling. You should find a toilet soon.",
        "low": "Slight feeling of fullness in your abdomen.",
    },
    "libido": {
        "high": "A deep, persistent desire burns within you. It's hard to think of anything else.",
        "medium": "You feel a warm, pulsing desire.",
        "low": "A quiet longing, barely more than a whisper.",
    },
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
        self.reflex_threshold = 95

    def initialize(self, kernel):
        self.kernel = kernel
        logger.info("BiosPlugin initialized (v7.0)")

    def on_event(self, event):
        if event.get("event") == "TICK_MINUTELY":
            self._update_metabolism()
        elif event.get("event") == "TICK_DAILY":
            self._advance_cycle()

    def _update_metabolism(self):
        physique = self.kernel.state_manager.get_domain("physique")
        if not physique: return

        # Calculate time delta
        last_tick_str = physique.get("last_tick", datetime.now().isoformat())
        try:
            last_tick = datetime.fromisoformat(last_tick_str).replace(tzinfo=None)
        except:
            last_tick = datetime.now()
            
        now = datetime.now()
        diff_hours = (now - last_tick).total_seconds() / 3600
        if diff_hours < 0.005: return

        # Load lifecycle & cycle
        lifecycle = self.kernel.state_manager.get_domain("lifecycle") or {"life_stage": "adult"}
        cycle = self.kernel.state_manager.get_domain("cycle") or {"current_day": 1, "simulator": {"active": False}}
        
        stage = lifecycle.get("life_stage", "adult")
        mults = LIFE_STAGE_MULTIPLIERS.get(stage, LIFE_STAGE_MULTIPLIERS["adult"])
        needs = physique.get("needs", {})

        # 1. Base Decay
        for k in NEEDS_KEYS:
            rate = DEFAULT_RATES.get(k, 4)
            m = mults.get(k, 1.0)
            delta = rate * m * diff_hours
            if k == "energy": 
                needs[k] = max(0, needs.get(k, 100) - delta)
            else: 
                needs[k] = min(100, needs.get(k, 0) + delta)

        # 2. Synergies (e.g. bladder -> arousal)
        if needs.get("bladder", 0) > 70:
            needs["arousal"] = min(100, needs.get("arousal", 0) + 10 * diff_hours)
        if needs.get("libido", 0) > 70:
            needs["arousal"] = min(100, needs.get("arousal", 0) + 3 * diff_hours)

        # 3. Cycle Modifiers
        day = cycle.get("simulator", {}).get("simulated_day") if cycle.get("simulator", {}).get("active") else cycle.get("current_day", 1)
        phase = self._get_phase(day)
        c_mods = CYCLE_PHASE_MODIFIERS.get(phase, {})
        symptom_scale = cycle.get("simulator", {}).get("custom_modifiers", {}).get("global", 1.0) if cycle.get("simulator", {}).get("active") else 1.0
        
        for k, val in c_mods.items():
            if k in needs:
                needs[k] = max(0, min(100, needs[k] + val * symptom_scale * diff_hours * 0.1))

        # 4. Reflex Lock Check
        critical = [k for k, v in needs.items() if v >= self.reflex_threshold and k != "energy"]
        if needs.get("energy", 100) <= (100 - self.reflex_threshold):
            critical.append("energy")
            
        if critical:
            self._fire_event("EVENT_NEED_CRITICAL", {"needs": critical})

        # Update State
        physique["needs"] = {k: round(v, 2) for k, v in needs.items()}
        physique["last_tick"] = now.isoformat()
        self.kernel.state_manager.update_domain("physique", physique)

    def _advance_cycle(self):
        cycle = self.kernel.state_manager.get_domain("cycle") or {"current_day": 1, "cycle_length": 28}
        if cycle.get("simulator", {}).get("active"): return

        current_day = cycle.get("current_day", 1)
        cycle_length = cycle.get("cycle_length", 28)
        
        new_day = (current_day % cycle_length) + 1
        cycle["current_day"] = new_day
        cycle["phase"] = self._get_phase(new_day)
        cycle["hormones"] = self._get_hormones(new_day)
        cycle["last_advance"] = datetime.now().isoformat()
        
        self.kernel.state_manager.update_domain("cycle", cycle)
        self._fire_event("EVENT_CYCLE_PHASE_CHANGE", {"phase": cycle["phase"], "day": new_day})

    def _get_phase(self, day):
        if day <= 5: return "menstruation"
        if day <= 13: return "follicular"
        if day <= 15: return "ovulation"
        return "luteal"

    def _get_hormones(self, day):
        i = max(0, min(27, day - 1))
        return {
            "estrogen": HORMONE_ESTROGEN[i],
            "progesterone": HORMONE_PROGESTERONE[i],
            "lh": HORMONE_LH[i],
            "fsh": HORMONE_FSH[i],
        }

    def _get_sensations(self, needs):
        results = []
        for k, v in needs.items():
            s = SENSATIONS.get(k)
            if not s: continue
            
            if k == "energy":
                if v < 10: results.append(s["low_critical"])
                elif v < 30: results.append(s["low_medium"])
            else:
                if v > 90: results.append(s["high"])
                elif v > 60: results.append(s["medium"])
                elif v > 40: results.append(s["low"])
        return results

    def _fire_event(self, event_type, data):
        if self.kernel and self.kernel.event_bus:
            asyncio.run_coroutine_threadsafe(
                self.kernel.event_bus.publish(event_type, "plugin.bios", data),
                self.kernel.event_loop
            )

    def handle_needs(self):
        """API Handler: GET /v1/plugins/bios/needs"""
        physique = self.kernel.state_manager.get_domain("physique") or {"needs": {}}
        cycle = self.kernel.state_manager.get_domain("cycle") or {"current_day": 1}
        needs = physique.get("needs", {})
        
        return {
            "needs": needs,
            "sensations": self._get_sensations(needs),
            "cycle": {
                "day": cycle.get("current_day", 1),
                "phase": self._get_phase(cycle.get("current_day", 1)),
                "hormones": self._get_hormones(cycle.get("current_day", 1))
            },
            "reflex_lock": any(v >= self.reflex_threshold for k, v in needs.items() if k != "energy") or needs.get("energy", 100) < 5
        }

    def handle_action(self, data: Dict[str, Any]):
        """API Handler: POST /v1/plugins/bios/action"""
        action = data.get("action")
        intensity = float(data.get("intensity", 1.0))
        if not action:
            return {"success": False, "error": "No action provided"}

        physique = self.kernel.state_manager.get_domain("physique")
        needs = physique.get("needs", {})

        # 1:1 Legacy Action Logic
        if action == "eat":
            needs["hunger"] = max(0, needs.get("hunger", 0) - 30 * intensity)
            needs["energy"] = min(100, needs.get("energy", 0) + 5 * intensity)
        elif action == "drink":
            needs["thirst"] = max(0, needs.get("thirst", 0) - 40 * intensity)
        elif action == "sleep":
            needs["energy"] = min(100, needs.get("energy", 0) + 60 * intensity)
            needs["stress"] = max(0, needs.get("stress", 0) - 20 * intensity)
            needs["hunger"] = min(100, needs.get("hunger", 0) + 10 * intensity)
        elif action == "toilet":
            needs["bladder"] = max(0, needs.get("bladder", 0) - 80 * intensity)
            needs["bowel"] = max(0, needs.get("bowel", 0) - 80 * intensity)
        elif action == "shower":
            needs["hygiene"] = max(0, needs.get("hygiene", 0) - 70 * intensity)
            needs["stress"] = max(0, needs.get("stress", 0) - 10 * intensity)
        elif action == "rest":
            needs["energy"] = min(100, needs.get("energy", 0) + 15 * intensity)
            needs["stress"] = max(0, needs.get("stress", 0) - 15 * intensity)
        elif action == "pleasure":
            needs["arousal"] = max(0, needs.get("arousal", 0) - 80 * intensity)
            needs["stress"] = max(0, needs.get("stress", 0) - 20 * intensity)
            needs["energy"] = max(0, needs.get("energy", 0) - 10 * intensity)
        
        physique["needs"] = {k: round(v, 2) for k, v in needs.items()}
        self.kernel.state_manager.update_domain("physique", physique)
        return {"success": True, "action": action, "needs": needs}

# Global instance for the loader
plugin = BiosPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_needs(): return plugin.handle_needs()
def handle_action(data): return plugin.handle_action(data)
