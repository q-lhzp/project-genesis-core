"""
Config Plugin - Model & MAC Configuration Management (v7.0 Stable)
Refactored for 1:1 Legacy Compliance & v7.0 Architecture
"""

import json
import logging
import os
import subprocess
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='[CONFIG] %(message)s')
logger = logging.getLogger("config")

# =============================================================================
# MODEL DISCOVERY
# =============================================================================

class ConfigPlugin:
    def __init__(self):
        self.kernel = None
        self._models_cache = None
        self._models_cache_time = 0

    def initialize(self, kernel):
        self.kernel = kernel
        logger.info("Config Engine initialized (v7.0)")

    def on_event(self, event):
        pass

    def get_openclaw_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from OpenClaw CLI."""
        try:
            # SAFE: Model discovery
            result = subprocess.run(["openclaw", "models", "list", "--json"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return [m for m in data.get("models", []) if m.get("available")]
        except: pass
        return []

    def handle_get_all(self, data=None):
        """API Handler: GET /v1/plugins/config/all"""
        import time
        if not self._models_cache or (time.time() - self._models_cache_time) > 60:
            self._models_cache = self.get_openclaw_models()
            self._models_cache_time = time.time()

        mconfig = self.kernel.state_manager.get_domain("model_config") or {}
        aconfig = self.kernel.state_manager.get_domain("agent_config") or {}
        
        return {
            "available_models": self._models_cache,
            "mac_assignments": mconfig.get("mac_assignments", {}),
            "keys": {k: "********" for k in mconfig if "key" in k or "api" in k}
        }

    def handle_save_assignments(self, data: Dict[str, str]):
        """API Handler: POST /v1/plugins/config/save"""
        mconfig = self.kernel.state_manager.get_domain("model_config") or {}
        mconfig["mac_assignments"] = data.get("assignments", {})
        self.kernel.state_manager.update_domain("model_config", mconfig)
        return {"success": True}

# Singleton instance
plugin = ConfigPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_get_all(data=None): return plugin.handle_get_all(data)
def handle_save_assignments(data): return plugin.handle_save_assignments(data)
