import yaml
import time
import threading
import numpy as np
import simpleaudio as sa
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import play_wave

class BabyPlayer:
    """Super simple music player for toddlers - one button = one cool riff!"""

    def __init__(self, config_file='baby_config.yaml'):
        self.running = True
        self.lock = threading.Lock()

        # Load configuration
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)

        self.tempo = self.config['tempo']
        self.root_freq = self.config['root_note']

        # Active loops
        self.active_drums = None
        self.active_bass = None
        self.active_melody = None
        self.loop_threads = []

        # Initialize hardware
        self.lp = find_launchpads()[0]
        if self.lp is None:
            print("No Launchpad found. Exiting.")
            exit()
        self.lp.open()
        self.lp.mode = Mode.PROG

        self.setup_colors()
        print(f"🎵 BABY MUSIC PLAYER READY! 🎵")

    def generate_bass_sound(self, frequency, duration=0.4):
        """Generate warm, deep bass sound"""
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)

        # Deep bass with nice harmonics
        wave = np.sin(2 * np.pi * frequency * t)
        wave += 0.6 * np.sin(2 * np.pi * frequency * 2 * t)  # Octave
        wave += 0.3 * np.sin(2 * np.pi * frequency * 3 * t)  # Fifth

        # Smooth envelope
        envelope = np.exp(-3 * t)
        wave *= envelope

        # Warm saturation
        wave = np.tanh(wave * 1.8)
        wave = (wave * 32767 * 0.9).astype(np.int16)
        return wave

    def generate_drum_sound(self, drum_type):
        """Generate simple drum sounds"""
        drums = self.config['drums']
        drum = drums[drum_type]

        duration = drum['decay']
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)

        if drum['type'] == 'kick':
            # Deep kick
            pitch_env = np.exp(-40 * t)
            frequency = drum['freq'] * (1 + 3 * pitch_env)
            wave = np.sin(2 * np.pi * frequency * t)
            wave += 0.3 * np.sin(2 * np.pi * drum['freq'] * 0.5 * t)
            wave *= np.exp(-8 * t)

        elif drum['type'] == 'snare':
            # Snappy snare
            tone = np.sin(2 * np.pi * drum['freq'] * t)
            noise = np.random.normal(0, 1, len(t))
            wave = 0.3 * tone + 0.7 * noise
            wave *= np.exp(-20 * t)

        elif drum['type'] == 'hihat':
            # Crisp hihat
            noise = np.random.normal(0, 1, len(t))
            wave = noise * np.exp(-100 * t)

        else:
            wave = np.sin(2 * np.pi * drum['freq'] * t)
            wave *= np.exp(-10 * t)

        wave = np.tanh(wave * drum.get('gain', 1.0))
        wave = (wave * 32767 * drum.get('volume', 0.7)).astype(np.int16)
        return wave

    def play_riff(self, riff_config):
        """Play a musical riff/phrase"""
        beat_duration = 60.0 / self.tempo / 4  # 16th note duration

        for note in riff_config['notes']:
            # Calculate frequency
            freq = self.root_freq * (2 ** (note['semitone'] / 12.0))

            # Generate sound
            duration = beat_duration * note['duration']
            wave = self.generate_bass_sound(freq, duration)

            # Play it
            play_wave(wave)

            # Wait for duration + any rest
            if 'rest' in note:
                time.sleep(beat_duration * note['rest'])

    def drum_loop(self, pattern_name):
        """Loop a drum pattern"""
        pattern = self.config['drum_patterns'][pattern_name]
        beat_duration = 60.0 / self.tempo / 4  # 16th notes
        step = 0

        while self.running and self.active_drums == pattern_name:
            # Play drums for this step
            for drum_name, drum_pattern in pattern['drums'].items():
                if drum_pattern[step] == 1:
                    wave = self.generate_drum_sound(drum_name)
                    threading.Thread(target=lambda w=wave: play_wave(w)).start()

            # Move to next step
            step = (step + 1) % 16
            time.sleep(beat_duration)

    def bass_loop(self, riff_name):
        """Loop a bass riff"""
        riff = self.config['bass_riffs'][riff_name]

        while self.running and self.active_bass == riff_name:
            self.play_riff(riff)

    def melody_loop(self, melody_name):
        """Loop a melody"""
        melody = self.config['melodies'][melody_name]

        while self.running and self.active_melody == melody_name:
            self.play_riff(melody)

    def setup_colors(self):
        """Set up colorful zones on the Launchpad"""
        # Clear all first
        for x in range(8):
            for y in range(8):
                self.lp.panel.led(x, y).color = (0, 0, 0)

        # DRUM ZONE (rows 6-7) - Warm colors (red/orange/yellow)
        drum_patterns = list(self.config['drum_patterns'].keys())
        colors = [(255, 0, 0), (255, 100, 0), (255, 200, 0), (200, 255, 0),
                  (255, 0, 100), (255, 150, 0), (200, 200, 0), (150, 255, 0)]

        for i, drum in enumerate(drum_patterns[:8]):
            x = i % 8
            y = 7 if i < 4 else 6
            if i >= 4:
                x = i - 4
            self.lp.panel.led(x, y).color = colors[i]

        # BASS ZONE (rows 4-5) - Deep colors (purple/blue/magenta)
        bass_riffs = list(self.config['bass_riffs'].keys())
        bass_colors = [(200, 0, 255), (150, 0, 200), (100, 0, 255), (200, 0, 200),
                       (180, 0, 255), (120, 0, 200), (160, 0, 255), (140, 0, 200)]

        for i, bass in enumerate(bass_riffs[:8]):
            x = i % 8
            y = 5 if i < 4 else 4
            if i >= 4:
                x = i - 4
            self.lp.panel.led(x, y).color = bass_colors[i]

        # MELODY ZONE (rows 2-3) - Bright colors (cyan/green/blue)
        melodies = list(self.config['melodies'].keys())
        melody_colors = [(0, 255, 200), (0, 200, 255), (0, 255, 150), (100, 255, 200),
                         (0, 255, 255), (0, 200, 200), (50, 255, 200), (0, 180, 255)]

        for i, melody in enumerate(melodies[:8]):
            x = i % 8
            y = 3 if i < 4 else 2
            if i >= 4:
                x = i - 4
            self.lp.panel.led(x, y).color = melody_colors[i]

        # STOP ALL button (top left)
        self.lp.panel.led(0, 0).color = (255, 255, 255)

        # TEMPO buttons (top right)
        self.lp.panel.led(6, 0).color = (100, 100, 100)  # Slower
        self.lp.panel.led(7, 0).color = (100, 100, 100)  # Faster

    def handle_button_press(self, button):
        """Handle button presses"""
        x, y = button.x, button.y

        if x >= 8 or y >= 8:
            return

        # STOP ALL button
        if x == 0 and y == 0:
            self.active_drums = None
            self.active_bass = None
            self.active_melody = None
            print("🛑 STOP ALL")
            self.flash_button(x, y)
            return

        # Tempo controls
        if y == 0 and x == 6:
            self.tempo = max(60, self.tempo - 10)
            print(f"🐢 Slower: {self.tempo} BPM")
            self.flash_button(x, y)
            return

        if y == 0 and x == 7:
            self.tempo = min(180, self.tempo + 10)
            print(f"🐇 Faster: {self.tempo} BPM")
            self.flash_button(x, y)
            return

        # DRUM ZONE (rows 6-7)
        if y in [6, 7]:
            drum_index = x if y == 7 else x + 4
            drum_patterns = list(self.config['drum_patterns'].keys())
            if drum_index < len(drum_patterns):
                pattern_name = drum_patterns[drum_index]
                self.active_drums = pattern_name
                print(f"🥁 Playing: {pattern_name}")
                threading.Thread(target=self.drum_loop, args=(pattern_name,), daemon=True).start()
                self.flash_button(x, y)

        # BASS ZONE (rows 4-5)
        elif y in [4, 5]:
            bass_index = x if y == 5 else x + 4
            bass_riffs = list(self.config['bass_riffs'].keys())
            if bass_index < len(bass_riffs):
                riff_name = bass_riffs[bass_index]
                self.active_bass = riff_name
                print(f"🎸 Bass: {riff_name}")
                threading.Thread(target=self.bass_loop, args=(riff_name,), daemon=True).start()
                self.flash_button(x, y)

        # MELODY ZONE (rows 2-3)
        elif y in [2, 3]:
            melody_index = x if y == 3 else x + 4
            melodies = list(self.config['melodies'].keys())
            if melody_index < len(melodies):
                melody_name = melodies[melody_index]
                self.active_melody = melody_name
                print(f"🎵 Melody: {melody_name}")
                threading.Thread(target=self.melody_loop, args=(melody_name,), daemon=True).start()
                self.flash_button(x, y)

    def flash_button(self, x, y):
        """Flash a button white when pressed"""
        original_color = self.lp.panel.led(x, y).color
        self.lp.panel.led(x, y).color = (255, 255, 255)
        time.sleep(0.1)
        self.lp.panel.led(x, y).color = original_color

    def event_loop(self):
        """Main event loop"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.001)

    def start(self):
        """Start the baby player!"""
        print("\n" + "=" * 60)
        print("🎵 BABY MUSIC PLAYER 🎵")
        print("=" * 60)
        print("\n👶 SUPER EASY TO USE - JUST PRESS BUTTONS! 👶")
        print("\n📍 WHERE TO PRESS:")
        print("  🔴 BOTTOM 2 ROWS (6-7): Drum beats (red/orange/yellow)")
        print("  🟣 MIDDLE 2 ROWS (4-5): Bass riffs (purple/magenta)")
        print("  🔵 NEXT 2 ROWS (2-3):   Melodies (cyan/blue/green)")
        print("  ⬜ TOP LEFT:            STOP ALL MUSIC")
        print("  ⚡ TOP RIGHT:           Slower / Faster")
        print("\n💡 TIP: Press different colors to layer sounds!")
        print("💡 Everything plays together in harmony!")
        print("\n⌨️  Press Ctrl+C to exit.\n")

        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            print("\n👋 Bye bye! Great music! 🎵")

if __name__ == "__main__":
    import sys
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'baby_config.yaml'
    player = BabyPlayer(config_file)
    player.start()
