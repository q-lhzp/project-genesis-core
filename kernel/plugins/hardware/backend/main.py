"""
Hardware Engine Plugin - System Monitoring & Resonance (v7.0 Stable)
Refactored for 1:1 Legacy Compliance & v7.0 Architecture
"""

import json
import os
import subprocess
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[HARDWARE] %(message)s')
logger = logging.getLogger("hardware")

# =============================================================================
# HARDWARE MONITORING LOGIC
# =============================================================================

class HardwarePlugin:
    def __init__(self):
        self.kernel = None

    def initialize(self, kernel):
        self.kernel = kernel
        if not self.kernel.state_manager.get_domain("hardware_resonance"):
            self.kernel.state_manager.update_domain("hardware_resonance", {
                "cpu_percent": 0,
                "memory": {"percent": 0, "used_mb": 0, "total_mb": 0},
                "cpu_temp_c": 0,
                "uptime": {"hours": 0, "minutes": 0},
                "resonance": "Calm"
            })
        logger.info("Hardware Engine initialized (v7.0)")

    def on_event(self, event):
        if event.get("event") == "TICK_MINUTELY":
            self._update_stats()

    def _update_stats(self):
        """Fetch all hardware stats."""
        cpu = self._get_cpu_usage()
        mem = self._get_memory_usage()
        temp = self._get_cpu_temp()
        uptime = self._get_uptime()
        
        # Determine Resonance
        resonance = "Calm"
        if cpu > 80 or mem.get("percent", 0) > 90: resonance = "Strained"
        elif cpu > 50: resonance = "Active"
        
        new_stats = {
            "cpu_percent": cpu,
            "memory": mem,
            "cpu_temp_c": temp,
            "uptime": uptime,
            "resonance": resonance,
            "last_update": datetime.now().isoformat()
        }
        
        self.kernel.state_manager.update_domain("hardware_resonance", new_stats)
        
        # Stress Event
        if resonance == "Strained":
            self._fire_event("EVENT_HARDWARE_STRESS", new_stats)

    def _get_cpu_usage(self) -> float:
        try:
            # Simple /proc/stat parser or top
            res = subprocess.run(["top", "-bn1"], capture_output=True, text=True, timeout=2)
            for line in res.stdout.split('\n'):
                if '%Cpu(s)' in line:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if 'id' in p: return round(100.0 - float(parts[i-1].replace(',', '.')), 1)
            return 0.0
        except: return 0.0

    def _get_memory_usage(self) -> Dict:
        try:
            res = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=2)
            lines = res.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                total = int(parts[1])
                used = int(parts[2])
                return {"total_mb": total, "used_mb": used, "percent": round((used/total)*100, 1)}
            return {}
        except: return {}

    def _get_cpu_temp(self) -> float:
        path = "/sys/class/thermal/thermal_zone0/temp"
        try:
            if os.path.exists(path):
                with open(path, 'r') as f: # SAFE: System metrics
                    return round(int(f.read().strip()) / 1000.0, 1)
            return 0.0
        except: return 0.0

    def _get_uptime(self) -> Dict:
        try:
            with open('/proc/uptime', 'r') as f: # SAFE: System metrics
                seconds = float(f.read().split()[0])
                return {"hours": int(seconds // 3600), "minutes": int((seconds % 3600) // 60)}
        except: return {}

    def _fire_event(self, event_type, data):
        if self.kernel and self.kernel.event_bus:
            asyncio.run_coroutine_threadsafe(
                self.kernel.event_bus.publish(event_type, "plugin.hardware", data),
                self.kernel.event_loop
            )

    def handle_get_stats(self, data=None):
        return self.kernel.state_manager.get_domain("hardware_resonance") or {}

# Singleton instance
plugin = HardwarePlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_get_stats(data=None): return plugin.handle_get_stats(data)
