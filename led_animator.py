"""
BabySynth - LED Animation Engine
Creates expressive visual feedback through dynamic LED animations.

Supports:
- Breathing/pulse animations
- Fade in/out effects
- Ripple effects (radial spread)
- Custom animation curves
- Non-blocking threaded animations
"""
import threading
import time
import math
from typing import Tuple, Callable, Optional, List
from enum import Enum


class AnimationCurve(Enum):
    """Animation easing functions."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    SINE = "sine"
    BOUNCE = "bounce"


class LEDAnimator:
    """
    Manages LED animations for expressive visual feedback.

    Features:
    - Non-blocking animations via threading
    - Multiple simultaneous animations
    - Configurable animation curves
    - Frame-based updates for smooth visuals
    """

    def __init__(self, launchpad, session_manager=None, web_broadcaster=None):
        self.lp = launchpad
        self.session_manager = session_manager
        self.web_broadcaster = web_broadcaster
        self.active_animations = {}  # {(x, y): animation_thread}
        self.animation_stop_flags = {}  # {(x, y): stop_flag}
        self.lock = threading.Lock()
        self.fps = 30  # Frames per second for animations
        self.frame_time = 1.0 / self.fps

    def stop_animation(self, x: int, y: int):
        """Stop any active animation for a button."""
        key = (x, y)
        with self.lock:
            if key in self.animation_stop_flags:
                self.animation_stop_flags[key].set()
                if key in self.active_animations:
                    # Wait for thread to finish (with timeout)
                    thread = self.active_animations[key]
                    thread.join(timeout=0.1)
                    del self.active_animations[key]
                del self.animation_stop_flags[key]

    def stop_all_animations(self):
        """Stop all active animations."""
        with self.lock:
            keys = list(self.animation_stop_flags.keys())
        for key in keys:
            self.stop_animation(key[0], key[1])

    def _set_led_color(self, x: int, y: int, color: Tuple[int, int, int]):
        """Set LED color and notify session manager."""
        led = self.lp.panel.led(x, y)
        led.color = color

        if self.web_broadcaster:
            self.web_broadcaster.update_led(x, y, color)

        if self.session_manager:
            self.session_manager.record_led_change(x, y, color)

    def _apply_curve(self, t: float, curve: AnimationCurve) -> float:
        """Apply easing curve to time value (0.0 to 1.0)."""
        if curve == AnimationCurve.LINEAR:
            return t
        elif curve == AnimationCurve.EASE_IN:
            return t * t
        elif curve == AnimationCurve.EASE_OUT:
            return 1 - (1 - t) * (1 - t)
        elif curve == AnimationCurve.EASE_IN_OUT:
            if t < 0.5:
                return 2 * t * t
            else:
                return 1 - 2 * (1 - t) * (1 - t)
        elif curve == AnimationCurve.SINE:
            return (math.sin(t * math.pi - math.pi/2) + 1) / 2
        elif curve == AnimationCurve.BOUNCE:
            if t < 0.5:
                return 2 * t
            else:
                return 2 - 2 * t
        return t

    def _interpolate_color(self, color1: Tuple[int, int, int],
                          color2: Tuple[int, int, int],
                          t: float) -> Tuple[int, int, int]:
        """Interpolate between two colors."""
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    # ========== BREATHING ANIMATION ==========

    def breathe(self, x: int, y: int, base_color: Tuple[int, int, int],
                period: float = 2.0, min_brightness: float = 0.3):
        """
        Create breathing/pulse effect - smooth sine wave brightness modulation.

        Perfect for sustained notes to show they're "alive".

        Args:
            x, y: Button position
            base_color: The base color to modulate
            period: Time for one complete breath cycle (seconds)
            min_brightness: Minimum brightness (0.0 to 1.0)
        """
        self.stop_animation(x, y)

        stop_flag = threading.Event()
        key = (x, y)

        with self.lock:
            self.animation_stop_flags[key] = stop_flag

        def animate():
            start_time = time.time()
            while not stop_flag.is_set():
                elapsed = time.time() - start_time
                phase = (elapsed % period) / period  # 0.0 to 1.0
                brightness = min_brightness + (1.0 - min_brightness) * (math.sin(phase * 2 * math.pi) + 1) / 2

                color = tuple(int(c * brightness) for c in base_color)
                self._set_led_color(x, y, color)

                time.sleep(self.frame_time)

        thread = threading.Thread(target=animate, daemon=True)
        with self.lock:
            self.active_animations[key] = thread
        thread.start()

    # ========== PULSE ANIMATION ==========

    def pulse(self, x: int, y: int, base_color: Tuple[int, int, int],
              duration: float = 0.5, max_brightness: float = 1.5):
        """
        Single pulse outward - brighten then return to base.

        Great for button press feedback.

        Args:
            x, y: Button position
            base_color: Starting color
            duration: Pulse duration (seconds)
            max_brightness: Peak brightness multiplier
        """
        self.stop_animation(x, y)

        stop_flag = threading.Event()
        key = (x, y)

        with self.lock:
            self.animation_stop_flags[key] = stop_flag

        def animate():
            start_time = time.time()
            while not stop_flag.is_set():
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    self._set_led_color(x, y, base_color)
                    break

                t = elapsed / duration
                # Pulse up then down
                brightness = 1.0 + (max_brightness - 1.0) * math.sin(t * math.pi)
                color = tuple(min(255, int(c * brightness)) for c in base_color)
                self._set_led_color(x, y, color)

                time.sleep(self.frame_time)

            with self.lock:
                if key in self.animation_stop_flags:
                    del self.animation_stop_flags[key]
                if key in self.active_animations:
                    del self.active_animations[key]

        thread = threading.Thread(target=animate, daemon=True)
        with self.lock:
            self.active_animations[key] = thread
        thread.start()

    # ========== FADE ANIMATION ==========

    def fade(self, x: int, y: int, from_color: Tuple[int, int, int],
             to_color: Tuple[int, int, int], duration: float = 0.5,
             curve: AnimationCurve = AnimationCurve.LINEAR):
        """
        Fade from one color to another.

        Args:
            x, y: Button position
            from_color: Starting color
            to_color: Ending color
            duration: Fade duration (seconds)
            curve: Animation easing curve
        """
        self.stop_animation(x, y)

        stop_flag = threading.Event()
        key = (x, y)

        with self.lock:
            self.animation_stop_flags[key] = stop_flag

        def animate():
            start_time = time.time()
            while not stop_flag.is_set():
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    self._set_led_color(x, y, to_color)
                    break

                t = self._apply_curve(elapsed / duration, curve)
                color = self._interpolate_color(from_color, to_color, t)
                self._set_led_color(x, y, color)

                time.sleep(self.frame_time)

            with self.lock:
                if key in self.animation_stop_flags:
                    del self.animation_stop_flags[key]
                if key in self.active_animations:
                    del self.active_animations[key]

        thread = threading.Thread(target=animate, daemon=True)
        with self.lock:
            self.active_animations[key] = thread
        thread.start()

    # ========== RIPPLE ANIMATION ==========

    def ripple(self, center_x: int, center_y: int, color: Tuple[int, int, int],
               radius: int = 3, duration: float = 0.8, fade_out: bool = True):
        """
        Create expanding ripple effect from center point.

        Beautiful for showing spatial relationships and impact.

        Args:
            center_x, center_y: Ripple origin
            color: Ripple color
            radius: Maximum ripple radius (in buttons)
            duration: Time for ripple to reach max radius
            fade_out: Whether colors fade as ripple expands
        """
        def animate():
            start_time = time.time()
            affected_buttons = set()

            # Calculate all buttons within max radius
            for y in range(9):
                for x in range(9):
                    distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                    if distance <= radius and distance > 0:
                        affected_buttons.add((x, y, distance))

            while True:
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    # Restore original colors (this is simplistic - ideally we'd track original state)
                    break

                t = elapsed / duration
                current_radius = radius * t

                for x, y, distance in affected_buttons:
                    if distance <= current_radius and distance >= current_radius - 1:
                        # This button is at the wavefront
                        brightness = 1.0
                        if fade_out:
                            brightness = 1.0 - (distance / radius)

                        ripple_color = tuple(int(c * brightness) for c in color)
                        self._set_led_color(x, y, ripple_color)

                time.sleep(self.frame_time)

        thread = threading.Thread(target=animate, daemon=True)
        thread.start()

    # ========== SPARKLE ANIMATION ==========

    def sparkle(self, x: int, y: int, base_color: Tuple[int, int, int],
                duration: float = 2.0, intensity: float = 0.5):
        """
        Random brightness variations - like a twinkling star.

        Args:
            x, y: Button position
            base_color: Base color
            duration: How long to sparkle (0 = infinite)
            intensity: How much brightness varies (0.0 to 1.0)
        """
        self.stop_animation(x, y)

        stop_flag = threading.Event()
        key = (x, y)

        with self.lock:
            self.animation_stop_flags[key] = stop_flag

        def animate():
            import random
            start_time = time.time()

            while not stop_flag.is_set():
                if duration > 0:
                    elapsed = time.time() - start_time
                    if elapsed >= duration:
                        self._set_led_color(x, y, base_color)
                        break

                # Random brightness flicker
                brightness = 1.0 + (random.random() * 2 - 1) * intensity
                color = tuple(max(0, min(255, int(c * brightness))) for c in base_color)
                self._set_led_color(x, y, color)

                time.sleep(0.05 + random.random() * 0.1)  # Variable timing for organic feel

            with self.lock:
                if key in self.animation_stop_flags:
                    del self.animation_stop_flags[key]
                if key in self.active_animations:
                    del self.active_animations[key]

        thread = threading.Thread(target=animate, daemon=True)
        with self.lock:
            self.active_animations[key] = thread
        thread.start()

    # ========== STROBE ANIMATION ==========

    def strobe(self, x: int, y: int, color: Tuple[int, int, int],
               frequency: float = 5.0, duration: float = 1.0):
        """
        Rapid on/off flashing.

        Args:
            x, y: Button position
            color: Strobe color
            frequency: Flashes per second
            duration: Total strobe duration
        """
        self.stop_animation(x, y)

        stop_flag = threading.Event()
        key = (x, y)

        with self.lock:
            self.animation_stop_flags[key] = stop_flag

        def animate():
            start_time = time.time()
            period = 1.0 / frequency

            while not stop_flag.is_set():
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    self._set_led_color(x, y, (0, 0, 0))
                    break

                # Toggle on/off
                phase = (elapsed % period) / period
                if phase < 0.5:
                    self._set_led_color(x, y, color)
                else:
                    self._set_led_color(x, y, (0, 0, 0))

                time.sleep(period / 2)

            with self.lock:
                if key in self.animation_stop_flags:
                    del self.animation_stop_flags[key]
                if key in self.active_animations:
                    del self.active_animations[key]

        thread = threading.Thread(target=animate, daemon=True)
        with self.lock:
            self.active_animations[key] = thread
        thread.start()

    # ========== WAVE ANIMATION ==========

    def wave(self, buttons: List[Tuple[int, int]], color: Tuple[int, int, int],
             period: float = 2.0, phase_offset: float = 0.2):
        """
        Create wave effect across multiple buttons.

        Perfect for sequences or chords.

        Args:
            buttons: List of (x, y) positions
            color: Wave color
            period: Time for one complete wave
            phase_offset: Phase delay between adjacent buttons
        """
        for i, (x, y) in enumerate(buttons):
            self.stop_animation(x, y)

        stop_flags = {}
        for i, (x, y) in enumerate(buttons):
            key = (x, y)
            stop_flag = threading.Event()
            stop_flags[key] = stop_flag
            with self.lock:
                self.animation_stop_flags[key] = stop_flag

        def animate():
            start_time = time.time()
            while True:
                # Check if any button wants to stop
                if any(flag.is_set() for flag in stop_flags.values()):
                    break

                elapsed = time.time() - start_time

                for i, (x, y) in enumerate(buttons):
                    if stop_flags[(x, y)].is_set():
                        continue

                    # Each button has phase offset
                    button_phase = (elapsed + i * phase_offset) % period / period
                    brightness = (math.sin(button_phase * 2 * math.pi) + 1) / 2

                    wave_color = tuple(int(c * brightness * 0.7 + c * 0.3) for c in color)
                    self._set_led_color(x, y, wave_color)

                time.sleep(self.frame_time)

            # Cleanup
            with self.lock:
                for x, y in buttons:
                    key = (x, y)
                    if key in self.animation_stop_flags:
                        del self.animation_stop_flags[key]
                    if key in self.active_animations:
                        del self.active_animations[key]

        thread = threading.Thread(target=animate, daemon=True)
        for x, y in buttons:
            with self.lock:
                self.active_animations[(x, y)] = thread
        thread.start()

    # ========== RAINBOW ANIMATION ==========

    def rainbow_cycle(self, x: int, y: int, period: float = 3.0):
        """
        Cycle through rainbow colors.

        Args:
            x, y: Button position
            period: Time for one complete rainbow cycle
        """
        self.stop_animation(x, y)

        stop_flag = threading.Event()
        key = (x, y)

        with self.lock:
            self.animation_stop_flags[key] = stop_flag

        def hsv_to_rgb(h, s, v):
            """Convert HSV to RGB (h in 0-360, s/v in 0-1)."""
            c = v * s
            x_val = c * (1 - abs((h / 60) % 2 - 1))
            m = v - c

            if h < 60:
                r, g, b = c, x_val, 0
            elif h < 120:
                r, g, b = x_val, c, 0
            elif h < 180:
                r, g, b = 0, c, x_val
            elif h < 240:
                r, g, b = 0, x_val, c
            elif h < 300:
                r, g, b = x_val, 0, c
            else:
                r, g, b = c, 0, x_val

            return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

        def animate():
            start_time = time.time()
            while not stop_flag.is_set():
                elapsed = time.time() - start_time
                hue = (elapsed / period * 360) % 360
                color = hsv_to_rgb(hue, 1.0, 1.0)
                self._set_led_color(x, y, color)
                time.sleep(self.frame_time)

            with self.lock:
                if key in self.animation_stop_flags:
                    del self.animation_stop_flags[key]
                if key in self.active_animations:
                    del self.active_animations[key]

        thread = threading.Thread(target=animate, daemon=True)
        with self.lock:
            self.active_animations[key] = thread
        thread.start()
