#!/usr/bin/env python3
"""
BabySynth - Animation Showcase
Demonstrates all LED animation effects.

This is a visual demo that shows off the expressive capabilities
of the LED animation system.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from lpminimk3 import find_launchpads, Mode, ButtonEvent
from led_animator import LEDAnimator


def main():
    print("\n🎨 BabySynth Animation Showcase")
    print("================================\n")

    # Initialize Launchpad
    launchpads = find_launchpads()
    if not launchpads:
        print("❌ No Launchpad found. Please connect your Launchpad Mini MK3.")
        sys.exit(1)

    lp = launchpads[0]
    lp.open()
    lp.mode = Mode.PROG

    # Clear grid
    for x in range(9):
        for y in range(9):
            lp.panel.led(x, y).color = (0, 0, 0)

    animator = LEDAnimator(lp)

    try:
        # ===== DEMO 1: BREATHING ANIMATION =====
        print("🫁 Demo 1: Breathing Animation")
        print("   Smooth sine-wave brightness modulation")
        print("   Perfect for sustained notes\n")

        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
        ]

        for i, color in enumerate(colors):
            animator.breathe(2 + i, 4, color, period=2.0, min_brightness=0.3)

        time.sleep(6)
        animator.stop_all_animations()
        print("   ✓ Complete\n")

        # ===== DEMO 2: PULSE ANIMATION =====
        print("💥 Demo 2: Pulse Animation")
        print("   Quick burst of brightness")
        print("   Great for button press feedback\n")

        for y in range(2, 7):
            animator.pulse(4, y, (255, 100, 200), duration=0.5, max_brightness=2.0)
            time.sleep(0.2)

        time.sleep(1)
        print("   ✓ Complete\n")

        # ===== DEMO 3: FADE ANIMATION =====
        print("🌈 Demo 3: Fade Animation")
        print("   Smooth color transitions")
        print("   Perfect for state changes\n")

        # Fade through rainbow
        rainbow_colors = [
            (255, 0, 0),    # Red
            (255, 127, 0),  # Orange
            (255, 255, 0),  # Yellow
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (148, 0, 211),  # Purple
        ]

        x, y = 4, 4
        for i in range(len(rainbow_colors) - 1):
            animator.fade(x, y, rainbow_colors[i], rainbow_colors[i + 1], duration=0.8)
            time.sleep(1.0)

        animator.fade(x, y, rainbow_colors[-1], (0, 0, 0), duration=0.5)
        time.sleep(0.6)
        print("   ✓ Complete\n")

        # ===== DEMO 4: RIPPLE ANIMATION =====
        print("🌊 Demo 4: Ripple Animation")
        print("   Expanding wave from center")
        print("   Beautiful spatial effect\n")

        # Multiple ripples
        for _ in range(3):
            animator.ripple(4, 4, (0, 255, 255), radius=4, duration=1.0, fade_out=True)
            time.sleep(1.2)

        print("   ✓ Complete\n")

        # ===== DEMO 5: SPARKLE ANIMATION =====
        print("✨ Demo 5: Sparkle Animation")
        print("   Random brightness variations")
        print("   Like twinkling stars\n")

        sparkle_buttons = [(2, 2), (4, 2), (6, 2), (2, 4), (4, 4), (6, 4), (2, 6), (4, 6), (6, 6)]
        for x, y in sparkle_buttons:
            animator.sparkle(x, y, (255, 255, 255), duration=4.0, intensity=0.6)

        time.sleep(4.5)
        animator.stop_all_animations()

        # Clear sparkles
        for x, y in sparkle_buttons:
            lp.panel.led(x, y).color = (0, 0, 0)

        print("   ✓ Complete\n")

        # ===== DEMO 6: WAVE ANIMATION =====
        print("🌀 Demo 6: Wave Animation")
        print("   Synchronized breathing across multiple buttons")
        print("   Perfect for chords or sequences\n")

        wave_buttons = [(1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4)]
        animator.wave(wave_buttons, (255, 100, 0), period=2.0, phase_offset=0.15)

        time.sleep(6)
        animator.stop_all_animations()

        # Clear wave
        for x, y in wave_buttons:
            lp.panel.led(x, y).color = (0, 0, 0)

        print("   ✓ Complete\n")

        # ===== DEMO 7: RAINBOW CYCLE =====
        print("🌈 Demo 7: Rainbow Cycle")
        print("   Continuous color wheel rotation")
        print("   Psychedelic mode!\n")

        rainbow_buttons = [
            (3, 3), (4, 3), (5, 3),
            (3, 4), (4, 4), (5, 4),
            (3, 5), (4, 5), (5, 5),
        ]

        for x, y in rainbow_buttons:
            animator.rainbow_cycle(x, y, period=3.0)

        time.sleep(9)
        animator.stop_all_animations()

        # Clear
        for x, y in rainbow_buttons:
            lp.panel.led(x, y).color = (0, 0, 0)

        print("   ✓ Complete\n")

        # ===== DEMO 8: STROBE =====
        print("⚡ Demo 8: Strobe Animation")
        print("   Rapid on/off flashing")
        print("   High-energy effect!\n")

        strobe_buttons = [(2, 2), (6, 2), (2, 6), (6, 6)]
        for x, y in strobe_buttons:
            animator.strobe(x, y, (255, 0, 255), frequency=8.0, duration=2.0)

        time.sleep(2.5)
        animator.stop_all_animations()

        # Clear
        for x, y in strobe_buttons:
            lp.panel.led(x, y).color = (0, 0, 0)

        print("   ✓ Complete\n")

        # ===== FINALE: EVERYTHING AT ONCE =====
        print("🎆 FINALE: All Animations Combined!")
        print("   The full LED orchestra\n")

        # Breathing corners
        animator.breathe(1, 1, (255, 0, 0), period=2.0)
        animator.breathe(7, 1, (0, 255, 0), period=2.2)
        animator.breathe(1, 7, (0, 0, 255), period=1.8)
        animator.breathe(7, 7, (255, 255, 0), period=2.4)

        # Sparkle middle
        animator.sparkle(4, 4, (255, 255, 255), duration=0, intensity=0.8)

        # Rainbow edges
        for x in range(2, 7):
            animator.rainbow_cycle(x, 0, period=4.0)

        time.sleep(8)

        print("\n✨ Animation showcase complete!")
        print("\n💡 These animations are now available in BabySynth!")
        print("   • Breathing: Sustained notes pulse gently")
        print("   • Pulse: Quick flash on button press")
        print("   • Fade: Smooth transitions when releasing")
        print("\n   Try them: python main.py\n")

    except KeyboardInterrupt:
        print("\n\n🛑 Showcase stopped\n")

    finally:
        animator.stop_all_animations()
        # Clear grid
        for x in range(9):
            for y in range(9):
                lp.panel.led(x, y).color = (0, 0, 0)


if __name__ == "__main__":
    main()
