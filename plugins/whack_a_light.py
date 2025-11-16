"""
Whack-a-Light Game Plugin
A simple game where lights appear randomly and baby must press them!
"""

import random
import time
import threading
from game_plugin import Game


class WhackALight(Game):
    """Simple whack-a-light game for babies"""

    def __init__(self):
        super().__init__(
            name="Whack-a-Light",
            description="Press the lit buttons as fast as you can!",
            difficulty="Easy",
            min_age=1
        )
        self.current_light = None
        self.score = 0
        self.spawn_timer = None

    def start(self):
        """Initialize the game"""
        self.clear_grid()
        self.score = 0
        print(f"🎮 {self.name} started!")
        print(f"💡 Press the colored lights when they appear!")
        self.spawn_light()

    def spawn_light(self):
        """Spawn a random light on the grid"""
        if not self.running:
            return

        # Pick a random position (avoiding top row)
        x = random.randint(0, 8)
        y = random.randint(1, 8)

        # Pick a random bright color
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
        ]
        color = random.choice(colors)

        # Clear previous light
        if self.current_light:
            old_x, old_y = self.current_light
            self.set_led(old_x, old_y, (0, 0, 0))

        # Set new light
        self.set_led(x, y, color)
        self.current_light = (x, y)

        # Schedule next light (gets faster as score increases)
        delay = max(0.5, 2.0 - (self.score * 0.1))
        self.spawn_timer = threading.Timer(delay, self.spawn_light)
        self.spawn_timer.start()

    def handle_button_press(self, x, y):
        """Handle button press"""
        if self.current_light and (x, y) == self.current_light:
            # Hit! Flash white and increase score
            self.set_led(x, y, (255, 255, 255))
            self.score += 1
            print(f"✨ Hit! Score: {self.score}")

            # Clear and spawn new light faster
            if self.spawn_timer:
                self.spawn_timer.cancel()
            time.sleep(0.1)
            self.spawn_light()

    def stop(self):
        """Clean up"""
        self.running = False
        if self.spawn_timer:
            self.spawn_timer.cancel()
        self.clear_grid()
        print(f"\n🏆 Final Score: {self.score}")
        print("Thanks for playing!")
