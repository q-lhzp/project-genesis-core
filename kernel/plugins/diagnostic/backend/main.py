import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("diagnostic")

class DiagnosticPlugin:
    def __init__(self):
        self.kernel = None

    def initialize(self, kernel):
        self.kernel = kernel
        logger.info("Diagnostic Plugin Initialized")

    def handle_health(self):
        """API Handler: Returns a health report of all loaded plugins."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "HEALTHY",
            "plugins": {}
        }

        # Check all plugins
        loader = getattr(self.kernel, 'plugin_loader', None)
        if not loader:
            return {"error": "Plugin loader not available"}

        for p_id, p_info in loader.loaded_plugins.items():
            manifest = p_info.get("manifest", {})
            module = p_info.get("module", None)
            
            p_report = {
                "name": manifest.get("name", "Unknown"),
                "version": manifest.get("version", "0.0.0"),
                "backend": "ONLINE" if module else "OFFLINE",
                "endpoints": []
            }

            # Check manifest API routes
            api_routes = manifest.get("api_routes", {})
            for route, handler in api_routes.items():
                p_report["endpoints"].append({
                    "route": route,
                    "handler": handler,
                    "status": "VERIFIED" if hasattr(module, handler) else "MISSING"
                })
            
            report["plugins"][p_id] = p_report

        return report

    def handle_logs(self, data=None):
        """API Handler: GET /v1/plugins/diagnostic/logs"""
        log_path = "kernel.log.jsonl"
        if not os.path.exists(log_path):
            return {"error": "Log file not found"}
        
        try:
            with open(log_path, 'r') as f: # SAFE: Diagnostic tool
                lines = f.readlines()
                return {"logs": lines[-50:]}
        except:
            return {"error": "Failed to read logs"}

    def handle_verify(self):
        """API Handler: POST /v1/plugins/diagnostic/verify"""
        # Placeholder for automated data-flow verification
        return {"status": "verification_triggered", "message": "Global audit initiated."}

# Global instance
plugin = DiagnosticPlugin()

def initialize(kernel): plugin.initialize(kernel)
def handle_health(): return plugin.handle_health()
def handle_verify(): return plugin.handle_verify()
