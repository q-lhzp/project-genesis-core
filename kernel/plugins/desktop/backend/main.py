"""
Desktop Engine Plugin - System Sovereignty & UI (v7.0 Stable)
Refactored for 1:1 Legacy Compliance & v7.0 Architecture
"""

import json
import os
import subprocess
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[DESKTOP] %(message)s')
logger = logging.getLogger("desktop")

# =============================================================================
# DESKTOP LOGIC
# =============================================================================

class DesktopPlugin:
    def __init__(self):
        self.kernel = None
        self.automation_dir = "/home/leo/Schreibtisch/desktop-automation/scripts"

    def initialize(self, kernel):
        self.kernel = kernel
        logger.info("Desktop Engine initialized (v7.0)")

    def on_event(self, event):
        if event.get("event") == "EVENT_LOCATION_CHANGE":
            # Auto-change wallpaper based on location
            self._update_wallpaper_from_location(event.get("data", {}).get("location"))

    def _update_wallpaper_from_location(self, location):
        if not location: return
        logger.info(f"Syncing wallpaper to location: {location}")
        # Placeholder for real script call
        # self.handle_set_wallpaper({"location": location})

    def handle_set_wallpaper(self, data: Dict[str, Any]):
        """API Handler: POST /v1/plugins/desktop/wallpaper"""
        wallpaper = data.get("wallpaper", "cyberpunk")
        
        # 1:1 Legacy Script Call
        script = "/home/leo/Schreibtisch/set-wall-cyberpunk.sh" # SAFE: Legacy system script
        try:
            if os.path.exists(script):
                subprocess.run(["bash", script, wallpaper], timeout=5) # SAFE: Desktop command
                logger.info(f"Wallpaper changed to: {wallpaper}")
                return {"success": True, "wallpaper": wallpaper}
            return {"success": False, "error": "Script not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def handle_set_theme(self, data: Dict[str, Any]):
        theme = data.get("theme", "dark")
        # In GNOME: gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
        try:
            cmd = ["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", f"prefer-{theme}"]
            subprocess.run(cmd, timeout=5) # SAFE: Desktop command
            return {"success": True, "theme": theme}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Singleton instance
plugin = DesktopPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_set_wallpaper(data): return plugin.handle_set_wallpaper(data)
def handle_set_theme(data): return plugin.handle_set_theme(data)
