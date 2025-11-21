"""
BabySynth - Turn-Taking Framework
Enables collaborative musical play with turn management and visual feedback.

Supports:
- Free play (both players anytime)
- Strict turns (one at a time)
- Call-and-response (player plays, other responds)
- Grid zones (left/right, top/bottom, custom)
- Visual turn indicators
- Automatic turn switching
"""
import time
import threading
from typing import List, Tuple, Callable, Optional
from enum import Enum
import logging


class TurnMode(Enum):
    """Turn-taking modes."""
    FREE_PLAY = "free_play"           # Both players can play anytime
    STRICT_TURNS = "strict_turns"     # Only current player can press buttons
    CALL_RESPONSE = "call_response"   # Player 1 plays, then player 2 responds
    TIMED_TURNS = "timed_turns"       # Each player gets N seconds


class GridZone(Enum):
    """Pre-defined grid zones."""
    LEFT_HALF = "left_half"       # x: 0-3
    RIGHT_HALF = "right_half"     # x: 5-8
    TOP_HALF = "top_half"         # y: 0-3
    BOTTOM_HALF = "bottom_half"   # y: 5-8
    FULL_GRID = "full_grid"       # Entire grid (for free play)


class TurnTaker:
    """
    Manages turn-taking for collaborative play.

    Features:
    - Multiple turn modes
    - Visual indicators (top row LEDs)
    - Automatic turn switching
    - Grid zone assignment
    - Turn timing and history
    """

    def __init__(self, launchpad, led_animator=None, session_manager=None):
        self.lp = launchpad
        self.led_animator = led_animator
        self.session_manager = session_manager

        # Turn state
        self.mode = TurnMode.FREE_PLAY
        self.current_player = 1
        self.player_count = 2

        # Player zones
        self.player_zones = {
            1: GridZone.LEFT_HALF,
            2: GridZone.RIGHT_HALF
        }

        # Player colors for visual feedback
        self.player_colors = {
            1: (255, 100, 100),  # Red
            2: (100, 100, 255),  # Blue
        }

        # Turn timing
        self.turn_start_time = time.time()
        self.turn_duration = 10.0  # seconds per turn (for TIMED_TURNS mode)
        self.min_turn_duration = 2.0  # minimum time before auto-switch

        # Turn history
        self.turn_history = []  # [(player, timestamp, duration)]

        # Callbacks
        self.on_turn_change_callbacks = []

        # Auto-turn timer
        self.turn_timer = None
        self.lock = threading.Lock()

        logging.info(f"TurnTaker initialized in {self.mode.value} mode")

    # ========== ZONE CHECKING ==========

    def is_in_zone(self, x: int, y: int, zone: GridZone) -> bool:
        """Check if a button is in a specific zone."""
        if zone == GridZone.FULL_GRID:
            return True
        elif zone == GridZone.LEFT_HALF:
            return x <= 3
        elif zone == GridZone.RIGHT_HALF:
            return x >= 5
        elif zone == GridZone.TOP_HALF:
            return y <= 3
        elif zone == GridZone.BOTTOM_HALF:
            return y >= 5
        return False

    def get_player_for_button(self, x: int, y: int) -> Optional[int]:
        """Determine which player owns a button based on zones."""
        for player, zone in self.player_zones.items():
            if self.is_in_zone(x, y, zone):
                return player
        return None

    def can_player_press(self, x: int, y: int, player: int = None) -> bool:
        """Check if a button press is allowed based on turn rules."""
        if player is None:
            player = self.current_player

        # In free play, anyone can press anything
        if self.mode == TurnMode.FREE_PLAY:
            return True

        # Check if button is in player's zone
        button_player = self.get_player_for_button(x, y)
        if button_player is None:
            return False  # Outside any zone

        # In strict turns, only current player can press
        if self.mode == TurnMode.STRICT_TURNS:
            return player == self.current_player

        # In call-response, current player can press their zone
        if self.mode == TurnMode.CALL_RESPONSE:
            return player == self.current_player and button_player == player

        # In timed turns, current player can press their zone
        if self.mode == TurnMode.TIMED_TURNS:
            return player == self.current_player and button_player == player

        return False

    # ========== TURN MANAGEMENT ==========

    def set_mode(self, mode: TurnMode):
        """Change turn-taking mode."""
        with self.lock:
            old_mode = self.mode
            self.mode = mode
            logging.info(f"Turn mode changed: {old_mode.value} → {mode.value}")

            # Update visual indicators
            self.update_turn_indicator()

            # Start/stop turn timer
            if mode == TurnMode.TIMED_TURNS:
                self.start_turn_timer()
            else:
                self.stop_turn_timer()

    def switch_turn(self, next_player: int = None):
        """Switch to the next player's turn."""
        with self.lock:
            # Record turn history
            turn_duration = time.time() - self.turn_start_time
            self.turn_history.append((self.current_player, self.turn_start_time, turn_duration))

            # Switch player
            old_player = self.current_player
            if next_player is not None:
                self.current_player = next_player
            else:
                # Cycle to next player
                self.current_player = (self.current_player % self.player_count) + 1

            self.turn_start_time = time.time()

            logging.info(f"Turn switched: Player {old_player} → Player {self.current_player}")

            # Update visuals
            self.update_turn_indicator()
            self.play_turn_change_sound()

            # Notify callbacks
            for callback in self.on_turn_change_callbacks:
                callback(old_player, self.current_player)

            # Restart timer if in timed mode
            if self.mode == TurnMode.TIMED_TURNS:
                self.start_turn_timer()

    def auto_switch_turn(self):
        """Automatically switch turns (called after time expires)."""
        elapsed = time.time() - self.turn_start_time
        if elapsed >= self.min_turn_duration:
            self.switch_turn()

    def request_turn_change(self, player: int):
        """Player requests to take their turn (for call-response mode)."""
        if self.mode == TurnMode.CALL_RESPONSE:
            # In call-response, pressing any button switches turn
            elapsed = time.time() - self.turn_start_time
            if elapsed >= self.min_turn_duration:
                self.switch_turn(player)

    # ========== VISUAL FEEDBACK ==========

    def update_turn_indicator(self):
        """Update top row LEDs to show whose turn it is."""
        # Top row (y=0) shows turn indicator
        # Player 1: Left side lit
        # Player 2: Right side lit

        if self.mode == TurnMode.FREE_PLAY:
            # In free play, show both players
            for x in range(1, 4):
                self._set_indicator_led(x, 0, self.player_colors[1])
            for x in range(5, 8):
                self._set_indicator_led(x, 0, self.player_colors[2])
        else:
            # Show current player
            color = self.player_colors[self.current_player]

            # Clear all first
            for x in range(9):
                self._set_indicator_led(x, 0, (0, 0, 0))

            # Light up current player's side
            if self.current_player == 1:
                for x in range(1, 4):
                    self._set_indicator_led(x, 0, color)
            elif self.current_player == 2:
                for x in range(5, 8):
                    self._set_indicator_led(x, 0, color)

        # If using animations, add pulse
        if self.led_animator and self.mode != TurnMode.FREE_PLAY:
            color = self.player_colors[self.current_player]
            if self.current_player == 1:
                self.led_animator.pulse(2, 0, color, duration=0.3)
            else:
                self.led_animator.pulse(6, 0, color, duration=0.3)

    def _set_indicator_led(self, x: int, y: int, color: Tuple[int, int, int]):
        """Set indicator LED color."""
        led = self.lp.panel.led(x, y)
        led.color = color

    def play_turn_change_sound(self):
        """Play audio feedback for turn change (optional)."""
        # Could trigger a sound here
        # For now, just visual feedback
        pass

    # ========== TURN TIMER ==========

    def start_turn_timer(self):
        """Start automatic turn timer."""
        self.stop_turn_timer()  # Cancel existing timer

        def timer_callback():
            self.auto_switch_turn()

        self.turn_timer = threading.Timer(self.turn_duration, timer_callback)
        self.turn_timer.daemon = True
        self.turn_timer.start()

    def stop_turn_timer(self):
        """Stop automatic turn timer."""
        if self.turn_timer:
            self.turn_timer.cancel()
            self.turn_timer = None

    # ========== CONFIGURATION ==========

    def set_player_zones(self, player_1_zone: GridZone, player_2_zone: GridZone):
        """Configure which zones each player controls."""
        with self.lock:
            self.player_zones[1] = player_1_zone
            self.player_zones[2] = player_2_zone
            logging.info(f"Player zones: P1={player_1_zone.value}, P2={player_2_zone.value}")

    def set_player_colors(self, player_1_color: Tuple[int, int, int],
                         player_2_color: Tuple[int, int, int]):
        """Set colors for turn indicators."""
        self.player_colors[1] = player_1_color
        self.player_colors[2] = player_2_color
        self.update_turn_indicator()

    def set_turn_duration(self, seconds: float):
        """Set duration for timed turns."""
        self.turn_duration = seconds

    def add_turn_change_callback(self, callback: Callable[[int, int], None]):
        """Register callback for turn changes. Called with (old_player, new_player)."""
        self.on_turn_change_callbacks.append(callback)

    # ========== STATISTICS ==========

    def get_turn_stats(self) -> dict:
        """Get statistics about turn-taking session."""
        if not self.turn_history:
            return {}

        player_turns = {1: [], 2: []}
        for player, timestamp, duration in self.turn_history:
            if player in player_turns:
                player_turns[player].append(duration)

        stats = {}
        for player, durations in player_turns.items():
            if durations:
                stats[f"player_{player}"] = {
                    "turn_count": len(durations),
                    "total_time": sum(durations),
                    "avg_turn_duration": sum(durations) / len(durations),
                    "min_turn": min(durations),
                    "max_turn": max(durations)
                }

        return stats

    def reset_turn_history(self):
        """Clear turn history."""
        with self.lock:
            self.turn_history = []

    # ========== DUET HELPERS ==========

    def is_duet_mode_active(self) -> bool:
        """Check if any collaborative mode is active."""
        return self.mode != TurnMode.FREE_PLAY

    def get_current_player_zone_buttons(self) -> List[Tuple[int, int]]:
        """Get all button positions in current player's zone."""
        zone = self.player_zones.get(self.current_player, GridZone.FULL_GRID)
        buttons = []

        for y in range(1, 9):  # Skip top row (indicators)
            for x in range(9):
                if self.is_in_zone(x, y, zone):
                    buttons.append((x, y))

        return buttons

    def highlight_player_zone(self, player: int, color: Tuple[int, int, int] = None):
        """Briefly highlight a player's zone."""
        if color is None:
            color = self.player_colors[player]

        zone = self.player_zones.get(player, GridZone.FULL_GRID)

        for y in range(1, 9):
            for x in range(9):
                if self.is_in_zone(x, y, zone):
                    if self.led_animator:
                        self.led_animator.pulse(x, y, color, duration=0.2, max_brightness=1.3)
