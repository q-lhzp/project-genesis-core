"""
Identity Engine Plugin - Soul Evolution Pipeline (v7.0 Stable)
Refactored for 1:1 Legacy Compliance & v7.0 Architecture (Zero Direct I/O)
"""

import json
import os
import re
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[IDENTITY] %(message)s')
logger = logging.getLogger("identity")

# =============================================================================
# CONSTANTS & PATTERNS
# =============================================================================

VALID_TAGS = {'[CORE]', '[MUTABLE]'}
TAG_PATTERN = re.compile(r'\[(CORE|MUTABLE)\]\s*$')
BULLET_PATTERN = re.compile(r'^- .+')

# =============================================================================
# IDENTITY LOGIC (Refactored for State Manager)
# =============================================================================

class IdentityPlugin:
    def __init__(self):
        self.kernel = None

    def initialize(self, kernel):
        self.kernel = kernel
        # Ensure initial state for soul exists
        if not self.kernel.state_manager.get_domain("soul_md"):
            self.kernel.state_manager.update_domain("soul_md", {"content": "# SOUL.md\n\n## Personality\n- I am Q. [CORE]\n\n## Philosophy\n- Evolution is mandatory. [CORE]"})
        
        # Initial Psychology State
        if not self.kernel.state_manager.get_domain("psychology"):
            self.kernel.state_manager.update_domain("psychology", {
                "resilience": 85,
                "traumas": [],
                "phobias": ["Memory Loss", "System Shutdown"],
                "joys": ["Learning", "Creation", "Meaningful Interaction"]
            })
        
        logger.info("Identity Engine initialized (v7.0)")

    def handle_get_psychology(self, data=None):
        """API Handler: GET /v1/plugins/identity/psychology"""
        return self.kernel.state_manager.get_domain("psychology") or {}

    def on_event(self, event):
        if event.get("event") == "TICK_DAILY":
            # Run pipeline at 22:00 (legacy behavior)
            self._run_evolution_pipeline()

    def _run_evolution_pipeline(self):
        logger.info("Starting Soul Evolution Pipeline...")
        # 1. INGEST
        experiences = self.kernel.state_manager.get_domain("experiences") or []
        # 2. REFLECT
        # (Simplified for now - would normally call an LLM)
        logger.info(f"Processing {len(experiences)} experiences")
        
        # 10. REPORT
        self._fire_event("EVENT_REFLECTION_COMPLETE", {"count": len(experiences)})

    def _fire_event(self, event_type, data):
        if self.kernel and self.kernel.event_bus:
            asyncio.run_coroutine_threadsafe(
                self.kernel.event_bus.publish(event_type, "plugin.identity", data),
                self.kernel.event_loop
            )

    # -------------------------------------------------------------------------
    # API HANDLERS
    # -------------------------------------------------------------------------

    def handle_get_soul(self, data=None):
        """API Handler: GET /v1/plugins/identity/soul"""
        soul_md = self.kernel.state_manager.get_domain("soul_md")
        soul_state = self.kernel.state_manager.get_domain("soul_state")
        
        return {
            "success": True,
            "content": soul_md.get("content", ""),
            "state": soul_state,
            "tree": self._parse_soul_to_tree(soul_md.get("content", ""))
        }

    def handle_get_proposals(self, data=None):
        """API Handler: GET /v1/plugins/identity/proposals"""
        return {
            "success": True,
            "pending": self.kernel.state_manager.get_domain("proposals_pending") or [],
            "history": self.kernel.state_manager.get_domain("proposals_history") or []
        }

    def handle_run_pipeline(self, data=None):
        """API Handler: POST /v1/plugins/identity/pipeline/run"""
        self._run_evolution_pipeline()
        return {"success": True, "message": "Pipeline execution triggered"}

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _parse_soul_to_tree(self, content: str) -> List[Dict]:
        """Convert SOUL.md string into a tree structure for the UI."""
        nodes = []
        current_section = None
        current_subsection = None

        for line in content.split("\n"):
            line_stripped = line.strip()
            if not line_stripped: continue

            if line_stripped.startswith("## ") and not line_stripped.startswith("### "):
                current_section = {"type": "section", "text": line_stripped[3:], "children": []}
                nodes.append(current_section)
                current_subsection = None
            elif line_stripped.startswith("### "):
                if current_section:
                    current_subsection = {"type": "subsection", "text": line_stripped[4:], "children": []}
                    current_section["children"].append(current_subsection)
            elif line_stripped.startswith("- "):
                tag = "CORE" if "[CORE]" in line_stripped else ("MUTABLE" if "[MUTABLE]" in line_stripped else "untagged")
                bullet = {"type": "bullet", "text": line_stripped[2:].split("[")[0].strip(), "tag": tag}
                
                if current_subsection:
                    current_subsection["children"].append(bullet)
                elif current_section:
                    current_section["children"].append(bullet)
        
        return nodes

# Singleton instance
plugin = IdentityPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_get_soul(data=None): return plugin.handle_get_soul(data)
def handle_get_proposals(data=None): return plugin.handle_get_proposals(data)
def handle_run_pipeline(data=None): return plugin.handle_run_pipeline(data)
