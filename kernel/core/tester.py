#!/usr/bin/env python3
"""
Multi-Plugin Test Runner for Project Genesis Core.

Discovers and runs tests for all active plugins in kernel/plugins/.
Looks for 'backend/tests.py' within each plugin directory.
Executes tests as separate processes and generates JSON reports.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# Constants
PLUGINS_DIR = Path(__file__).parent.parent / "plugins"
TEST_FILE = "tests.py"
BACKEND_DIR = "backend"


def discover_plugins(plugins_dir: Path) -> list[dict[str, str]]:
    """Discover all plugins in the plugins directory."""
    plugins = []

    if not plugins_dir.exists():
        print(f"Warning: Plugins directory not found: {plugins_dir}")
        return plugins

    for item in plugins_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            manifest_path = item / "manifest.json"
            plugin_id = item.name

            # Try to read plugin id from manifest
            if manifest_path.exists():
                try:
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                        plugin_id = manifest.get("id", item.name)
                except (json.JSONDecodeError, IOError):
                    pass

            plugins.append({
                "name": item.name,
                "id": plugin_id,
                "path": item
            })

    return sorted(plugins, key=lambda p: p["name"])


def find_test_file(plugin_path: Path) -> Path | None:
    """Find the tests.py file in the plugin's backend directory."""
    test_path = plugin_path / BACKEND_DIR / TEST_FILE
    if test_path.exists():
        return test_path
    return None


def run_test(test_path: Path, plugin_id: str, timeout: int = 60) -> dict[str, Any]:
    """
    Run a single test file as a separate process.

    Returns a dict with success status, output, and error message.
    """
    result = {
        "plugin_id": plugin_id,
        "success": False,
        "output": "",
        "error_message": "",
        "duration_ms": 0
    }

    start_time = datetime.now()

    try:
        proc = subprocess.Popen(
            [sys.executable, str(test_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=test_path.parent
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            result["error_message"] = f"Test timed out after {timeout} seconds"
            result["output"] = stdout
            return result

        end_time = datetime.now()
        result["duration_ms"] = int((end_time - start_time).total_seconds() * 1000)
        result["output"] = stdout
        result["error_message"] = stderr

        # Determine success based on exit code
        if proc.returncode == 0:
            result["success"] = True
        else:
            result["error_message"] = f"Exit code {proc.returncode}: {stderr}" if stderr else f"Exit code {proc.returncode}"

    except FileNotFoundError:
        result["error_message"] = f"Python interpreter not found: {sys.executable}"
    except PermissionError:
        result["error_message"] = f"Permission denied: {test_path}"
    except Exception as e:
        result["error_message"] = f"Error running test: {str(e)}"

    return result


def run_all_tests(plugins_dir: Path, verbose: bool = False, timeout: int = 60) -> dict[str, Any]:
    """
    Discover and run all plugin tests.

    Returns a comprehensive JSON report.
    """
    plugins = discover_plugins(plugins_dir)

    if verbose:
        print(f"Discovered {len(plugins)} plugins")

    results = {
        "timestamp": datetime.now().isoformat(),
        "plugins_dir": str(plugins_dir),
        "overall_status": "ALL_PASSED",
        "total_plugins": len(plugins),
        "plugins_tested": 0,
        "plugins_passed": 0,
        "plugins_failed": 0,
        "plugins_skipped": 0,
        "results": []
    }

    for plugin in plugins:
        plugin_id = plugin["id"]
        plugin_name = plugin["name"]
        plugin_path = plugin["path"]

        if verbose:
            print(f"\nTesting plugin: {plugin_name} ({plugin_id})")

        test_path = find_test_file(plugin_path)

        if test_path is None:
            if verbose:
                print(f"  -> No tests.py found, skipping")
            results["plugins_skipped"] += 1
            results["results"].append({
                "plugin_id": plugin_id,
                "plugin_name": plugin_name,
                "success": None,
                "output": "",
                "error_message": "No backend/tests.py found",
                "skipped": True,
                "duration_ms": 0
            })
            continue

        results["plugins_tested"] += 1

        if verbose:
            print(f"  -> Running: {test_path}")

        test_result = run_test(test_path, plugin_id, timeout)
        test_result["plugin_name"] = plugin_name

        results["results"].append(test_result)

        if test_result["success"]:
            results["plugins_passed"] += 1
            if verbose:
                print(f"  -> PASSED ({test_result['duration_ms']}ms)")
        else:
            results["plugins_failed"] += 1
            results["overall_status"] = "FAILURES_DETECTED"
            if verbose:
                print(f"  -> FAILED: {test_result['error_message']}")

    return results


def print_summary(results: dict[str, Any]) -> None:
    """Print a human-readable summary of the test results."""
    print("\n" + "=" * 60)
    print("MULTI-PLUGIN TEST RUNNER - SUMMARY")
    print("=" * 60)
    print(f"Timestamp:    {results['timestamp']}")
    print(f"Plugins Dir:  {results['plugins_dir']}")
    print("-" * 60)
    print(f"Total Plugins:    {results['total_plugins']}")
    print(f"Tests Run:        {results['plugins_tested']}")
    print(f"Passed:           {results['plugins_passed']}")
    print(f"Failed:           {results['plugins_failed']}")
    print(f"Skipped:          {results['plugins_skipped']}")
    print("-" * 60)
    print(f"OVERALL STATUS: {results['overall_status']}")
    print("=" * 60)

    # Show failed tests
    if results['plugins_failed'] > 0:
        print("\nFailed Plugins:")
        for r in results['results']:
            if not r.get('success', True):
                print(f"  - {r['plugin_id']}: {r.get('error_message', 'Unknown error')}")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Plugin Test Runner for Project Genesis Core",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         # Run all tests with default settings
  %(prog)s --verbose               # Show detailed output
  %(prog)s --output results.json    # Save JSON report to file
  %(prog)s --timeout 120           # Set timeout to 120 seconds per test
  %(prog)s --quiet                  # Only show summary and errors
        """
    )

    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=PLUGINS_DIR,
        help=f"Path to plugins directory (default: {PLUGINS_DIR})"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Path to save JSON report (default: print to stdout)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output during test execution"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only show summary (implies --summary)"
    )

    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=60,
        help="Timeout in seconds for each test (default: 60)"
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary after tests complete"
    )

    args = parser.parse_args()

    # Determine verbosity
    verbose = args.verbose or args.quiet

    # Run tests
    results = run_all_tests(args.plugins_dir, verbose=verbose, timeout=args.timeout)

    # Print summary
    if args.summary or args.quiet or args.verbose:
        print_summary(results)

    # Output JSON
    json_output = json.dumps(results, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json_output)
        print(f"\nJSON report saved to: {output_path}")
    else:
        print("\n" + json_output)

    # Exit with appropriate code
    if results["overall_status"] == "ALL_PASSED":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
