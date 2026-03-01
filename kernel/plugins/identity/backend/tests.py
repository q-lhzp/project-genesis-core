#!/usr/bin/env python3
"""
Identity Plugin Unit Tests - Soul Evolution Pipeline
Tests the Identity Engine and Soul Validator logic.
"""

import sys
import os
import json
import tempfile
import importlib.util
from datetime import datetime
from unittest.mock import MagicMock, patch

# Calculate paths
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PATH = os.path.join(TESTS_DIR, "main.py")


class MockStateManager:
    """Mock state manager."""
    def __init__(self):
        pass

    def get_domain(self, domain):
        return {}

    def update_domain(self, domain, data):
        pass


class MockKernel:
    """Mock kernel with state_manager."""
    def __init__(self):
        self.state_manager = MockStateManager()
        self.workspace = tempfile.mkdtemp()


# Create mock kernel
mock_kernel = MockKernel()

# Load the plugin module directly
spec = importlib.util.spec_from_file_location("identity_main", MAIN_PATH)
identity_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity_main)

# Override the plugin's kernel reference
identity_main.plugin.kernel = mock_kernel
identity_main.plugin.workspace = mock_kernel.workspace
identity_main.plugin.data_dir = os.path.join(mock_kernel.workspace, 'memory')


def test_soul_validator_parses_soul():
    """Test that SoulValidator can parse a valid SOUL.md file."""
    # Create temporary SOUL.md
    soul_content = """## Personality
- Creative thinker [CORE]
- Analytical [MUTABLE]

## Philosophy
- Continuous growth [CORE]

## Boundaries
- Privacy respected [CORE]

## Continuity
- Long-term memory maintained [CORE]
"""

    soul_path = os.path.join(mock_kernel.workspace, "SOUL.md")
    with open(soul_path, "w") as f:
        f.write(soul_content)

    # Parse
    result = identity_main.SoulValidator.parse_soul(soul_path)

    assert result is not None, "Should parse successfully"
    assert len(result["sections"]) >= 4, "Should have 4 sections"
    assert len(result["bullets"]) > 0, "Should have bullets"

    print(f"[TEST] Parsed {len(result['sections'])} sections, {len(result['bullets'])} bullets")
    print("[PASS] SoulValidator parses SOUL.md correctly")


def test_soul_validator_validates_structure():
    """Test that SoulValidator detects missing sections."""
    # Create incomplete SOUL.md
    soul_content = """## Personality
- Only personality [CORE]
"""

    soul_path = os.path.join(mock_kernel.workspace, "SOUL_INVALID.md")
    with open(soul_path, "w") as f:
        f.write(soul_content)

    # Validate
    result = identity_main.SoulValidator.validate(soul_path)

    assert result["status"] == "FAIL", "Should fail validation"
    assert len(result["errors"]) > 0, "Should have errors"

    print(f"[TEST] Validation errors: {len(result['errors'])}")
    print("[PASS] SoulValidator detects missing sections")


def test_soul_validator_validates_tags():
    """Test that SoulValidator requires tags on bullets."""
    # Create SOUL.md with untagged bullet
    soul_content = """## Personality
- Untagged bullet

## Philosophy
- Has tag [CORE]

## Boundaries
- Privacy [CORE]

## Continuity
- Memory [CORE]
"""

    soul_path = os.path.join(mock_kernel.workspace, "SOUL_NOTAG.md")
    with open(soul_path, "w") as f:
        f.write(soul_content)

    # Validate
    result = identity_main.SoulValidator.validate(soul_path)

    assert result["status"] == "FAIL", "Should fail validation"
    # Should have error about missing tag
    errors = [e for e in result["errors"] if "tag" in e.get("field", "")]
    assert len(errors) > 0, "Should have tag errors"

    print(f"[TEST] Tag errors found: {len(errors)}")
    print("[PASS] SoulValidator requires [CORE] or [MUTABLE] tags")


