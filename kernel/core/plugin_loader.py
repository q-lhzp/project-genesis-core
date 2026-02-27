import os
import json
import importlib.util
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[PLUGIN_LOADER] %(message)s')
logger = logging.getLogger("plugin_loader")

class PluginLoader:
    def __init__(self, kernel, plugins_dir):
        self.kernel = kernel
        self.plugins_dir = plugins_dir
        self.loaded_plugins = {}

    def discover_and_load(self):
        """Scan the plugins directory and load all valid plugins."""
        logger.info(f"Scanning for plugins in: {self.plugins_dir}")
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
            return

        for entry in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, entry)
            if os.path.isdir(plugin_path):
                manifest_path = os.path.join(plugin_path, "manifest.json")
                if os.path.exists(manifest_path):
                    self._load_plugin(entry, plugin_path, manifest_path)
                else:
                    logger.warning(f"Directory {entry} missing manifest.json, skipping.")

    def _load_plugin(self, plugin_id, path, manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # 1. Validation (Basic)
            required = ["id", "name", "version"]
            for field in required:
                if field not in manifest:
                    logger.error(f"Plugin {plugin_id} missing required field: {field}")
                    return

            # 2. Dynamic Import of Backend
            # According to spec: plugins/[id]/backend/main.py
            backend_main = os.path.join(path, "backend", "main.py")
            module = None
            if os.path.exists(backend_main):
                # Add plugin path to sys.path to allow internal imports within the plugin
                plugin_backend_dir = os.path.dirname(backend_main)
                if plugin_backend_dir not in sys.path:
                    sys.path.insert(0, plugin_backend_dir)

                spec = importlib.util.spec_from_file_location(f"gen_plugin_{plugin_id}", backend_main)
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"gen_plugin_{plugin_id}"] = module
                spec.loader.exec_module(module)
                
                # Initialize plugin if it has an init function
                # Pass the kernel so plugin can access state_manager, event_bus, etc.
                if hasattr(module, "initialize"):
                    module.initialize(self.kernel)
                    logger.info(f"Initialized backend for {plugin_id}")

            # 3. Register Event Subscriptions
            if "events" in manifest and module:
                subs = manifest["events"].get("subscribes", [])
                if hasattr(module, "on_event"):
                    for event_type in subs:
                        self.kernel.event_bus.subscribe(event_type, module.on_event)
                        logger.info(f"Plugin {plugin_id} subscribed to {event_type}")

            self.loaded_plugins[plugin_id] = {
                "manifest": manifest,
                "module": module,
                "path": path
            }
            logger.info(f"Successfully loaded plugin: {manifest['name']} v{manifest['version']}")

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}")

    def get_plugin_manifests(self):
        return [p["manifest"] for p in self.loaded_plugins.values()]

    def get_plugin_by_id(self, plugin_id):
        return self.loaded_plugins.get(plugin_id)
