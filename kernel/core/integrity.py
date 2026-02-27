#!/usr/bin/env python3
"""
Project Genesis Core - Plugin Integrity Validator
Validates plugin directories for security, structure, and compliance.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


class IntegrityValidator:
    """Validates plugin directories against Genesis Core security policies."""

    # Required manifest fields
    REQUIRED_MANIFEST_FIELDS = ["id", "name", "version"]

    # Forbidden file operations (security policy)
    FORBIDDEN_OPERATIONS = [
        "open(",
        "os.remove(",
        "os.unlink(",
        "os.rmdir(",
        "os.mkdir(",
        "os.makedirs(",
        "os.rename(",
        "os.replace(",
        "shutil.rmtree(",
        "shutil.move(",
        "shutil.copy(",
        "pathlib.Path.unlink(",
        "pathlib.Path.mkdir(",
        "pathlib.Path.rename(",
    ]

    # Approved safe paths
    APPROVED_PATHS = ["/v1/state/"]

    def __init__(self, plugin_path: str):
        self.plugin_path = Path(plugin_path).resolve()
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self) -> dict[str, Any]:
        """Run all validation checks and return JSON report."""
        self.errors.clear()
        self.warnings.clear()

        # 1. Check if plugin directory exists
        if not self.plugin_path.exists():
            self.errors.append(f"Plugin directory does not exist: {self.plugin_path}")
            return self._build_report()

        if not self.plugin_path.is_dir():
            self.errors.append(f"Path is not a directory: {self.plugin_path}")
            return self._build_report()

        # 2. Validate manifest.json
        self._validate_manifest()

        # 3. Validate directory structure
        self._validate_structure()

        # 4. Static analysis of backend/main.py
        self._analyze_backend()

        return self._build_report()

    def _validate_manifest(self) -> None:
        """Check manifest.json for required fields."""
        manifest_path = self.plugin_path / "manifest.json"

        if not manifest_path.exists():
            self.errors.append("manifest.json not found")
            return

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"manifest.json is invalid JSON: {e}")
            return

        # Check required fields
        for field in self.REQUIRED_MANIFEST_FIELDS:
            if field not in manifest:
                self.errors.append(f"manifest.json missing required field: {field}")

        # Validate version format (semver-like)
        if "version" in manifest:
            version = manifest["version"]
            if not re.match(r"^\d+\.\d+\.\d+$", version):
                self.warnings.append(f"Version '{version}' does not match semver format (x.y.z)")

        # Check api_routes if present
        if "api_routes" in manifest:
            if not isinstance(manifest["api_routes"], dict):
                self.errors.append("api_routes must be an object (dictionary)")
            elif len(manifest["api_routes"]) == 0:
                self.warnings.append("api_routes is empty - plugin will have no endpoints")

        # Check UI definition if present
        if "ui" in manifest:
            ui = manifest["ui"]
            if not isinstance(ui, dict):
                self.errors.append("ui must be an object (dictionary)")
            else:
                # Check for required UI fields
                if "tab_id" not in ui:
                    self.warnings.append("ui missing 'tab_id' - may not appear in dashboard")
                if "entry" not in ui:
                    self.warnings.append("ui missing 'entry' - UI may not load")

    def _validate_structure(self) -> None:
        """Verify required directory structure."""
        # Check backend/main.py
        backend_main = self.plugin_path / "backend" / "main.py"
        if not backend_main.exists():
            self.errors.append("backend/main.py not found - required for plugin backend")
        elif not backend_main.is_file():
            self.errors.append("backend/main.py is not a file")

        # Check frontend/view.js
        frontend_view = self.plugin_path / "frontend" / "view.js"
        if not frontend_view.exists():
            self.errors.append("frontend/view.js not found - required for plugin UI")
        elif not frontend_view.is_file():
            self.errors.append("frontend/view.js is not a file")

    def _analyze_backend(self) -> None:
        """Static analysis for forbidden file operations."""
        backend_main = self.plugin_path / "backend" / "main.py"

        if not backend_main.exists():
            return  # Already reported in structure check

        try:
            with open(backend_main, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Failed to read backend/main.py: {e}")
            return

        plugin_id = self.plugin_path.name
        plugin_dir = str(self.plugin_path)

        # Check for forbidden operations
        for operation in self.FORBIDDEN_OPERATIONS:
            if operation in content:
                # Find the line for better error message
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    if operation in line:
                        # Check if there's a comment explaining the safe usage
                        if "# SECURE:" in line or "# SAFE:" in line:
                            continue
                        self._check_operation_safety(operation, line, plugin_dir, plugin_id)

    def _check_operation_safety(
        self, operation: str, line: str, plugin_dir: str, plugin_id: str
    ) -> None:
        """Check if a forbidden operation is used safely."""
        # Extract potential file path from the line
        # Look for string literals that might be paths

        # Check if the operation targets the plugin's own directory
        if f'"{plugin_dir}' in line or f"'{plugin_dir}" in line:
            # Check if it's truly within the plugin directory
            if plugin_dir in line:
                # Safe: operating within own directory
                return

        # Check for approved API paths
        for approved in self.APPROVED_PATHS:
            if approved in line:
                # Safe: using approved state API
                return

        # Check for state server usage (approved path)
        if "/v1/state/" in line or "state_manager" in line:
            # Check if it's using the state manager (approved)
            if "get_domain" in line or "update_domain" in line:
                return

        # If we get here, it's potentially unsafe
        self.errors.append(
            f"Forbidden file operation '{operation.strip('(')}' detected in backend/main.py "
            f"(line: {line.strip()[:60]}...). "
            f"Plugins must only use file operations within their own directory or use the /v1/state/ API."
        )

    def _build_report(self) -> dict[str, Any]:
        """Build the final JSON report."""
        status = "SUCCESS" if not self.errors else "FAILURE"

        return {
            "status": status,
            "plugin_path": str(self.plugin_path),
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": {
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
            },
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Project Genesis Core - Plugin Integrity Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/project-genesis-core/kernel/plugins/avatar
  %(prog)s ./kernel/plugins/vault --json
  %(prog)s ./plugins/my-plugin/
        """,
    )

    parser.add_argument(
        "plugin_path",
        help="Path to the plugin directory to validate",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (machine-readable)",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed error/warning messages",
    )

    args = parser.parse_args()

    # Run validation
    validator = IntegrityValidator(args.plugin_path)
    report = validator.validate()

    # Output
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        # Human-readable output
        print(f"\n{'='*60}")
        print(f"  Plugin Integrity Validator")
        print(f"{'='*60}")
        print(f"\nPlugin: {report['plugin_path']}")
        print(f"Status: {report['status']}")
        print(f"\nSummary: {report['summary']['error_count']} errors, {report['summary']['warning_count']} warnings")

        if report["errors"]:
            print(f"\n{'--'*30}")
            print("ERRORS:")
            for error in report["errors"]:
                print(f"  ✗ {error}")

        if report["warnings"]:
            print(f"\n{'--'*30}")
            print("WARNINGS:")
            for warning in report["warnings"]:
                print(f"  ⚠ {warning}")

        print(f"\n{'='*60}")

    # Exit with appropriate code
    sys.exit(0 if report["status"] == "SUCCESS" else 1)


if __name__ == "__main__":
    main()
