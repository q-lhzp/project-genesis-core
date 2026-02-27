"""
Developer Plugin - Self-Expansion Engine
Allows Q to propose and create new scripts/tools in the development folder.
"""

import ast
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[DEVELOPER] %(message)s')
logger = logging.getLogger("developer")

# =============================================================================
# CONSTANTS
# =============================================================================

PLUGIN_NAME = "developer-engine"
DEVELOPMENT_FOLDER = "development"

# =============================================================================
# PLUGIN CLASS
# =============================================================================

class DeveloperPlugin:
    def __init__(self):
        self.kernel = None
        self.data_dir = None
        self.development_path = None

    def initialize(self, kernel):
        self.kernel = kernel

        # Set up development folder path
        base_path = getattr(kernel, 'base_path', os.getcwd())
        self.data_dir = os.path.join(base_path, 'data')
        self.development_path = os.path.join(self.data_dir, DEVELOPMENT_FOLDER)

        # Create development folder if it doesn't exist
        os.makedirs(self.development_path, exist_ok=True)

        # Initialize development_state domain if not exists
        dev_state = kernel.state_manager.get_domain("development_state")
        if dev_state is None:
            kernel.state_manager.update_domain("development_state", {
                "projects": [],
                "last_proposal": None,
                "initialized_at": datetime.now().isoformat()
            })

        logger.info(f"DeveloperPlugin initialized. Development path: {self.development_path}")

    def on_event(self, event):
        """Handle kernel events."""
        if event.get("event") == "TICK_MINUTELY":
            # Could add auto-validation or cleanup here
            pass

    # =========================================================================
    # API HANDLERS
    # =========================================================================

    def handle_propose_code(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a proposed file to the development folder.
        Validates .py files for syntax errors before saving.

        Request format:
        {
            "filename": "my_tool.py",
            "content": "print('Hello World')",
            "description": "Optional description"
        }
        """
        filename = request.get("filename", "")
        content = request.get("content", "")
        description = request.get("description", "")

        if not filename:
            return {"success": False, "error": "filename is required"}

        if not content:
            return {"success": False, "error": "content is required"}

        # Security: prevent path traversal
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(self.development_path, safe_filename)

        # Validate Python files
        if safe_filename.endswith('.py'):
            validation_result = self._validate_python_syntax(content)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Syntax error: {validation_result['error']}",
                    "line": validation_result.get("line")
                }

        # Save the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Saved proposal: {safe_filename}")

            # Update development_state
            self._update_development_state(safe_filename, description)

            return {
                "success": True,
                "filename": safe_filename,
                "path": file_path,
                "validated": safe_filename.endswith('.py')
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def handle_list_projects(self) -> Dict[str, Any]:
        """
        Scan the development folder and return list of proposed projects.

        Returns:
        {
            "success": True,
            "projects": [
                {
                    "name": "my_tool.py",
                    "type": "python",
                    "size": 1024,
                    "modified": "2026-02-27T10:30:00"
                }
            ]
        }
        """
        projects = []

        try:
            for entry in os.scandir(self.development_path):
                if entry.is_file():
                    stat = entry.stat()
                    file_type = self._get_file_type(entry.name)

                    projects.append({
                        "name": entry.name,
                        "type": file_type,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })

            # Sort by modified date (newest first)
            projects.sort(key=lambda x: x["modified"], reverse=True)

            logger.info(f"Found {len(projects)} projects in development folder")

            return {
                "success": True,
                "projects": projects,
                "total": len(projects)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _validate_python_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validate Python code using ast.parse.
        Returns {"valid": True} or {"valid": False, "error": "...", "line": N}
        """
        try:
            ast.parse(code)
            return {"valid": True}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "line": e.lineno
            }

    def _get_file_type(self, filename: str) -> str:
        """Determine file type from extension."""
        ext = os.path.splitext(filename)[1].lower()
        type_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".json": "json",
            ".md": "markdown",
            ".sh": "shell",
            ".yaml": "yaml",
            ".yml": "yaml"
        }
        return type_map.get(ext, "unknown")

    def _update_development_state(self, filename: str, description: str):
        """Update the development_state domain in kernel state."""
        dev_state = self.kernel.state_manager.get_domain("development_state")

        if dev_state is None:
            dev_state = {"projects": [], "last_proposal": None}

        # Add new project to list
        project_entry = {
            "name": filename,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "type": self._get_file_type(filename)
        }

        # Check if already exists, update if so
        existing_names = [p["name"] for p in dev_state.get("projects", [])]
        if filename in existing_names:
            for p in dev_state["projects"]:
                if p["name"] == filename:
                    p.update(project_entry)
                    p["updated_at"] = datetime.now().isoformat()
        else:
            dev_state["projects"].insert(0, project_entry)

        # Update last_proposal
        dev_state["last_proposal"] = {
            "filename": filename,
            "timestamp": datetime.now().isoformat()
        }

        self.kernel.state_manager.update_domain("development_state", dev_state)
        logger.info(f"Updated development_state with project: {filename}")


# =============================================================================
# GLOBAL EXPORTS (Plugin Loader Interface)
# =============================================================================

plugin = DeveloperPlugin()

def initialize(kernel):
    plugin.initialize(kernel)

def on_event(event):
    plugin.on_event(event)

def handle_propose_code(request: Dict[str, Any]) -> Dict[str, Any]:
    return plugin.handle_propose_code(request)

def handle_list_projects() -> Dict[str, Any]:
    return plugin.handle_list_projects()
