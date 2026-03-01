#!/usr/bin/env python3
"""
Developer Plugin Unit Tests - Code Proposal & Project Management
Tests the self-expansion engine for creating and validating code proposals.
"""

import sys
import os
import importlib.util
import tempfile
import shutil
from datetime import datetime

# Calculate paths
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PATH = os.path.join(TESTS_DIR, "main.py")


class MockStateManager:
    """Mock state manager with development_state domain."""
    def __init__(self):
        self._domains = {
            "development_state": {
                "projects": [],
                "last_proposal": None,
                "initialized_at": datetime.now().isoformat()
            }
        }

    def get_domain(self, domain):
        return self._domains.get(domain)

    def update_domain(self, domain, data):
        self._domains[domain] = data


class MockKernel:
    """Mock kernel with state_manager and base_path."""
    def __init__(self, temp_dir):
        self.state_manager = MockStateManager()
        self.base_path = temp_dir


def run_tests():
    """Run all DEVELOPER plugin tests."""
    # Create temporary directory for development folder
    temp_dir = tempfile.mkdtemp()
    dev_folder = os.path.join(temp_dir, "data", "development")
    os.makedirs(dev_folder, exist_ok=True)

    try:
        # Create mock kernel
        mock_kernel = MockKernel(temp_dir)

        # Load the plugin module directly
        spec = importlib.util.spec_from_file_location("developer_main", MAIN_PATH)
        developer_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(developer_main)

        # Get the plugin instance
        plugin = developer_main.plugin
        plugin.initialize(mock_kernel)

        # Test 1: handle_propose_code with valid Python code
        print("\n>>> Test 1: Valid Python code syntax check")
        valid_code = '''def hello_world():
    """A simple function."""
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
'''
        result = plugin.handle_propose_code({
            "filename": "valid_test.py",
            "content": valid_code,
            "description": "Test valid Python file"
        })

        assert result.get("success") == True, f"Expected success, got: {result}"
        assert result.get("validated") == True, "Should be validated as Python"
        print("[PASS] Valid Python code accepted")

        # Test 2: handle_propose_code with invalid Python code
        print("\n>>> Test 2: Invalid Python code error detection")
        invalid_code = '''def broken_function(
    print("This is broken")
'''
        result = plugin.handle_propose_code({
            "filename": "invalid_test.py",
            "content": invalid_code,
            "description": "Test invalid Python file"
        })

        assert result.get("success") == False, f"Expected failure, got: {result}"
        assert "Syntax error" in result.get("error", ""), f"Expected syntax error, got: {result}"
        assert result.get("line") is not None, "Should return line number"
        print(f"[PASS] Invalid Python code rejected (line {result.get('line')})")

        # Test 3: handle_list_projects scanning logic
        print("\n>>> Test 3: List projects scanning logic")

        # Create some test files in development folder (besides valid_test.py from test 1)
        with open(os.path.join(dev_folder, "project_b.js"), "w") as f:
            f.write("// JavaScript project")
        with open(os.path.join(dev_folder, "project_c.json"), "w") as f:
            f.write('{"test": true}')

        result = plugin.handle_list_projects()

        assert result.get("success") == True, f"Expected success, got: {result}"
        # Should have at least 3 projects: valid_test.py + project_b.js + project_c.json
        assert result.get("total") >= 3, f"Expected at least 3 projects, got: {result.get('total')}"

        projects = result.get("projects", [])
        types = [p.get("type") for p in projects]
        assert "python" in types, "Should find Python file"
        assert "javascript" in types, "Should find JavaScript file"
        assert "json" in types, "Should find JSON file"
        print(f"[PASS] Found {result.get('total')} projects with correct types")

        # Test 4: development_state domain is updated
        print("\n>>> Test 4: development_state domain update")
        dev_state = mock_kernel.state_manager.get_domain("development_state")

        assert dev_state is not None, "development_state should exist"
        projects_count = len(dev_state.get("projects", []))
        assert projects_count >= 1, f"Should have at least one project, got {projects_count}"

        last_proposal = dev_state.get("last_proposal")
        assert last_proposal is not None, "last_proposal should be set"
        assert last_proposal.get("filename") == "valid_test.py", "Last proposal should be valid_test.py"

        print("[PASS] development_state correctly updated")

        # Test 5: Verify project list contains our proposals
        print("\n>>> Test 5: Verify project entries in state")
        projects_in_state = dev_state.get("projects", [])

        valid_project = next((p for p in projects_in_state if p.get("name") == "valid_test.py"), None)
        assert valid_project is not None, "valid_test.py should be in projects"
        assert valid_project.get("description") == "Test valid Python file"
        assert valid_project.get("type") == "python"

        print("[PASS] Project entries contain correct metadata")

        print("\n" + "=" * 60)
        print("All DEVELOPER plugin tests passed!")
        print("[DEVELOPER TEST] PASSED")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"[FAIL] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] Test error: {e}")
        return 1
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(run_tests())
