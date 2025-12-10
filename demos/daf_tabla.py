"""
Daf & Tabla Percussion Demo
Interactive percussion soundboard for traditional Persian and Indian drums.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import threading
from synth import LaunchpadSynth
from lpminimk3 import ButtonEvent

class DafTablaDemo:
    def __init__(self, config_file='configs/daf_tabla.yaml', model='DAF_TABLA', scale='C_major'):
        """
        Initialize the Daf/Tabla demo

        Args:
            config_file: Path to the daf_tabla config file
            model: Which layout to use (DAF_TABLA, TABLA_FULL, or DAF_FULL)
            scale: Scale to use (not really applicable for percussion, but required)
        """
        print("=" * 60)
        print("   DAF & TABLA PERCUSSION DEMO")
        print("=" * 60)
        print("\nInitializing Launchpad...")

        self.synth = LaunchpadSynth(config_file)
        self.synth.assign_notes_and_files(scale, model)
        self.running = True
        self.recording = False
        self.recorded_pattern = []
        self.pattern_start_time = None

        print(f"\n✓ Loaded layout: {model}")
        print(f"✓ Config: {config_file}")
        print("\nControls:")
        print("  - Press pads to play percussion sounds")
        print("  - Top-right corner button: Start/Stop recording")
        print("  - Press Ctrl+C to exit")
        print("\nLayout Guide:")
        self.print_layout_guide(model)
        print("\n" + "=" * 60)
        print("Ready to play! Press the pads to make sounds.")
        print("=" * 60 + "\n")

    def print_layout_guide(self, model):
        """Print a guide for the current layout"""
        if model == 'DAF_TABLA':
            print("""
  Top Half (D & T):
    - Left 4 columns (D): Deep bass strokes (Dum/Ge)
    - Right 4 columns (T): Treble strokes (Tak/Tin)
  Bottom Half (B & S):
    - Left 4 columns (B): Daf bass (Dum)
    - Right 4 columns (S): Daf treble (Tak)
            """)
        elif model == 'TABLA_FULL':
            print("""
  Top Section:
    - Left (N): Na strokes (open rim)
    - Middle (T): Tin strokes (closed rim)
    - Right (K): Te strokes (middle)
  Middle Section:
    - Left (D): Ge bass
    - Middle (G): Ka slap
    - Right (C): Dha combined
  Bottom (R): Rolls
            """)
        elif model == 'DAF_FULL':
            print("""
  Top rows: Bass (Dum) - deep center strokes
  Upper middle: Treble (Tak) - bright rim strokes
  Lower middle: Slaps (Ka) - sharp accents
  Bottom: Rolls - finger rolls
            """)

    def handle_button_event(self, event):
        """Handle button press/release events"""
        x, y = event.button.x, event.button.y

        # Top-right corner is control button (8, 0)
        if x == 8 and y == 0:
            if event.type == ButtonEvent.PRESS:
                self.toggle_recording()
            return

        # Record button press if recording
        if self.recording and event.type == ButtonEvent.PRESS:
            current_time = time.time()
            if self.pattern_start_time is None:
                self.pattern_start_time = current_time
                timestamp = 0
            else:
                timestamp = current_time - self.pattern_start_time

            self.recorded_pattern.append({
                'x': x,
                'y': y,
                'time': timestamp
            })

        # Pass event to synth for sound playback
        self.synth.handle_event(event)

    def toggle_recording(self):
        """Toggle pattern recording on/off"""
        self.recording = not self.recording

        if self.recording:
            # Start recording
            self.recorded_pattern = []
            self.pattern_start_time = None
            print("\n🔴 RECORDING started - play your rhythm!")
            # Light up corner button red
            led = self.synth.lp.panel.led(8, 0)
            led.color = (255, 0, 0)
        else:
            # Stop recording
            print(f"⏹️  RECORDING stopped - captured {len(self.recorded_pattern)} hits")
            # Light up corner button green
            led = self.synth.lp.panel.led(8, 0)
            led.color = (0, 255, 0)

            if len(self.recorded_pattern) > 0:
                print("   Press corner button again to playback pattern")
                # Wait a moment, then offer playback
                time.sleep(1)
                threading.Thread(target=self.playback_pattern, daemon=True).start()

    def playback_pattern(self):
        """Play back the recorded pattern"""
        if not self.recorded_pattern:
            return

        print("\n▶️  Playing back pattern...")
        start_time = time.time()

        for hit in self.recorded_pattern:
            # Wait until it's time for this hit
            target_time = start_time + hit['time']
            current_time = time.time()
            if current_time < target_time:
                time.sleep(target_time - current_time)

            # Create a synthetic press event and play the sound
            x, y = hit['x'], hit['y']

            # Find and play the corresponding sound
            for char, file_data in self.synth.audio_files.items():
                for button in file_data['buttons']:
                    if button.x == x and button.y == y:
                        # Play the sound
                        self.synth.play_sound(file_data['file'], file_data['buttons'], file_data['color'])
                        break

        print("✓ Playback complete!\n")
        # Reset corner button color
        led = self.synth.lp.panel.led(8, 0)
        led.color = (0, 0, 100)  # Dim blue

    def run(self):
        """Main event loop"""
        try:
            # Set corner button to dim blue
            led = self.synth.lp.panel.led(8, 0)
            led.color = (0, 0, 100)

            while self.running:
                event = self.synth.lp.panel.buttons().poll_for_event()
                if event:
                    self.handle_button_event(event)
                else:
                    time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up...")
        self.synth.clear_grid()
        self.synth.lp.close()
        print("Goodbye! 🎵")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Daf & Tabla Percussion Demo')
    parser.add_argument('--layout', '-l',
                       choices=['DAF_TABLA', 'TABLA_FULL', 'DAF_FULL'],
                       default='DAF_TABLA',
                       help='Choose which layout to use (default: DAF_TABLA)')
    parser.add_argument('--config', '-c',
                       default='configs/daf_tabla.yaml',
                       help='Path to config file (default: configs/daf_tabla.yaml)')

    args = parser.parse_args()

    # Check if sound files exist
    import os
    sound_dirs = ['sounds/tabla', 'sounds/daf']
    missing_dirs = [d for d in sound_dirs if not os.path.exists(d)]

    if missing_dirs:
        print("\n⚠️  WARNING: Sound directories not found!")
        print(f"Missing: {', '.join(missing_dirs)}")
        print("\nPlease set up sound files first. See: sounds/DAF_TABLA_SOUNDS.md")
        print("\nQuick setup with placeholders:")
        print("  mkdir -p sounds/tabla sounds/daf")
        print("  # Then copy placeholder files as described in DAF_TABLA_SOUNDS.md")

        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return

    demo = DafTablaDemo(config_file=args.config, model=args.layout)
    demo.run()


if __name__ == '__main__':
    main()
