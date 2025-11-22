"""
Mock Launchpad for Testing
Simulates Launchpad Mini MK3 without hardware.
"""
from enum import Enum
from typing import List, Tuple, Optional
import time
import threading


class Mode(Enum):
    """Launchpad modes."""
    PROG = "programmer"
    LIVE = "live"


class ButtonEvent:
    """Mock button event."""
    PRESS = "press"
    RELEASE = "release"

    def __init__(self, button, event_type):
        self.button = button
        self.type = event_type


class MockButton:
    """Mock button."""
    def __init__(self, x, y):
        self.x = x
        self.y = y


class MockLED:
    """Mock LED with color state."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._color = (0, 0, 0)
        self.color_history = []  # Track all color changes

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.color_history.append((time.time(), value))


class MockPanel:
    """Mock panel with LEDs and buttons."""
    def __init__(self):
        self._leds = {}
        for x in range(9):
            for y in range(9):
                self._leds[(x, y)] = MockLED(x, y)

        self._event_queue = []
        self._lock = threading.Lock()

    def led(self, x, y):
        """Get LED at position."""
        return self._leds.get((x, y))

    def buttons(self):
        """Return button manager."""
        return MockButtonManager(self)

    def inject_event(self, x, y, event_type):
        """Inject a button event for testing."""
        with self._lock:
            button = MockButton(x, y)
            event = ButtonEvent(button, event_type)
            self._event_queue.append(event)

    def get_led_state(self, x, y):
        """Get current LED color."""
        led = self.led(x, y)
        return led.color if led else None

    def get_all_led_states(self):
        """Get all LED states as dict."""
        return {(x, y): led.color for (x, y), led in self._leds.items()}

    def get_led_history(self, x, y):
        """Get color change history for LED."""
        led = self.led(x, y)
        return led.color_history if led else []


class MockButtonManager:
    """Mock button event manager."""
    def __init__(self, panel):
        self.panel = panel

    def poll_for_event(self):
        """Poll for next button event."""
        with self.panel._lock:
            if self.panel._event_queue:
                return self.panel._event_queue.pop(0)
        return None


class MockLaunchpad:
    """Mock Launchpad Mini MK3."""
    def __init__(self):
        self.panel = MockPanel()
        self.mode = None
        self.is_open = False

    def open(self):
        """Open connection (no-op for mock)."""
        self.is_open = True

    def close(self):
        """Close connection (no-op for mock)."""
        self.is_open = False

    # Test helpers
    def press_button(self, x, y):
        """Simulate button press."""
        self.panel.inject_event(x, y, ButtonEvent.PRESS)

    def release_button(self, x, y):
        """Simulate button release."""
        self.panel.inject_event(x, y, ButtonEvent.RELEASE)

    def press_and_release(self, x, y, hold_time=0.1):
        """Simulate press and release with delay."""
        self.press_button(x, y)
        time.sleep(hold_time)
        self.release_button(x, y)

    def get_grid_state(self):
        """Get current LED grid as ASCII."""
        lines = []
        for y in range(9):
            row = ""
            for x in range(9):
                color = self.panel.get_led_state(x, y)
                if color and sum(color) > 0:
                    row += "█"
                else:
                    row += "·"
            lines.append(row)
        return "\n".join(lines)

    def verify_led(self, x, y, expected_color, tolerance=5):
        """Verify LED is at expected color (within tolerance)."""
        actual = self.panel.get_led_state(x, y)
        if actual is None:
            return False

        for i in range(3):
            if abs(actual[i] - expected_color[i]) > tolerance:
                return False
        return True


def find_launchpads():
    """Mock find_launchpads - returns single mock Launchpad."""
    return [MockLaunchpad()]
