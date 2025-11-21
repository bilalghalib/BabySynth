"""
BabySynth - Playback Engine
Replays recorded sessions with LED visualization and optional audio.
"""
import time
import threading
from typing import Optional
import logging
from lpminimk3 import Mode, find_launchpads
from session_manager import SessionManager


class PlaybackEngine:
    """
    Replays recorded BabySynth sessions on the Launchpad hardware.

    Supports:
    - Variable playback speed (0.25x to 4x)
    - Pause/resume
    - Jump to specific time
    - Visual-only mode (LED changes without audio)
    - Pattern highlighting during playback
    """

    def __init__(self, session_manager: SessionManager, launchpad=None):
        self.session_manager = session_manager
        self.lp = launchpad
        self.is_playing = False
        self.is_paused = False
        self.playback_speed = 1.0
        self.current_time = 0.0
        self.playback_thread: Optional[threading.Thread] = None

    def init_launchpad(self):
        """Initialize Launchpad connection if not provided."""
        if not self.lp:
            launchpads = find_launchpads()
            if not launchpads:
                raise RuntimeError("No Launchpad found for playback")
            self.lp = launchpads[0]
            self.lp.open()
            self.lp.mode = Mode.PROG
        self.clear_grid()

    def clear_grid(self):
        """Clear all LEDs."""
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)

    def play_session(self, session_id: int, speed: float = 1.0,
                    visual_only: bool = False, show_patterns: bool = True):
        """
        Play back a recorded session.

        Args:
            session_id: Session ID to replay
            speed: Playback speed multiplier (0.25 to 4.0)
            visual_only: If True, only show LED changes (no audio)
            show_patterns: If True, highlight detected patterns during playback
        """
        if self.is_playing:
            logging.warning("Already playing a session")
            return

        session = self.session_manager.get_session(session_id)
        if not session:
            logging.error(f"Session {session_id} not found")
            return

        # Load session data
        events = self.session_manager.get_session_events(session_id)
        led_changes = self.session_manager.get_session_led_changes(session_id)
        patterns = self.session_manager.get_session_patterns(session_id) if show_patterns else []

        if not events and not led_changes:
            logging.warning(f"Session {session_id} has no recorded events")
            return

        self.playback_speed = speed
        self.current_time = 0.0
        self.is_playing = True
        self.is_paused = False

        # Initialize launchpad if needed
        if not self.lp:
            self.init_launchpad()

        print(f"\n🎬 Playing session {session_id}")
        print(f"   Profile: {session['user_profile']}")
        print(f"   Duration: {session.get('duration', 0):.1f}s")
        print(f"   Events: {session.get('total_events', 0)}")
        print(f"   Speed: {speed}x")
        if patterns:
            print(f"   Patterns detected: {len(patterns)}")
        print("\n   Press Ctrl+C to stop\n")

        # Start playback in a separate thread
        self.playback_thread = threading.Thread(
            target=self._playback_loop,
            args=(events, led_changes, patterns, visual_only)
        )
        self.playback_thread.start()

    def _playback_loop(self, events, led_changes, patterns, visual_only):
        """Internal playback loop."""
        start_time = time.time()

        # Merge events and LED changes into a single timeline
        timeline = []

        for event in events:
            timeline.append({
                'time': event['relative_time'],
                'type': 'event',
                'data': event
            })

        for led in led_changes:
            timeline.append({
                'time': led['relative_time'],
                'type': 'led',
                'data': led
            })

        # Sort by time
        timeline.sort(key=lambda x: x['time'])

        # Pattern markers
        pattern_markers = []
        for pattern in patterns:
            pattern_markers.append({
                'time': pattern['start_time'],
                'type': 'pattern_start',
                'data': pattern
            })
            pattern_markers.append({
                'time': pattern['end_time'],
                'type': 'pattern_end',
                'data': pattern
            })

        # Merge pattern markers
        timeline.extend(pattern_markers)
        timeline.sort(key=lambda x: x['time'])

        # Track current pattern for highlighting
        current_pattern = None

        try:
            for item in timeline:
                if not self.is_playing:
                    break

                # Wait until we reach the item's time
                while self.is_playing and not self.is_paused:
                    elapsed = (time.time() - start_time) * self.playback_speed
                    if elapsed >= item['time']:
                        break
                    time.sleep(0.001)

                if not self.is_playing:
                    break

                # Handle pattern markers
                if item['type'] == 'pattern_start':
                    current_pattern = item['data']
                    print(f"\n   ⭐ Pattern: {current_pattern['description']}")
                    self._highlight_pattern_start()

                elif item['type'] == 'pattern_end':
                    current_pattern = None

                # Handle LED changes
                elif item['type'] == 'led':
                    led_data = item['data']
                    self._set_led(
                        led_data['x'], led_data['y'],
                        (led_data['color_r'], led_data['color_g'], led_data['color_b']),
                        is_pattern=current_pattern is not None
                    )

                # Handle events (for logging/display)
                elif item['type'] == 'event':
                    event_data = item['data']
                    if event_data['event_type'] == 'button_press':
                        note_info = event_data.get('note_name', 'audio file')
                        print(f"   🎵 [{item['time']:.2f}s] Press at ({event_data['x']}, {event_data['y']}) - {note_info}")

            print("\n✨ Playback complete!\n")

        except KeyboardInterrupt:
            print("\n\n⏹️  Playback stopped\n")

        finally:
            self.is_playing = False
            self.clear_grid()

    def _set_led(self, x: int, y: int, color: tuple, is_pattern: bool = False):
        """Set LED color, optionally with pattern highlight."""
        if is_pattern:
            # Add white flash to highlight pattern moments
            color = tuple(min(255, c + 50) for c in color)

        led = self.lp.panel.led(x, y)
        led.color = color

    def _highlight_pattern_start(self):
        """Visual cue when a pattern starts."""
        # Brief white flash across all buttons
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                current = led.color
                led.color = (255, 255, 255)

        time.sleep(0.05)

        # Restore (will be handled by next LED change in timeline)

    def pause(self):
        """Pause playback."""
        self.is_paused = True
        logging.info("Playback paused")

    def resume(self):
        """Resume playback."""
        self.is_paused = False
        logging.info("Playback resumed")

    def stop(self):
        """Stop playback."""
        self.is_playing = False
        if self.playback_thread:
            self.playback_thread.join(timeout=1.0)
        self.clear_grid()
        logging.info("Playback stopped")

    def set_speed(self, speed: float):
        """Change playback speed (0.25x to 4x)."""
        if 0.25 <= speed <= 4.0:
            self.playback_speed = speed
            logging.info(f"Playback speed set to {speed}x")
        else:
            logging.warning(f"Invalid speed {speed}. Must be between 0.25 and 4.0")

    def display_session_summary(self, session_id: int):
        """
        Display a beautiful summary of a session before playback.

        Shows:
        - Session metadata
        - Most pressed buttons
        - Detected patterns
        - Duration and tempo
        """
        session = self.session_manager.get_session(session_id)
        summary = self.session_manager.get_session_summary(session_id)
        patterns = self.session_manager.get_session_patterns(session_id)

        if not session:
            print(f"❌ Session {session_id} not found")
            return

        from datetime import datetime

        start_dt = datetime.fromtimestamp(session['start_time'])

        print("\n" + "="*60)
        print(f"  SESSION #{session_id}: {session['user_profile']}")
        print("="*60)
        print(f"  Date: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Duration: {summary.get('duration', 0):.1f} seconds")
        print(f"  Config: {session.get('config_name', 'unknown')}")
        print(f"  Scale: {session.get('scale', 'unknown')} - {session.get('model_name', 'unknown')}")
        print(f"\n  📊 Activity:")
        print(f"     Total events: {summary.get('total_events', 0)}")
        print(f"     Button presses: {summary.get('button_presses', 0)}")
        print(f"     Avg tempo: {summary.get('average_tempo', 0):.2f}s between presses")

        most_pressed = summary.get('most_pressed_buttons', [])
        if most_pressed:
            print(f"\n  🔥 Most pressed buttons:")
            for i, btn in enumerate(most_pressed[:3], 1):
                pos = btn['position']
                count = btn['count']
                print(f"     {i}. Position {pos} - {count} times")

        if patterns:
            print(f"\n  ⭐ Interesting moments detected:")
            for pattern in patterns:
                desc = pattern['description']
                start = pattern['start_time']
                print(f"     • [{start:.1f}s] {desc}")

        if session.get('notes'):
            print(f"\n  📝 Notes: {session['notes']}")

        print("="*60 + "\n")

    def generate_session_video_ascii(self, session_id: int, output_file: str):
        """
        Generate an ASCII art "video" of the session.

        Creates a text file with frame-by-frame ASCII representation
        of the LED grid state.
        """
        led_changes = self.session_manager.get_session_led_changes(session_id)

        if not led_changes:
            print("No LED changes to visualize")
            return

        # Group LED changes by relative time (frame)
        frames = {}
        for led in led_changes:
            frame_time = round(led['relative_time'], 1)  # 100ms frames
            if frame_time not in frames:
                frames[frame_time] = {}
            frames[frame_time][(led['x'], led['y'])] = (led['color_r'], led['color_g'], led['color_b'])

        # Build cumulative grid state
        grid_state = {}
        output_lines = []

        for frame_time in sorted(frames.keys()):
            # Update grid state
            for (x, y), color in frames[frame_time].items():
                grid_state[(x, y)] = color

            # Render grid as ASCII
            output_lines.append(f"\n[{frame_time}s]")
            for y in range(9):
                row = ""
                for x in range(9):
                    color = grid_state.get((x, y), (0, 0, 0))
                    if sum(color) > 0:
                        row += "█"  # Lit button
                    else:
                        row += "·"  # Unlit button
                output_lines.append(row)

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))

        print(f"✨ ASCII video saved to {output_file}")
