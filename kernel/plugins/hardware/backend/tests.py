"""
Hardware Plugin Tests
Tests for system resource monitoring and stress detection.
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add project root to sys.path for absolute imports
# Path: kernel/plugins/hardware/backend/tests.py -> backend -> hardware -> plugins -> kernel -> project_root
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Import HardwarePlugin from main.py
from kernel.plugins.hardware.backend.main import (
    HardwarePlugin,
    CPU_THRESHOLD,
    RAM_THRESHOLD,
    TEMP_THRESHOLD,
    get_cpu_usage,
    get_ram_usage,
    get_temperature
)


class TestHardwarePlugin(unittest.TestCase):
    """Test suite for HardwarePlugin."""

    def setUp(self):
        """Set up test fixtures with mocked kernel and state_manager."""
        # Mock kernel
        self.kernel = Mock()
        self.kernel.state_manager = Mock()

        # Mock state_manager methods
        self.kernel.state_manager.get_domain = Mock(return_value={})
        self.kernel.state_manager.update_domain = Mock()

        # Mock event_bus
        self.kernel.event_bus = Mock()
        self.kernel.event_bus.publish = Mock()

        # Create plugin instance
        self.plugin = HardwarePlugin()

    def test_initialize(self):
        """Test plugin initialization with kernel."""
        self.plugin.initialize(self.kernel)
        self.assertEqual(self.plugin.kernel, self.kernel)
        self.assertIsNone(self.plugin.last_stress_event)

    @patch('kernel.plugins.hardware.backend.main.get_cpu_usage')
    @patch('kernel.plugins.hardware.backend.main.get_ram_usage')
    @patch('kernel.plugins.hardware.backend.main.get_temperature')
    def test_monitor_resources_normal(self, mock_temp, mock_ram, mock_cpu):
        """Test resource monitoring with normal values (below thresholds)."""
        # Mock system resource readings
        mock_cpu.return_value = 50.0  # Below CPU_THRESHOLD (80.0)
        mock_ram.return_value = 60.0  # Below RAM_THRESHOLD (90.0)
        mock_temp.return_value = 50.0  # Below TEMP_THRESHOLD (85.0)

        self.plugin.initialize(self.kernel)
        self.plugin._monitor_resources()

        # Verify state was updated
        self.kernel.state_manager.update_domain.assert_called_once()
        call_args = self.kernel.state_manager.update_domain.call_args
        domain_name = call_args[0][0]
        self.assertEqual(domain_name, "hardware_resonance")

        # Verify no stress event was published
        self.kernel.event_bus.publish.assert_not_called()

    @patch('kernel.plugins.hardware.backend.main.get_cpu_usage')
    @patch('kernel.plugins.hardware.backend.main.get_ram_usage')
    @patch('kernel.plugins.hardware.backend.main.get_temperature')
    def test_monitor_resources_cpu_stress(self, mock_temp, mock_ram, mock_cpu):
        """Test stress detection when CPU exceeds threshold."""
        # Mock system resource readings - CPU over threshold
        mock_cpu.return_value = 95.0  # Above CPU_THRESHOLD (80.0)
        mock_ram.return_value = 50.0  # Below RAM_THRESHOLD
        mock_temp.return_value = 50.0  # Below TEMP_THRESHOLD

        self.plugin.initialize(self.kernel)
        self.plugin._monitor_resources()

        # Verify EVENT_HARDWARE_STRESS was published
        self.kernel.event_bus.publish.assert_called_once()
        call_args = self.kernel.event_bus.publish.call_args[0][0]
        self.assertEqual(call_args["event"], "EVENT_HARDWARE_STRESS")
        self.assertIn("cpu_high:95.0%", call_args["payload"]["reasons"])

    @patch('kernel.plugins.hardware.backend.main.get_cpu_usage')
    @patch('kernel.plugins.hardware.backend.main.get_ram_usage')
    @patch('kernel.plugins.hardware.backend.main.get_temperature')
    def test_monitor_resources_ram_stress(self, mock_temp, mock_ram, mock_cpu):
        """Test stress detection when RAM exceeds threshold."""
        # Mock system resource readings - RAM over threshold
        mock_cpu.return_value = 30.0
        mock_ram.return_value = 95.0  # Above RAM_THRESHOLD (90.0)
        mock_temp.return_value = 50.0

        self.plugin.initialize(self.kernel)
        self.plugin._monitor_resources()

        # Verify EVENT_HARDWARE_STRESS was published
        self.kernel.event_bus.publish.assert_called_once()
        call_args = self.kernel.event_bus.publish.call_args[0][0]
        self.assertEqual(call_args["event"], "EVENT_HARDWARE_STRESS")
        self.assertIn("ram_high:95.0%", call_args["payload"]["reasons"])

    @patch('kernel.plugins.hardware.backend.main.get_cpu_usage')
    @patch('kernel.plugins.hardware.backend.main.get_ram_usage')
    @patch('kernel.plugins.hardware.backend.main.get_temperature')
    def test_monitor_resources_temp_stress(self, mock_temp, mock_ram, mock_cpu):
        """Test stress detection when temperature exceeds threshold."""
        # Mock system resource readings - Temperature over threshold
        mock_cpu.return_value = 30.0
        mock_ram.return_value = 50.0
        mock_temp.return_value = 90.0  # Above TEMP_THRESHOLD (85.0)

        self.plugin.initialize(self.kernel)
        self.plugin._monitor_resources()

        # Verify EVENT_HARDWARE_STRESS was published
        self.kernel.event_bus.publish.assert_called_once()
        call_args = self.kernel.event_bus.publish.call_args[0][0]
        self.assertEqual(call_args["event"], "EVENT_HARDWARE_STRESS")
        self.assertIn("temp_high:90.0°C", call_args["payload"]["reasons"])

    @patch('kernel.plugins.hardware.backend.main.get_cpu_usage')
    @patch('kernel.plugins.hardware.backend.main.get_ram_usage')
    @patch('kernel.plugins.hardware.backend.main.get_temperature')
    def test_monitor_resources_multiple_stress(self, mock_temp, mock_ram, mock_cpu):
        """Test stress detection with multiple thresholds exceeded."""
        # Mock system resource readings - Multiple thresholds exceeded
        mock_cpu.return_value = 95.0  # Above CPU_THRESHOLD
        mock_ram.return_value = 95.0  # Above RAM_THRESHOLD
        mock_temp.return_value = 90.0  # Above TEMP_THRESHOLD

        self.plugin.initialize(self.kernel)
        self.plugin._monitor_resources()

        # Verify EVENT_HARDWARE_STRESS was published with multiple reasons
        self.kernel.event_bus.publish.assert_called_once()
        call_args = self.kernel.event_bus.publish.call_args[0][0]
        self.assertEqual(call_args["event"], "EVENT_HARDWARE_STRESS")
        reasons = call_args["payload"]["reasons"]
        self.assertEqual(len(reasons), 3)
        self.assertIn("cpu_high:95.0%", reasons)
        self.assertIn("ram_high:95.0%", reasons)
        self.assertIn("temp_high:90.0°C", reasons)

    def test_on_event_tick_minutelly(self):
        """Test on_event handles TICK_MINUTELY events."""
        self.plugin.initialize(self.kernel)

        with patch.object(self.plugin, '_monitor_resources') as mock_monitor:
            event = {"event": "TICK_MINUTELY"}
            self.plugin.on_event(event)
            mock_monitor.assert_called_once()

    def test_on_event_other_event(self):
        """Test on_event ignores non-TICK_MINUTELY events."""
        self.plugin.initialize(self.kernel)

        with patch.object(self.plugin, '_monitor_resources') as mock_monitor:
            event = {"event": "OTHER_EVENT"}
            self.plugin.on_event(event)
            mock_monitor.assert_not_called()

    def test_handle_get_stats(self):
        """Test handle_get_stats returns correct stats structure."""
        self.plugin.kernel = self.kernel
        self.kernel.state_manager.get_domain = Mock(return_value={"last_update": "2026-02-27T10:00:00"})

        with patch('kernel.plugins.hardware.backend.main.get_cpu_usage', return_value=50.0):
            with patch('kernel.plugins.hardware.backend.main.get_ram_usage', return_value=60.0):
                with patch('kernel.plugins.hardware.backend.main.get_temperature', return_value=55.0):
                    stats = self.plugin.handle_get_stats()

        self.assertEqual(stats["cpu_percent"], 50.0)
        self.assertEqual(stats["ram_percent"], 60.0)
        self.assertEqual(stats["temperature_celsius"], 55.0)
        self.assertEqual(stats["cpu_threshold"], CPU_THRESHOLD)
        self.assertEqual(stats["ram_threshold"], RAM_THRESHOLD)
        self.assertEqual(stats["temp_threshold"], TEMP_THRESHOLD)
        self.assertEqual(stats["status"], "ok")

    def test_stress_debounce(self):
        """Test that stress events are debounced (not published within 5 minutes)."""
        self.plugin.initialize(self.kernel)
        self.plugin.last_stress_event = datetime.now().isoformat()

        # Should not publish stress event due to debounce
        self.plugin._publish_stress_event(["cpu_high:95.0%"])
        self.kernel.event_bus.publish.assert_not_called()


class TestThresholdConstants(unittest.TestCase):
    """Test threshold constants are correctly defined."""

    def test_cpu_threshold(self):
        self.assertEqual(CPU_THRESHOLD, 80.0)

    def test_ram_threshold(self):
        self.assertEqual(RAM_THRESHOLD, 90.0)

    def test_temp_threshold(self):
        self.assertEqual(TEMP_THRESHOLD, 85.0)


if __name__ == "__main__":
    # Run tests
    result = unittest.main(verbosity=2, exit=False)
    if result.result.wasSuccessful():
        print("\n[HARDWARE TEST] PASSED")
        sys.exit(0)
    else:
        print("\n[HARDWARE TEST] FAILED")
        sys.exit(1)
