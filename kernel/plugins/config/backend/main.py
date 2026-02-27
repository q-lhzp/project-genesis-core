"""
Config Plugin - Model & MAC Configuration Management
Provides API for dynamic model switching via dropdowns.
"""

import json
import logging
import os
import subprocess
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='[CONFIG] %(message)s')
logger = logging.getLogger("config")

# Path to agent config
AGENT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "my-agent-config.json")

# Path to kernel model config
MODEL_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "model_config.json")

# =============================================================================
# MODEL DISCOVERY
# =============================================================================

def get_openclaw_models() -> List[Dict[str, Any]]:
    """Fetch available models from OpenClaw CLI."""
    try:
        result = subprocess.run(
            ["openclaw", "models", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            # Filter to only configured/available models
            models = [m for m in data.get("models", []) if m.get("available") and not m.get("missing")]
            logger.info(f"Loaded {len(models)} available models from OpenClaw")
            return models
    except Exception as e:
        logger.error(f"Failed to fetch OpenClaw models: {e}")

    return []


def load_agent_config() -> List[Dict[str, str]]:
    """Load current role assignments from my-agent-config.json."""
    try:
        if os.path.exists(AGENT_CONFIG_PATH):
            with open(AGENT_CONFIG_PATH, "r") as f:
                config = json.load(f)
                logger.info(f"Loaded agent config with {len(config)} role assignments")
                return config
    except Exception as e:
        logger.error(f"Failed to load agent config: {e}")

    return []


def save_agent_config(config: List[Dict[str, str]]) -> bool:
    """Save role assignments to my-agent-config.json."""
    try:
        with open(AGENT_CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved agent config with {len(config)} role assignments")
        return True
    except Exception as e:
        logger.error(f"Failed to save agent config: {e}")
        return False


def load_model_config() -> Dict[str, Any]:
    """Load kernel model config from data/model_config.json."""
    try:
        if os.path.exists(MODEL_CONFIG_PATH):
            with open(MODEL_CONFIG_PATH, "r") as f:
                config = json.load(f)
                logger.info("Loaded kernel model config")
                return config
    except Exception as e:
        logger.error(f"Failed to load model config: {e}")

    return {"mac_assignments": {}, "api_key": "", "key_anthropic": "", "key_venice": "", "key_xai": "", "key_gemini_img": "", "key_fal": "", "key_gemini": "", "key_minimax": "", "local_url": "", "image_provider": "nano", "vision_provider": "gpt-4o"}


def save_model_config(config: Dict[str, Any]) -> bool:
    """Save kernel model config to data/model_config.json."""
    try:
        os.makedirs(os.path.dirname(MODEL_CONFIG_PATH), exist_ok=True)
        with open(MODEL_CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        logger.info("Saved kernel model config")
        return True
    except Exception as e:
        logger.error(f"Failed to save model config: {e}")
        return False


# =============================================================================
# PLUGIN CLASS
# =============================================================================

class ConfigPlugin:
    def __init__(self):
        self.kernel = None
        self._models_cache = None
        self._models_cache_time = 0

    def initialize(self, kernel):
        self.kernel = kernel
        logger.info("ConfigPlugin initialized and connected to Kernel")

    def on_event(self, event):
        # No periodic events needed
        pass

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models (cached for 60 seconds)."""
        import time
        now = time.time()

        if self._models_cache is None or (now - self._models_cache_time) > 60:
            self._models_cache = get_openclaw_models()
            self._models_cache_time = now

        return self._models_cache

    def get_role_assignments(self) -> Dict[str, str]:
        """Get current role -> model assignments."""
        config = load_agent_config()
        return {entry["agent"]: entry["model"] for entry in config}

    def set_role_model(self, role: str, model: str) -> bool:
        """Update a role's model assignment."""
        config = load_agent_config()

        # Find and update or add
        found = False
        for entry in config:
            if entry["agent"].lower() == role.lower():
                entry["model"] = model
                found = True
                break

        if not found:
            config.append({"agent": role, "model": model})

        return save_agent_config(config)

    def get_all_config(self) -> Dict[str, Any]:
        """Get full configuration for UI."""
        return {
            "available_models": self.get_available_models(),
            "role_assignments": self.get_role_assignments()
        }

    def save_config(self, assignments: Dict[str, str]) -> bool:
        """Save role assignments to both my-agent-config.json and data/model_config.json."""
        # Save to my-agent-config.json
        config = [{"agent": role, "model": model} for role, model in assignments.items()]
        if not save_agent_config(config):
            return False

        # Update kernel model_config.json
        model_config = load_model_config()
        model_config["mac_assignments"] = {
            "persona": assignments.get("Persona", ""),
            "limbic": assignments.get("Limbic", ""),
            "analyst": assignments.get("Analyst", ""),
            "developer": assignments.get("Developer", "")
        }

        return save_model_config(model_config)


# Global instance for the loader
plugin = ConfigPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def get_available_models(): return plugin.get_available_models()
def get_role_assignments(): return plugin.get_role_assignments()
def set_role_model(role, model): return plugin.set_role_model(role, model)
def get_all_config(): return plugin.get_all_config()
def save_config(assignments): return plugin.save_config(assignments)
