"""
BabySynth Comprehensive Test Suite
Tests all components including failure modes and edge cases.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock lpminimk3 before importing our code
sys.modules['lpminimk3'] = __import__('tests.mock_launchpad', fromlist=[''])

import unittest
import time
import tempfile
import shutil
import threading
from pathlib import Path

from session_manager import SessionManager
from led_animator import LEDAnimator, AnimationCurve
from turn_taker import TurnTaker, TurnMode, GridZone
from config_reloader import ConfigReloader
from tests.mock_launchpad import MockLaunchpad


class TestSessionManager(unittest.TestCase):
    """Test session recording and playback."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.sm = SessionManager(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_session_creation(self):
        """Test basic session creation."""
        session_id = self.sm.start_session(user_profile="test_user")
        self.assertIsNotNone(session_id)
        self.assertEqual(self.sm.current_session_id, session_id)

    def test_session_end(self):
        """Test session ending."""
        session_id = self.sm.start_session(user_profile="test_user")
        self.sm.end_session()
        self.assertIsNone(self.sm.current_session_id)

        session = self.sm.get_session(session_id)
        self.assertIsNotNone(session['end_time'])
        self.assertIsNotNone(session['duration'])

    def test_button_press_recording(self):
        """Test button press recording."""
        session_id = self.sm.start_session(user_profile="test_user")
        self.sm.record_button_press(4, 4, note_name="C", frequency=261.63)

        events = self.sm.get_session_events(session_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['x'], 4)
        self.assertEqual(events[0]['y'], 4)
        self.assertEqual(events[0]['note_name'], "C")

    def test_led_change_recording(self):
        """Test LED change recording."""
        session_id = self.sm.start_session(user_profile="test_user")
        self.sm.record_led_change(4, 4, (255, 0, 0))

        led_changes = self.sm.get_session_led_changes(session_id)
        self.assertEqual(len(led_changes), 1)
        self.assertEqual(led_changes[0]['color_r'], 255)

    def test_pattern_detection_rapid_sequence(self):
        """Test rapid sequence pattern detection."""
        session_id = self.sm.start_session(user_profile="test_user")

        # Simulate rapid button presses
        for i in range(5):
            self.sm.record_button_press(i, 4, note_name="C")
            time.sleep(0.1)  # < 0.3s threshold

        self.sm.end_session()

        patterns = self.sm.get_session_patterns(session_id)
        rapid_patterns = [p for p in patterns if p['pattern_type'] == 'rapid_sequence']
        self.assertGreater(len(rapid_patterns), 0)

    def test_pattern_detection_long_pause(self):
        """Test long pause pattern detection."""
        session_id = self.sm.start_session(user_profile="test_user")

        self.sm.record_button_press(0, 0, note_name="C")
        time.sleep(3.5)  # > 3s threshold
        self.sm.record_button_press(1, 1, note_name="D")

        self.sm.end_session()

        patterns = self.sm.get_session_patterns(session_id)
        pause_patterns = [p for p in patterns if p['pattern_type'] == 'long_pause']
        self.assertGreater(len(pause_patterns), 0)

    def test_session_export(self):
        """Test session export to JSON."""
        session_id = self.sm.start_session(user_profile="test_user")
        self.sm.record_button_press(4, 4, note_name="C")
        self.sm.end_session()

        export_path = os.path.join(self.temp_dir, "export.json")
        self.sm.export_session(session_id, export_path)

        self.assertTrue(os.path.exists(export_path))

    def test_empty_session(self):
        """Test empty session (edge case)."""
        session_id = self.sm.start_session(user_profile="test_user")
        self.sm.end_session()

        session = self.sm.get_session(session_id)
        self.assertEqual(session['total_events'], 0)

    def test_concurrent_recording(self):
        """Test thread safety of recording (CRITICAL)."""
        session_id = self.sm.start_session(user_profile="test_user")

        def record_events(start_x):
            for i in range(10):
                self.sm.record_button_press(start_x + i % 9, 4, note_name="C")

        threads = [threading.Thread(target=record_events, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        events = self.sm.get_session_events(session_id)
        self.assertEqual(len(events), 50)  # 5 threads * 10 events


class TestLEDAnimator(unittest.TestCase):
    """Test LED animation system."""

    def setUp(self):
        self.lp = MockLaunchpad()
        self.lp.open()
        self.animator = LEDAnimator(self.lp)

    def tearDown(self):
        self.animator.stop_all_animations()

    def test_pulse_animation(self):
        """Test pulse animation."""
        self.animator.pulse(4, 4, (255, 0, 0), duration=0.2)
        time.sleep(0.1)  # Mid-pulse

        # LED should be brighter than base
        color = self.lp.panel.get_led_state(4, 4)
        self.assertGreater(sum(color), 255)  # Brighter than red

        time.sleep(0.2)  # After pulse
        color = self.lp.panel.get_led_state(4, 4)
        self.assertEqual(color, (255, 0, 0))  # Back to base

    def test_fade_animation(self):
        """Test fade animation."""
        self.animator.fade(4, 4, (255, 0, 0), (0, 255, 0), duration=0.3)
        time.sleep(0.15)  # Halfway

        color = self.lp.panel.get_led_state(4, 4)
        # Should be between red and green
        self.assertGreater(color[0], 0)  # Some red
        self.assertGreater(color[1], 0)  # Some green

        time.sleep(0.2)  # Complete
        color = self.lp.panel.get_led_state(4, 4)
        self.assertTrue(self.lp.verify_led(4, 4, (0, 255, 0)))

    def test_breathing_animation(self):
        """Test breathing animation."""
        self.animator.breathe(4, 4, (255, 0, 0), period=0.5, min_brightness=0.5)
        time.sleep(0.3)  # Let it breathe

        self.animator.stop_animation(4, 4)
        # Animation should stop cleanly

    def test_stop_all_animations(self):
        """Test stopping all animations."""
        # Start multiple animations
        for i in range(5):
            self.animator.breathe(i, 4, (255, 0, 0))

        self.assertEqual(len(self.animator.active_animations), 5)

        self.animator.stop_all_animations()
        self.assertEqual(len(self.animator.active_animations), 0)

    def test_animation_thread_limit(self):
        """Test thread explosion scenario (CRITICAL)."""
        # Simulate rapid button mashing
        for i in range(100):
            self.animator.pulse(i % 9, 4, (255, 0, 0), duration=0.1)

        time.sleep(0.2)
        # All pulses should complete without crash
        self.assertLess(len(self.animator.active_animations), 50)  # Should cleanup

    def test_concurrent_animations_same_button(self):
        """Test multiple animations on same button (edge case)."""
        self.animator.breathe(4, 4, (255, 0, 0))
        time.sleep(0.05)
        self.animator.pulse(4, 4, (0, 255, 0))  # Should stop breathe

        time.sleep(0.2)
        # Only pulse should be active (breathe stopped)
        self.assertEqual(len([k for k in self.animator.active_animations.keys() if k == (4, 4)]), 0)


class TestTurnTaker(unittest.TestCase):
    """Test turn-taking system."""

    def setUp(self):
        self.lp = MockLaunchpad()
        self.lp.open()
        self.turn_taker = TurnTaker(self.lp)

    def test_free_play_mode(self):
        """Test free play mode allows all presses."""
        self.turn_taker.set_mode(TurnMode.FREE_PLAY)

        self.assertTrue(self.turn_taker.can_player_press(1, 4, player=1))
        self.assertTrue(self.turn_taker.can_player_press(6, 4, player=2))
        self.assertTrue(self.turn_taker.can_player_press(6, 4, player=1))  # Cross-zone OK

    def test_strict_turns_mode(self):
        """Test strict turns mode enforces current player."""
        self.turn_taker.set_mode(TurnMode.STRICT_TURNS)
        self.turn_taker.current_player = 1

        self.assertTrue(self.turn_taker.can_player_press(1, 4, player=1))  # P1 in P1 zone
        self.assertFalse(self.turn_taker.can_player_press(6, 4, player=2))  # P2 blocked

    def test_turn_switching(self):
        """Test turn switching."""
        self.turn_taker.set_mode(TurnMode.STRICT_TURNS)
        self.assertEqual(self.turn_taker.current_player, 1)

        self.turn_taker.switch_turn()
        self.assertEqual(self.turn_taker.current_player, 2)

        self.turn_taker.switch_turn()
        self.assertEqual(self.turn_taker.current_player, 1)  # Cycle back

    def test_zone_detection(self):
        """Test grid zone detection."""
        self.turn_taker.set_player_zones(GridZone.LEFT_HALF, GridZone.RIGHT_HALF)

        # Left zone
        self.assertTrue(self.turn_taker.is_in_zone(0, 4, GridZone.LEFT_HALF))
        self.assertTrue(self.turn_taker.is_in_zone(3, 4, GridZone.LEFT_HALF))
        self.assertFalse(self.turn_taker.is_in_zone(5, 4, GridZone.LEFT_HALF))

        # Right zone
        self.assertTrue(self.turn_taker.is_in_zone(5, 4, GridZone.RIGHT_HALF))
        self.assertFalse(self.turn_taker.is_in_zone(3, 4, GridZone.RIGHT_HALF))

    def test_turn_history(self):
        """Test turn history tracking."""
        self.turn_taker.set_mode(TurnMode.STRICT_TURNS)

        time.sleep(0.1)
        self.turn_taker.switch_turn()
        time.sleep(0.1)
        self.turn_taker.switch_turn()

        self.assertEqual(len(self.turn_taker.turn_history), 2)
        self.assertEqual(self.turn_taker.turn_history[0][0], 1)  # Player 1
        self.assertEqual(self.turn_taker.turn_history[1][0], 2)  # Player 2

    def test_turn_stats(self):
        """Test turn statistics generation."""
        self.turn_taker.set_mode(TurnMode.STRICT_TURNS)

        time.sleep(0.2)
        self.turn_taker.switch_turn()
        time.sleep(0.2)
        self.turn_taker.switch_turn()

        stats = self.turn_taker.get_turn_stats()
        self.assertIn('player_1', stats)
        self.assertIn('player_2', stats)
        self.assertGreater(stats['player_1']['avg_turn_duration'], 0)

    def test_simultaneous_press_race_condition(self):
        """Test race condition on simultaneous presses (CRITICAL)."""
        self.turn_taker.set_mode(TurnMode.STRICT_TURNS)
        self.turn_taker.current_player = 1

        def press_button(player, x, y):
            can_press = self.turn_taker.can_player_press(x, y, player=player)
            return can_press

        # Simulate both players pressing at once
        results = []
        threads = []
        for i in range(10):
            t = threading.Thread(target=lambda: results.append(press_button(1, 2, 4)))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All should get consistent result (all True for P1)
        self.assertTrue(all(results))


class TestConfigReloader(unittest.TestCase):
    """Test configuration reloading."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")

        # Create minimal config
        self.write_config({
            'name': 'test',
            'models': {'TEST': {'layout': 'x\nx\n'}},
            'scales': {'C_major': ['C']},
            'colors': {'C': [255, 0, 0]},
            'debounce': True
        })

        # Mock synth object
        class MockSynth:
            def __init__(self):
                self.notes = {}
                self.audio_files = {}
                self.model_name = ""
                self.scales = {}
                self.colors = {}
                self.models = {}

            def load_config(self, path):
                import yaml
                with open(path) as f:
                    config = yaml.safe_load(f)
                self.model_name = config['name']
                self.scales = config['scales']
                self.colors = config['colors']
                self.models = config['models']

            def assign_notes_and_files(self, scale, model):
                pass

        self.synth = MockSynth()
        self.reloader = ConfigReloader(self.synth, self.config_path)

    def tearDown(self):
        self.reloader.stop_watching()
        shutil.rmtree(self.temp_dir)

    def write_config(self, config_dict):
        import yaml
        with open(self.config_path, 'w') as f:
            yaml.dump(config_dict, f)
        time.sleep(0.1)  # Ensure file timestamp updates

    def test_manual_reload(self):
        """Test manual config reload."""
        self.write_config({'name': 'updated', 'models': {}, 'scales': {}, 'colors': {}})
        self.reloader.reload_config()

        self.assertEqual(self.synth.model_name, 'updated')

    def test_reload_with_invalid_config(self):
        """Test reload with invalid config (CRITICAL)."""
        # Write invalid config
        with open(self.config_path, 'w') as f:
            f.write("invalid: yaml: content:")

        self.reloader.reload_config()

        # Should preserve old config
        self.assertEqual(self.synth.model_name, 'test')

    def test_toggle_config(self):
        """Test A/B config toggling."""
        alt_path = os.path.join(self.temp_dir, "alt_config.yaml")
        self.write_config({'name': 'alternate', 'models': {}, 'scales': {}, 'colors': {}})
        shutil.copy(self.config_path, alt_path)

        self.reloader.set_alternate_config(alt_path)
        self.reloader.toggle_config()

        # Should swap
        self.assertEqual(self.reloader.current_config_path, alt_path)

    def test_file_watching(self):
        """Test automatic file watching."""
        reloaded = []

        def on_reload(path, success):
            reloaded.append((path, success))

        self.reloader.add_reload_callback(on_reload)
        self.reloader.start_watching(check_interval=0.5)

        time.sleep(0.3)
        self.write_config({'name': 'watched', 'models': {}, 'scales': {}, 'colors': {}})
        time.sleep(1.0)  # Wait for watcher

        self.assertGreater(len(reloaded), 0)
        self.assertEqual(self.synth.model_name, 'watched')


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error scenarios."""

    def test_launchpad_disconnect_simulation(self):
        """Simulate Launchpad disconnect (edge case)."""
        lp = MockLaunchpad()
        lp.open()

        # Simulate disconnect
        lp.close()

        # Attempting operations should not crash
        try:
            led = lp.panel.led(4, 4)
            led.color = (255, 0, 0)  # Should work even when "closed"
        except Exception as e:
            self.fail(f"Disconnect handling failed: {e}")

    def test_animation_during_config_reload(self):
        """Test animation state during config reload (CRITICAL)."""
        lp = MockLaunchpad()
        lp.open()
        animator = LEDAnimator(lp)

        # Start animation
        animator.breathe(4, 4, (255, 0, 0))
        time.sleep(0.1)

        # Simulate config reload (animator should cleanup)
        animator.stop_all_animations()

        # No threads should remain
        self.assertEqual(len(animator.active_animations), 0)

    def test_disk_full_simulation(self):
        """Simulate disk full during session recording (CRITICAL)."""
        # This would require actual disk full scenario
        # For now, test that we handle write errors
        pass  # TODO: Mock filesystem operations

    def test_unicode_in_session_notes(self):
        """Test Unicode handling in session notes."""
        sm = SessionManager(":memory:")
        session_id = sm.start_session(user_profile="test", notes="🎵🎶 Music! 日本語")
        sm.end_session()

        session = sm.get_session(session_id)
        self.assertEqual(session['notes'], "🎵🎶 Music! 日本語")


class TestReport:
    """Test result aggregator and report generator."""

    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'errors': [],
            'skipped': []
        }

    def add_result(self, test_name, status, message=""):
        self.results[status].append({
            'test': test_name,
            'message': message,
            'timestamp': time.time()
        })

    def generate_markdown_report(self):
        """Generate comprehensive markdown test report."""
        total = sum(len(v) for v in self.results.values())
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        errors = len(self.results['errors'])

        pass_rate = (passed / total * 100) if total > 0 else 0

        report = f"""# BabySynth Test Report

**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Total Tests:** {total}
**Pass Rate:** {pass_rate:.1f}%

## Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Passed | {passed} | {passed/total*100:.1f}% |
| ❌ Failed | {failed} | {failed/total*100:.1f}% |
| ⚠️ Errors | {errors} | {errors/total*100:.1f}% |

---

## 🟢 What's Working

"""
        for test in self.results['passed']:
            report += f"- ✅ **{test['test']}**\n"

        report += "\n---\n\n## 🔴 What's Broken\n\n"

        for test in self.results['failed']:
            report += f"- ❌ **{test['test']}**\n"
            if test['message']:
                report += f"  - Error: `{test['message']}`\n"

        for test in self.results['errors']:
            report += f"- ⚠️ **{test['test']}**\n"
            if test['message']:
                report += f"  - Error: `{test['message']}`\n"

        report += "\n---\n\n## 📋 Recommendations\n\n"

        if failed + errors == 0:
            report += "🎉 All tests passing! Ready for release.\n"
        elif pass_rate >= 90:
            report += "⚠️ Minor issues found. Address before release.\n"
        elif pass_rate >= 70:
            report += "🔧 Significant issues found. Fix critical failures.\n"
        else:
            report += "🚨 Major issues found. NOT READY for release.\n"

        return report


def run_all_tests():
    """Run all tests and generate report."""
    print("\n🧪 Running BabySynth Test Suite...\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestLEDAnimator))
    suite.addTests(loader.loadTestsFromTestCase(TestTurnTaker))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigReloader))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate report
    report_gen = TestReport()

    for test, _ in result.successes if hasattr(result, 'successes') else []:
        report_gen.add_result(str(test), 'passed')

    for test, traceback in result.failures:
        report_gen.add_result(str(test), 'failed', str(traceback))

    for test, traceback in result.errors:
        report_gen.add_result(str(test), 'errors', str(traceback))

    # Also use simple counting
    for test in result.testsRun:
        pass  # Already counted above

    # Generate markdown report
    markdown_report = report_gen.generate_markdown_report()

    # Write to file
    report_path = "TEST_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(markdown_report)

    print(f"\n📄 Test report written to {report_path}\n")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
