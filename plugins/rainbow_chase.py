"""
Rainbow Chase Game Plugin
Colors sweep across the screen - baby tries to catch them!
"""

import time
import threading
from game_plugin import Game


class RainbowChase(Game):
    """Rainbow colors sweep across the grid for baby to catch"""

    def __init__(self):
        super().__init__(
            name="Rainbow Chase",
            description="Chase and catch the rainbow as it moves!",
            difficulty="Easy",
            min_age=1
        )
        self.current_col = 0
        self.current_color_idx = 0
        self.rainbow_colors = [
            (255, 0, 0),      # Red
            (255, 127, 0),    # Orange
            (255, 255, 0),    # Yellow
            (0, 255, 0),      # Green
            (0, 0, 255),      # Blue
            (75, 0, 130),     # Indigo
            (148, 0, 211),    # Violet
        ]
        self.move_timer = None
        self.score = 0

    def start(self):
        """Start the rainbow chase"""
        self.clear_grid()
        self.score = 0
        self.current_col = 0
        print(f"🎮 {self.name} started!")
        print(f"🌈 Catch the rainbow colors as they move!")
        self.move_rainbow()

    def move_rainbow(self):
        """Move the rainbow column"""
        if not self.running:
            return

        # Clear previous column
        if self.current_col > 0:
            for y in range(1, 9):
                self.set_led(self.current_col - 1, y, (0, 0, 0))

        # Draw current column
        color = self.rainbow_colors[self.current_color_idx]
        for y in range(1, 9):
            self.set_led(self.current_col, y, color)

        # Move to next column and color
        self.current_col += 1
        self.current_color_idx = (self.current_color_idx + 1) % len(self.rainbow_colors)

        # Wrap around
        if self.current_col >= 9:
            self.current_col = 0

        # Schedule next move
        self.move_timer = threading.Timer(0.5, self.move_rainbow)
        self.move_timer.start()

    def handle_button_press(self, x, y):
        """Baby caught a color!"""
        # Check if they pressed the current rainbow column
        if x == self.current_col - 1 or x == self.current_col:
            self.score += 1
            # Flash white to show success
            old_color = self.lp.panel.led(x, y).color
            self.set_led(x, y, (255, 255, 255))
            time.sleep(0.05)
            self.set_led(x, y, old_color)
            print(f"🌟 Caught! Score: {self.score}")

    def stop(self):
        """Clean up"""
        self.running = False
        if self.move_timer:
            self.move_timer.cancel()
        self.clear_grid()
        print(f"\n🏆 Final Score: {self.score}")
