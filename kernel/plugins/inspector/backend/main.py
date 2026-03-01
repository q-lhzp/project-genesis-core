import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='[INSPECTOR] %(message)s')
logger = logging.getLogger("inspector")

class InspectorPlugin:
    """Plugin for inspecting agent prompts and system state."""
    
    def __init__(self):
        self.kernel = None
        self.prompt_history = {}  # In-memory storage for prompts
        
    def initialize(self, kernel):
        """Initialize with kernel reference."""
        self.kernel = kernel
        logger.info("InspectorPlugin initialized")
        
    def handle_log_prompt(self, data: Dict[str, Any]):
        """API Handler: POST /v1/plugins/inspector/log_prompt"""
        agent_id = data.get("agent_id", "unknown")
        prompt = data.get("prompt", "")
        injected_data = data.get("injected_data", {})
        
        # Store latest prompt for each agent
        self.prompt_history[agent_id] = {
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "injected_data": injected_data
        }
        logger.info(f"Logged prompt for agent: {agent_id}")
        return {"success": True}
        
    def handle_get_prompts(self):
        """API Handler: GET /v1/plugins/inspector/prompts"""
        return self.prompt_history

# Singleton Instance
plugin = InspectorPlugin()

# Module Exports
def initialize(kernel): plugin.initialize(kernel)
def handle_log_prompt(data): return plugin.handle_log_prompt(data)
def handle_get_prompts(): return plugin.handle_get_prompts()