def test_proposal_validator_validates_format():
    """Test ProposalValidator checks proposal format."""
    # Create test proposal
    proposal = {
        "id": "PROP-20260227-001",
        "tag": "[MUTABLE]",
        "change_type": "add",
        "proposed_content": "- New trait [MUTABLE]",
        "target_section": "## Personality"
    }

    # Write proposal
    prop_path = os.path.join(mock_kernel.workspace, "proposals.jsonl")
    with open(prop_path, "w") as f:
        f.write(json.dumps(proposal) + "\n")

    # Create minimal SOUL
    soul_path = os.path.join(mock_kernel.workspace, "SOUL.md")
    with open(soul_path, "w") as f:
        f.write("## Personality\n- Existing [CORE]\n## Philosophy\n## Boundaries\n## Continuity\n")

    # Validate
    result = identity_main.ProposalValidator.validate(prop_path, soul_path)

    assert result["status"] == "PASS", f"Valid proposal should pass: {result}"

    print("[PASS] ProposalValidator validates proposal format")


def test_proposal_validator_blocks_core():
    """Test ProposalValidator blocks [CORE] modifications."""
    # Create proposal targeting CORE
    proposal = {
        "id": "PROP-20260227-002",
        "tag": "[CORE]",  # Invalid - can't modify CORE
        "change_type": "modify",
        "current_content": "- Existing [CORE]",
        "proposed_content": "- Modified [CORE]",
        "target_section": "## Personality"
    }

    prop_path = os.path.join(mock_kernel.workspace, "proposals_core.jsonl")
    with open(prop_path, "w") as f:
        f.write(json.dumps(proposal) + "\n")

    soul_path = os.path.join(mock_kernel.workspace, "SOUL.md")
    with open(soul_path, "w") as f:
        f.write("## Personality\n- Existing [CORE]\n## Philosophy\n## Boundaries\n## Continuity\n")

    result = identity_main.ProposalValidator.validate(prop_path, soul_path)

    assert result["status"] == "FAIL", "Should fail - CORE cannot be modified"
    core_errors = [e for e in result["errors"] if "CORE" in e.get("message", "")]
    assert len(core_errors) > 0, "Should have CORE error"

    print("[PASS] ProposalValidator blocks [CORE] modifications")


def test_reflection_validator():
    """Test ReflectionValidator validates reflection JSON."""
    # Create valid reflection
    reflection = {
        "id": "REF-20260227-001",
        "timestamp": datetime.now().isoformat(),
        "type": "routine_batch",
        "experience_ids": ["EXP-001", "EXP-002"],
        "summary": "Daily reflection",
        "insights": ["Insight 1"],
        "proposal_decision": {
            "should_propose": False,
            "triggers_fired": []
        },
        "proposals": []
    }

    ref_path = os.path.join(mock_kernel.workspace, "reflection.json")
    with open(ref_path, "w") as f:
        json.dump(reflection, f)

    result = identity_main.ReflectionValidator.validate(ref_path)

    assert result["status"] == "PASS", f"Valid reflection should pass: {result}"

    print("[PASS] ReflectionValidator validates reflection JSON")


def test_identity_plugin_initializes():
    """Test that IdentityPlugin initializes correctly."""
    assert identity_main.plugin.kernel is not None, "Plugin should have kernel"
    assert identity_main.plugin.workspace is not None, "Plugin should have workspace"

    print("[PASS] IdentityPlugin initializes with workspace")


def main():
    """Run all IDENTITY plugin tests."""
    print("=" * 60)
    print("IDENTITY PLUGIN - SOUL EVOLUTION TESTS")
    print("=" * 60)

    tests = [
        test_soul_validator_parses_soul,
        test_soul_validator_validates_structure,
        test_soul_validator_validates_tags,
        test_proposal_validator_validates_format,
        test_proposal_validator_blocks_core,
        test_reflection_validator,
        test_identity_plugin_initializes,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            print(f"\n>>> Running: {test.__name__}")
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n[SUCCESS] All IDENTITY Soul Evolution tests passed!")
        print("[IDENTITY TEST] PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
