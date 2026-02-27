"""
Desktop Plugin - Desktop Sovereignty Control
Controls wallpaper and theme via gsettings (GNOME).
Reacts to weather events (storm -> dark mode).
"""

import logging
import subprocess
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='[DESKTOP] %(message)s')
logger = logging.getLogger("desktop")

# =============================================================================
# CONSTANTS
# =============================================================================

GSETTING_WALLPAPER = "org.gnome.desktop.background picture-uri"
GSETTING_THEME = "org.gnome.desktop.interface color-scheme"

VALID_THEMES = ["default", "prefer-light", "prefer-dark"]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def run_gsettings(schema: str, key: str, value: str = None) -> str:
    """
    Run gsettings command to get or set a value.
    Returns the current value if no value is provided.
    """
    try:
        if value is None:
            # Get current value
            result = subprocess.run(
                ["gsettings", "get", schema, key],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.warning(f"gsettings get failed: {result.stderr}")
                return None
        else:
            # Set value
            result = subprocess.run(
                ["gsettings", "set", schema, key, value],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                logger.warning(f"gsettings set failed: {result.stderr}")
                return None
            return value
    except FileNotFoundError:
        logger.error("gsettings not found - not running GNOME?")
        return None
    except Exception as e:
        logger.error(f"gsettings error: {e}")
        return None


def set_wallpaper(path: str) -> bool:
    """Set desktop wallpaper from file path."""
    if not path:
        return False

    # Convert to file:// URI if needed
    if not path.startswith("file://"):
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        path = f"file://{path}"

    result = run_gsettings(GSETTING_WALLPAPER, "picture-uri", path)
    if result:
        logger.info(f"Wallpaper set to: {path}")
        return True
    return False


def get_wallpaper() -> str:
    """Get current wallpaper URI."""
    return run_gsettings(GSETTING_WALLPAPER, "picture-uri")


def set_theme(theme: str) -> bool:
    """Set color scheme (default, prefer-light, prefer-dark)."""
    if theme not in VALID_THEMES:
        logger.warning(f"Invalid theme: {theme}")
        return False

    result = run_gsettings(GSETTING_THEME, "color-scheme", theme)
    if result:
        logger.info(f"Theme set to: {theme}")
        return True
    return False


def get_theme() -> str:
    """Get current color scheme."""
    value = run_gsettings(GSETTING_THEME, "color-scheme")
    return value.strip("'") if value else "default"


# =============================================================================
# PLUGIN CLASS
# =============================================================================

class DesktopPlugin:
    def __init__(self):
        self.kernel = None
        self.last_storm_warning = None

    def initialize(self, kernel):
        self.kernel = kernel
        logger.info("DesktopPlugin initialized and connected to Kernel")

        # Subscribe to weather events
        if hasattr(kernel, 'event_bus'):
            kernel.event_bus.subscribe("EVENT_WEATHER_UPDATE", self.on_weather_update)
            logger.info("Subscribed to EVENT_WEATHER_UPDATE")

    def on_event(self, event):
        """React to events - placeholder for general event handling."""
        pass

    def on_weather_update(self, event):
        """
        Handle weather update events.
        If weather is 'storm', automatically switch to dark theme.
        """
        # Event structure: {"event": "EVENT_WEATHER_UPDATE", "source": "...", "data": {...}}
        data = event.get("data", {})
        weather = data.get("weather", "").lower()

        logger.info(f"Weather update received: {weather}")

        if weather == "storm":
            # Check debounce (don't switch too often)
            now = datetime.now()
            if self.last_storm_warning:
                last_time = datetime.fromisoformat(self.last_storm_warning)
                if (now - last_time).total_seconds() < 600:  # 10 minutes
                    logger.debug("Skipping storm theme switch - debounced")
                    return

            self.last_storm_warning = now.isoformat()

            # Switch to dark mode
            if set_theme("prefer-dark"):
                logger.warning("Storm detected - switched to dark theme")
                self._update_state()

                # Publish event for other plugins
                if hasattr(self.kernel, 'event_bus'):
                    self.kernel.event_bus.publish(
                        "EVENT_DESKTOP_THEME_CHANGED",
                        "desktop",
                        {"theme": "prefer-dark", "reason": "storm"}
                    )
        else:
            # Clear storm warning when weather improves
            self.last_storm_warning = None

    def _update_state(self):
        """Update desktop_state domain in state manager."""
        if not self.kernel:
            return

        state = {
            "wallpaper": get_wallpaper(),
            "theme": get_theme(),
            "last_update": datetime.now().isoformat()
        }

        if hasattr(self.kernel, 'state_manager'):
            self.kernel.state_manager.update_domain("desktop_state", state)
            logger.debug(f"State updated: {state}")

    # =========================================================================
    # API HANDLERS
    # =========================================================================

    def handle_set_wallpaper(self, path: str) -> dict:
        """API handler to set wallpaper."""
        success = set_wallpaper(path)

        result = {
            "success": success,
            "wallpaper": path if success else None,
            "timestamp": datetime.now().isoformat()
        }

        # Update state
        self._update_state()

        return result

    def handle_set_theme(self, theme: str) -> dict:
        """API handler to set theme."""
        if theme not in VALID_THEMES:
            return {
                "success": False,
                "error": f"Invalid theme. Valid: {VALID_THEMES}",
                "current_theme": get_theme()
            }

        success = set_theme(theme)

        result = {
            "success": success,
            "theme": theme if success else get_theme(),
            "timestamp": datetime.now().isoformat()
        }

        # Update state
        self._update_state()

        return result

    def handle_get_desktop_state(self) -> dict:
        """API handler to get current desktop state."""
        wallpaper = get_wallpaper()
        theme = get_theme()

        # Get from state manager
        state_domain = {}
        if hasattr(self.kernel, 'state_manager'):
            state_domain = self.kernel.state_manager.get_domain("desktop_state") or {}

        return {
            "wallpaper": wallpaper,
            "theme": theme,
            "valid_themes": VALID_THEMES,
            "last_update": state_domain.get("last_update", None)
        }


# =============================================================================
# EXPORTS (Loader Pattern)
# =============================================================================

plugin = DesktopPlugin()


def initialize(kernel):
    plugin.initialize(kernel)


def on_event(event):
    plugin.on_event(event)


def handle_set_wallpaper(path: str = None):
    return plugin.handle_set_wallpaper(path)


def handle_set_theme(theme: str = "default"):
    return plugin.handle_set_theme(theme)


def handle_get_desktop_state():
    return plugin.handle_get_desktop_state()
