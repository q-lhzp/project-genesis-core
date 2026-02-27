"""
Hardware Plugin - System Resource Monitoring & Hardware Resonance
Monitors CPU, RAM, and Temperature; publishes stress events.
"""

import logging
import subprocess
import os
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='[HARDWARE] %(message)s')
logger = logging.getLogger("hardware")

# =============================================================================
# CONSTANTS
# =============================================================================

CPU_THRESHOLD = 80.0  # % CPU usage to trigger stress
RAM_THRESHOLD = 90.0  # % RAM usage to trigger stress
TEMP_THRESHOLD = 85.0  # °C temperature to trigger stress

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_cpu_usage() -> float:
    """Get CPU usage percentage using top or mpstat."""
    try:
        # Try using top (more portable)
        result = subprocess.run(
            ["top", "-bn1"],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split('\n'):
            if 'Cpu(s)' in line or '%Cpu' in line:
                # Extract idle percentage
                match = re.search(r'(\d+\.\d+)\s*id', line)
                if match:
                    idle = float(match.group(1))
                    return round(100.0 - idle, 1)
        return 0.0
    except Exception as e:
        logger.warning(f"CPU monitoring failed: {e}")
        return 0.0

def get_ram_usage() -> float:
    """Get RAM usage percentage from /proc/meminfo or free."""
    try:
        # Try using free command
        result = subprocess.run(
            ["free", "-b"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 3:
                total = int(parts[1])
                used = int(parts[2])
                if total > 0:
                    return round((used / total) * 100.1, 1)
    except Exception:
        pass

    # Fallback: read /proc/meminfo
    try:
        with open('/proc/meminfo', 'r') as f:
            content = f.read()
        mem = {}
        for line in content.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                mem[key.strip()] = val.strip().split()[0]
        total = int(mem.get('MemTotal', 0))
        available = int(mem.get('MemAvailable', 0))
        if total > 0:
            used = total - available
            return round((used / total) * 100.1, 1)
    except Exception as e:
        logger.warning(f"RAM monitoring failed: {e}")
    return 0.0

def get_temperature() -> float:
    """Get CPU temperature from various sources."""
    temp = None

    # Try /sys/class/thermal (Linux)
    thermal_zones = ['/sys/class/thermal/thermal_zone0/temp',
                     '/sys/class/thermal/thermal_zone1/temp',
                     '/sys/class/thermal/thermal_zone2/temp']
    for tz in thermal_zones:
        try:
            if os.path.exists(tz):
                with open(tz, 'r') as f:
                    temp_c = int(f.read().strip()) / 1000.0
                    if temp is None or temp_c > temp:
                        temp = temp_c
        except Exception:
            pass

    # Try vcgencmd (Raspberry Pi)
    if temp is None:
        try:
            result = subprocess.run(
                ["vcgencmd", "measure_temp"],
                capture_output=True,
                text=True,
                timeout=5
            )
            match = re.search(r'temp=(\d+\.\d+)', result.stdout)
            if match:
                temp = float(match.group(1))
        except Exception:
            pass

    # Try sensors (lm-sensors)
    if temp is None:
        try:
            result = subprocess.run(
                ["sensors"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Look for CPU temperature patterns
            for line in result.stdout.split('\n'):
                match = re.search(r'Core 0.*?(\d+\.\d+)', line)
                if match:
                    t = float(match.group(1))
                    if temp is None or t > temp:
                        temp = t
        except Exception:
            pass

    return round(temp, 1) if temp else 0.0

# =============================================================================
# PLUGIN CLASS
# =============================================================================

class HardwarePlugin:
    def __init__(self):
        self.kernel = None
        self.last_stress_event = None

    def initialize(self, kernel):
        self.kernel = kernel
        logger.info("HardwarePlugin initialized and connected to Kernel")

    def on_event(self, event):
        """React to TICK_MINUTELY events to monitor hardware."""
        if event.get("event") == "TICK_MINUTELY":
            self._monitor_resources()

    def _monitor_resources(self):
        """Fetch hardware stats, check thresholds, update state, publish events."""
        cpu = get_cpu_usage()
        ram = get_ram_usage()
        temp = get_temperature()

        # Build hardware stats
        stats = {
            "cpu_percent": cpu,
            "ram_percent": ram,
            "temperature_celsius": temp,
            "timestamp": datetime.now().isoformat()
        }

        # Update hardware_resonance state domain
        state = self.kernel.state_manager.get_domain("hardware_resonance") or {}
        state.update(stats)
        state["last_update"] = datetime.now().isoformat()
        self.kernel.state_manager.update_domain("hardware_resonance", state)

        logger.info(f"Resources: CPU={cpu}% RAM={ram}% TEMP={temp}°C")

        # Check thresholds and publish stress event
        stress_reasons = []
        if cpu > CPU_THRESHOLD:
            stress_reasons.append(f"cpu_high:{cpu}%")
        if ram > RAM_THRESHOLD:
            stress_reasons.append(f"ram_high:{ram}%")
        if temp > TEMP_THRESHOLD:
            stress_reasons.append(f"temp_high:{temp}°C")

        if stress_reasons:
            self._publish_stress_event(stress_reasons)

    def _publish_stress_event(self, reasons: list):
        """Publish EVENT_HARDWARE_STRESS if not recently published."""
        now = datetime.now()

        # Debounce: don't publish if last event was < 5 minutes ago
        if self.last_stress_event:
            last_time = datetime.fromisoformat(self.last_stress_event)
            if (now - last_time).total_seconds() < 300:
                return

        self.last_stress_event = now.isoformat()

        event = {
            "event": "EVENT_HARDWARE_STRESS",
            "payload": {
                "reasons": reasons,
                "timestamp": now.isoformat()
            }
        }

        if hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.publish(event)
        logger.warning(f"HARDWARE STRESS: {', '.join(reasons)}")

    def handle_get_stats(self) -> dict:
        """API handler to get current hardware stats."""
        cpu = get_cpu_usage()
        ram = get_ram_usage()
        temp = get_temperature()

        state = self.kernel.state_manager.get_domain("hardware_resonance") or {}

        return {
            "cpu_percent": cpu,
            "ram_percent": ram,
            "temperature_celsius": temp,
            "cpu_threshold": CPU_THRESHOLD,
            "ram_threshold": RAM_THRESHOLD,
            "temp_threshold": TEMP_THRESHOLD,
            "last_update": state.get("last_update", None),
            "status": "ok" if cpu < CPU_THRESHOLD and ram < RAM_THRESHOLD else "stressed"
        }


# =============================================================================
# EXPORTS (Loader Pattern)
# =============================================================================

plugin = HardwarePlugin()

def initialize(kernel):
    plugin.initialize(kernel)

def on_event(event):
    plugin.on_event(event)

def handle_get_stats():
    return plugin.handle_get_stats()
