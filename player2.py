import yaml
import time
import random
import threading
import numpy as np
import simpleaudio as sa
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import generate_sine_wave, play_wave

class JamStation:
    def __init__(self, song_file='songs/sweet_caroline.yaml'):
        # Initialize
        self.running = True
        self.lock = threading.Lock()

        # Load song configuration
        self.load_song(song_file)

        # Musical state
        self.pressed_keys = set()
        self.visual_effects = []
        self.octave_shift = -1  # Start lower for less annoying sounds
        self.max_octave = 1  # Limit high notes

        # Beat system
        self.beat_on = False
        self.current_beat_pattern = 0
        self.next_beat_pattern = None
        self.beat_position = 0
        self.last_beat_time = time.time()
        self.beats_per_bar = 16
        self.current_tempo = self.tempo

        # Instrument modes
        self.current_instrument = 'bass'  # Start with bass - better for toddlers

        # Arpeggiator
        self.arpeggiator_on = False
        self.arp_index = 0
        self.last_arp_time = time.time()

        # Visual state
        self.last_display_update = 0
        self.beat_flash_time = 0

        # Volume controls
        self.drum_volume = 1.0
        self.bass_volume = 1.0
        self.melody_volume = 0.7

        # Initialize hardware
        self.init_launchpad()
        self.setup_layout()
        
    def load_song(self, song_file):
        """Load song configuration from YAML"""
        with open(song_file, 'r') as file:
            self.song = yaml.safe_load(file)
            
        self.song_name = self.song['name']
        self.tempo = self.song['tempo']
        self.root_note = self.song['root_note']
        
        # Generate scale frequencies for multiple octaves
        self.scale_notes = []
        octave_range = 3
        for octave in range(octave_range):
            for interval in self.song['scale']['intervals']:
                freq = self.root_note * (2 ** octave) * (2 ** (interval / 12))
                self.scale_notes.append(freq)
        
        # Parse chords
        self.chords = {}
        for chord_name, intervals in self.song['chords'].items():
            self.chords[chord_name] = [
                self.root_note * (2 ** (interval / 12)) 
                for interval in intervals
            ]
            
        # Load instruments
        self.drums = self.song['drums']

        # Convert beat_patterns from dict to list with names
        beat_patterns_dict = self.song['beat_patterns']
        self.beat_patterns = []
        for name, pattern in beat_patterns_dict.items():
            pattern['name'] = name.replace('_', ' ')
            self.beat_patterns.append(pattern)

        # Load tempo changes if specified
        self.tempo_changes = self.song.get('tempo_changes', {})
        
    def get_note_color(self, note_index):
        """Get color for a note based on its scale degree"""
        degree = note_index % len(self.song['scale']['intervals'])
        interval = self.song['scale']['intervals'][degree]
        
        # Color coding by scale degree
        color_map = {
            0: (255, 0, 0),      # Root - Red
            2: (255, 127, 0),    # Second - Orange
            3: (255, 191, 0),    # Minor 3rd
            4: (255, 255, 0),    # Major 3rd - Yellow
            5: (127, 255, 0),    # Fourth - Yellow-green
            7: (0, 255, 0),      # Fifth - Green
            9: (0, 255, 255),    # Sixth - Cyan
            10: (0, 127, 255),   # Minor 7th - Blue
            11: (127, 0, 255),   # Major 7th - Purple
            12: (255, 0, 255),   # Octave - Magenta
        }
        
        base_color = color_map.get(interval, (128, 128, 128))
        
        # Dim based on instrument
        if self.current_instrument == 'bass':
            return tuple(int(c * 0.6) for c in base_color)
        elif self.current_instrument == 'chords':
            return tuple(int(c * 0.8) for c in base_color)
        return base_color
        
    def init_launchpad(self):
        self.lp = find_launchpads()[0]
        if self.lp is None:
            print("No Launchpad found. Exiting.")
            exit()
        self.lp.open()
        self.lp.mode = Mode.PROG
        self.clear_grid()
        print(f"🎵 Jam Station loaded: {self.song_name} 🎵")
        
    def clear_grid(self):
        for x in range(8):  # Only 0-7 for main grid
            for y in range(8):  # Only 0-7 for main grid
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def generate_bass_sound(self, frequency, duration=0.3):
        """Generate deep bass sounds"""
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)

        # Deep bass with harmonics
        wave = np.sin(2 * np.pi * frequency * t)
        wave += 0.5 * np.sin(2 * np.pi * frequency * 2 * t)
        wave += 0.3 * np.sin(2 * np.pi * frequency * 3 * t)

        # Pluck envelope
        envelope = np.exp(-4 * t) * 0.7 + 0.3
        envelope *= np.exp(-1 * t)

        wave *= envelope
        wave = np.tanh(wave * 1.5)

        wave = (wave * 32767 * 0.8 * self.bass_volume).astype(np.int16)
        return wave
        
    def generate_drum_sound(self, drum_name):
        """Generate drum sounds"""
        drum = self.drums[drum_name]
        duration = drum['decay']
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        if drum['type'] == 'kick':
            # Deep kick
            base_freq = drum['freq']
            sub = np.sin(2 * np.pi * base_freq * 0.5 * t)
            
            pitch_env = np.exp(-drum.get('pitch_decay', 35) * t)
            frequency = base_freq * (1 + drum.get('pitch_mod', 4) * pitch_env)
            body = np.sin(2 * np.pi * frequency * t)
            
            click = np.zeros_like(t)
            click_samples = int(0.005 * sample_rate)
            if click_samples < len(t):
                click[:click_samples] = np.random.normal(0, 0.5, click_samples)
                click[:click_samples] *= np.linspace(1, 0, click_samples)
            
            wave = 0.4 * sub + 0.5 * body + 0.1 * click
            wave *= np.exp(-drum.get('env_decay', 8) * t)
            
        elif drum['type'] == 'snare':
            tone1 = np.sin(2 * np.pi * drum['freq'] * t)
            tone2 = np.sin(2 * np.pi * drum['freq'] * 1.7 * t)
            
            noise = np.random.normal(0, 1, len(t))
            noise_hp = np.diff(np.concatenate(([0], noise)))
            
            wave = 0.3 * tone1 + 0.2 * tone2 + 0.5 * noise_hp[:len(t)]
            
            attack = int(0.002 * sample_rate)
            wave[:attack] *= np.linspace(0, 1, attack)
            wave[attack:] *= np.exp(-drum.get('env_decay', 20) * t[attack:])
            
        elif drum['type'] == 'hihat':
            frequencies = [drum['freq'], drum['freq'] * 1.23, drum['freq'] * 1.67]
            wave = np.zeros_like(t)
            
            for freq in frequencies:
                wave += np.sin(2 * np.pi * freq * t) * np.random.uniform(0.3, 1.0)
                
            noise = np.random.normal(0, 0.4, len(t))
            wave = 0.4 * wave + 0.6 * noise
            wave *= np.exp(-drum.get('env_decay', 100) * t)
            
        elif drum['type'] == 'crash':
            fundamentals = [drum['freq'] * ratio for ratio in [1, 1.48, 2.13, 2.89, 3.67]]
            wave = np.zeros_like(t)
            
            for i, freq in enumerate(fundamentals):
                partial_env = np.exp(-(drum.get('env_decay', 12) + i * 1.5) * t)
                wave += np.sin(2 * np.pi * freq * t) * partial_env * (1 / (i + 1))
                
            shimmer = np.random.normal(0, 0.3, len(t))
            shimmer *= np.exp(-drum.get('env_decay', 12) * t)
            
            wave = 0.6 * wave + 0.4 * shimmer
            
            attack_samples = int(0.02 * sample_rate)
            wave[:attack_samples] *= np.linspace(0, 1, attack_samples)
            
        else:
            wave = np.sin(2 * np.pi * drum['freq'] * t)
            wave *= np.exp(-10 * t)
        
        wave = np.tanh(wave * drum.get('gain', 1.0))
        wave = (wave * 32767 * drum.get('volume', 0.7) * self.drum_volume).astype(np.int16)
        return wave
        
    def generate_synth_sound(self, frequency, sound_config=None):
        """Generate synth sounds"""
        if sound_config is None:
            sound_config = self.song.get(f'{self.current_instrument}_sound', {})
            
        duration = sound_config.get('duration', 0.3)
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        wave = np.zeros_like(t)
        harmonics = sound_config.get('harmonics', [1])
        
        for i, harmonic_amp in enumerate(harmonics):
            if harmonic_amp > 0:
                harmonic_freq = frequency * (i + 1)
                wave += harmonic_amp * np.sin(2 * np.pi * harmonic_freq * t)
                
        # Envelope
        attack = sound_config.get('attack', 0.01)
        decay = sound_config.get('decay', 0.1)
        sustain = sound_config.get('sustain', 0.7)
        
        attack_samples = int(attack * sample_rate)
        decay_samples = int(decay * sample_rate)
        
        envelope = np.ones_like(t) * sustain
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        if decay_samples > 0 and attack_samples + decay_samples < len(t):
            envelope[attack_samples:attack_samples + decay_samples] = np.linspace(1, sustain, decay_samples)
            
        wave *= envelope
        wave = np.clip(wave, -1, 1)

        # Apply melody volume for lead/chord sounds
        vol_mult = self.melody_volume if self.current_instrument in ['lead', 'chords'] else self.bass_volume
        wave = (wave * 32767 * sound_config.get('volume', 0.6) * vol_mult).astype(np.int16)
        return wave
        
    def setup_layout(self):
        """Set up the visual layout using only the 8x8 grid"""
        # Clear first
        self.clear_grid()

        # Scale notes (rows 2-6, 5 rows x 8 = 40 notes)
        note_index = 0
        for y in range(6, 1, -1):  # Rows 2-6 from bottom to top
            for x in range(8):
                if note_index < len(self.scale_notes):
                    led = self.lp.panel.led(x, y)
                    led.color = self.get_note_color(note_index)
                    note_index += 1

        # Bottom row (y=7) - Controls
        # Instrument selectors
        instruments = [
            ('lead', (255, 255, 0)),
            ('bass', (255, 0, 255)),
            ('chords', (0, 255, 255))
        ]
        for i, (inst, color) in enumerate(instruments):
            led = self.lp.panel.led(i, 7)
            if self.current_instrument == inst:
                led.color = color
            else:
                led.color = tuple(c // 4 for c in color)

        # Beat on/off button
        led = self.lp.panel.led(3, 7)
        led.color = (0, 255, 0) if self.beat_on else (255, 0, 0)

        # Arpeggiator button
        led = self.lp.panel.led(4, 7)
        led.color = (255, 0, 255) if self.arpeggiator_on else (50, 0, 50)

        # Octave controls
        led = self.lp.panel.led(6, 7)  # Down
        led.color = (100, 100, 255)
        led = self.lp.panel.led(7, 7)  # Up
        led.color = (100, 100, 255)

        # Top row (y=0) - Beat patterns
        for i in range(min(8, len(self.beat_patterns))):
            led = self.lp.panel.led(i, 0)
            if i == self.current_beat_pattern:
                led.color = (0, 255, 255)  # Cyan for active pattern
            elif self.next_beat_pattern == i:
                led.color = (255, 127, 0)  # Orange for queued pattern
            else:
                led.color = (50, 50, 0)  # Dim for inactive

        # Second row (y=1) - 16-step sequencer visualization
        self.update_sequencer_display()

    def update_sequencer_display(self):
        """Update row 1 to show the current beat pattern with position indicator"""
        if not self.beat_on:
            # When beat is off, show a dim visualization
            for x in range(8):
                led = self.lp.panel.led(x, 1)
                led.color = (20, 20, 20)
            return

        pattern = self.beat_patterns[self.current_beat_pattern]

        # Show each of the 16 steps (2 steps per LED for 8 LEDs)
        for x in range(8):
            step1 = x * 2
            step2 = x * 2 + 1

            # Check if any drums hit on these steps
            has_kick1 = pattern['drums'].get('kick', [0]*16)[step1] == 1
            has_kick2 = pattern['drums'].get('kick', [0]*16)[step2] == 1
            has_snare1 = pattern['drums'].get('snare', [0]*16)[step1] == 1
            has_snare2 = pattern['drums'].get('snare', [0]*16)[step2] == 1
            has_hihat1 = pattern['drums'].get('hihat', [0]*16)[step1] == 1
            has_hihat2 = pattern['drums'].get('hihat', [0]*16)[step2] == 1

            # Color based on what's playing
            color = [0, 0, 0]
            if has_kick1 or has_kick2:
                color[0] = 200  # Red for kick
            if has_snare1 or has_snare2:
                color[1] = 200  # Green for snare
            if has_hihat1 or has_hihat2:
                color[2] = 200  # Blue for hihat

            # If nothing, show dim gray
            if color == [0, 0, 0]:
                color = [30, 30, 30]

            # Highlight current beat position
            current_pair = self.beat_position // 2
            if x == current_pair:
                # Brighten the current position
                color = [min(255, c + 100) for c in color]

            led = self.lp.panel.led(x, 1)
            led.color = tuple(color)

    def play_beat_step(self):
        """Play a single step of the current beat pattern"""
        if not self.beat_on:
            return
            
        pattern = self.beat_patterns[self.current_beat_pattern]
        
        # Check for pattern transition at bar start
        if self.next_beat_pattern is not None and self.beat_position == 0:
            self.current_beat_pattern = self.next_beat_pattern
            self.next_beat_pattern = None
            pattern = self.beat_patterns[self.current_beat_pattern]
            # Update pattern display
            for i in range(min(8, len(self.beat_patterns))):
                led = self.lp.panel.led(i, 0)
                if i == self.current_beat_pattern:
                    led.color = (255, 255, 0)
                else:
                    led.color = (100, 100, 0)
            
        # Play drums for this step
        for drum_name, drum_pattern in pattern['drums'].items():
            if drum_pattern[self.beat_position] == 1:
                wave = self.generate_drum_sound(drum_name)
                threading.Thread(target=lambda: play_wave(wave)).start()
                
        # Visual beat indicator
        self.beat_flash_time = time.time()
        
        # Update beat position
        self.beat_position = (self.beat_position + 1) % self.beats_per_bar
        
    def beat_loop(self):
        """Main beat loop"""
        while self.running:
            if self.beat_on:
                current_time = time.time()
                beat_duration = 60.0 / self.current_tempo / 4  # 16th notes
                
                if current_time - self.last_beat_time >= beat_duration:
                    self.play_beat_step()
                    self.last_beat_time = current_time
                    
            time.sleep(0.001)
            
    def handle_button_press(self, button):
        """Handle button press"""
        x, y = button.x, button.y
        
        # Only handle main grid buttons
        if x >= 8 or y >= 8:
            return
            
        with self.lock:
            self.pressed_keys.add((x, y))
            
        # Bottom row controls
        if y == 7:
            if x == 0:  # Lead
                self.current_instrument = 'lead'
                self.setup_layout()
            elif x == 1:  # Bass
                self.current_instrument = 'bass'
                self.setup_layout()
            elif x == 2:  # Chords
                self.current_instrument = 'chords'
                self.setup_layout()
            elif x == 3:  # Beat on/off
                self.beat_on = not self.beat_on
                if self.beat_on:
                    self.beat_position = 0
                    self.last_beat_time = time.time()
                led = self.lp.panel.led(x, y)
                led.color = (0, 255, 0) if self.beat_on else (255, 0, 0)
            elif x == 4:  # Arpeggiator on/off
                self.arpeggiator_on = not self.arpeggiator_on
                print(f"🎹 Arpeggiator: {'ON' if self.arpeggiator_on else 'OFF'}")
                led = self.lp.panel.led(x, y)
                led.color = (255, 0, 255) if self.arpeggiator_on else (50, 0, 50)
            elif x == 6:  # Octave down
                self.octave_shift = max(-2, self.octave_shift - 1)
                print(f"Octave: {self.octave_shift:+d}")
            elif x == 7:  # Octave up
                self.octave_shift = min(self.max_octave, self.octave_shift + 1)
                print(f"Octave: {self.octave_shift:+d}")
                
        # Top row - beat patterns
        elif y == 0:
            if x < len(self.beat_patterns):
                if self.beat_on:
                    # Queue pattern change for next bar
                    self.next_beat_pattern = x
                    print(f"Pattern '{self.beat_patterns[x]['name']}' queued for next bar")
                else:
                    self.current_beat_pattern = x
                    self.setup_layout()
                    print(f"Pattern: {self.beat_patterns[x]['name']}")
                    
        # Scale notes (rows 2-6)
        elif y >= 2 and y <= 6:
            note_index = (6 - y) * 8 + x
            if note_index < len(self.scale_notes):
                frequency = self.scale_notes[note_index] * (2 ** self.octave_shift)
                
                if self.current_instrument == 'lead':
                    wave = self.generate_synth_sound(frequency)
                elif self.current_instrument == 'bass':
                    wave = self.generate_bass_sound(frequency)
                elif self.current_instrument == 'chords':
                    self.play_scale_chord(note_index)
                    return
                    
                threading.Thread(target=lambda: play_wave(wave)).start()
                self.create_note_effect(x, y)
                
    def play_scale_chord(self, note_index):
        """Play a chord built from the scale"""
        # Build triad
        chord_notes = []
        scale_intervals = self.song['scale']['intervals']
        base_degree = note_index % len(scale_intervals)
        
        for offset in [0, 2, 4]:  # Root, third, fifth
            degree = (base_degree + offset) % len(scale_intervals)
            interval = scale_intervals[degree]
            freq = self.root_note * (2 ** (interval / 12)) * (2 ** self.octave_shift)
            chord_notes.append(freq)
            
        # Generate and mix
        waves = []
        chord_config = self.song.get('chord_sound', {})
        for freq in chord_notes:
            wave = self.generate_synth_sound(freq, chord_config)
            waves.append(wave)
            
        # Mix
        max_len = max(len(w) for w in waves)
        mixed = np.zeros(max_len, dtype=np.float32)
        for wave in waves:
            mixed[:len(wave)] += wave / 32767.0
        mixed = (mixed / len(waves) * 32767 * 0.7).astype(np.int16)
        
        threading.Thread(target=lambda: play_wave(mixed)).start()
        
    def create_note_effect(self, x, y):
        """Create visual effect for played notes"""
        with self.lock:
            self.visual_effects.append({
                'x': x,
                'y': y,
                'start_time': time.time(),
                'duration': 0.3
            })
            
    def handle_button_release(self, button):
        """Handle button release"""
        x, y = button.x, button.y
        if x < 8 and y < 8:
            with self.lock:
                self.pressed_keys.discard((x, y))
                
    def update_display(self):
        """Update visual effects with minimal flickering"""
        while self.running:
            current_time = time.time()

            # Only update display every 50ms to reduce flicker
            if current_time - self.last_display_update < 0.05:
                time.sleep(0.01)
                continue

            self.last_display_update = current_time

            # Update beat sequencer visualization
            if self.beat_on:
                self.update_sequencer_display()

            # Update visual effects
            with self.lock:
                effects_to_remove = []
                for effect in self.visual_effects:
                    age = current_time - effect['start_time']
                    if age < effect['duration']:
                        # Just brighten the note briefly
                        led = self.lp.panel.led(effect['x'], effect['y'])
                        brightness = 1.0 - (age / effect['duration'])
                        led.color = tuple(int(255 * brightness) for _ in range(3))
                    else:
                        effects_to_remove.append(effect)
                        # Restore original color
                        if 2 <= effect['y'] <= 6:
                            note_index = (6 - effect['y']) * 8 + effect['x']
                            if note_index < len(self.scale_notes):
                                led = self.lp.panel.led(effect['x'], effect['y'])
                                led.color = self.get_note_color(note_index)

                for effect in effects_to_remove:
                    self.visual_effects.remove(effect)

            time.sleep(0.01)

    def arpeggiator_loop(self):
        """Arpeggiator - automatically play pressed notes in sequence"""
        while self.running:
            if self.arpeggiator_on and len(self.pressed_keys) > 0:
                current_time = time.time()
                arp_speed = 60.0 / self.current_tempo / 4  # 16th notes

                if current_time - self.last_arp_time > arp_speed:
                    # Get pressed scale keys only
                    scale_keys = [(x, y) for x, y in self.pressed_keys if 2 <= y <= 6]

                    if scale_keys:
                        key = scale_keys[self.arp_index % len(scale_keys)]
                        x, y = key
                        note_index = (6 - y) * 8 + x

                        if note_index < len(self.scale_notes):
                            frequency = self.scale_notes[note_index] * (2 ** self.octave_shift)

                            if self.current_instrument == 'bass':
                                wave = self.generate_bass_sound(frequency, 0.15)
                            else:
                                sound_config = self.song.get(f'{self.current_instrument}_sound', {})
                                sound_config['duration'] = 0.15
                                wave = self.generate_synth_sound(frequency, sound_config)

                            threading.Thread(target=lambda: play_wave(wave)).start()

                        self.arp_index += 1
                        self.last_arp_time = current_time

            time.sleep(0.01)

    def command_loop(self):
        """Terminal command interface for runtime changes"""
        import sys
        print("\n💻 TERMINAL COMMANDS READY!")
        print("Type 'help' for list of commands\n")

        while self.running:
            try:
                cmd = input("> ").strip().lower()

                if not cmd:
                    continue

                parts = cmd.split()
                command = parts[0]

                if command == 'help' or command == 'h':
                    print("\n📋 AVAILABLE COMMANDS:")
                    print("  tempo <bpm>        - Change tempo (e.g., tempo 120)")
                    print("  pattern <num>      - Switch pattern (e.g., pattern 2)")
                    print("  beat               - Toggle beat on/off")
                    print("  arp                - Toggle arpeggiator on/off")
                    print("  volume <type> <n>  - Set volume (e.g., volume drums 0.8)")
                    print("  octave <n>         - Set octave shift (e.g., octave -1)")
                    print("  instrument <type>  - Set instrument (lead/bass/chords)")
                    print("  list               - List all patterns")
                    print("  status             - Show current settings")
                    print("  quit / exit        - Exit program")
                    print()

                elif command == 'tempo' or command == 't':
                    if len(parts) > 1:
                        try:
                            new_tempo = int(parts[1])
                            if 40 <= new_tempo <= 200:
                                self.current_tempo = new_tempo
                                print(f"🎵 Tempo set to {new_tempo} BPM")
                            else:
                                print("❌ Tempo must be between 40-200 BPM")
                        except ValueError:
                            print("❌ Invalid tempo value")
                    else:
                        print(f"Current tempo: {self.current_tempo} BPM")

                elif command == 'pattern' or command == 'p':
                    if len(parts) > 1:
                        try:
                            pattern_num = int(parts[1]) - 1
                            if 0 <= pattern_num < len(self.beat_patterns):
                                if self.beat_on:
                                    self.next_beat_pattern = pattern_num
                                    print(f"🥁 Pattern '{self.beat_patterns[pattern_num]['name']}' queued")
                                else:
                                    self.current_beat_pattern = pattern_num
                                    print(f"🥁 Pattern '{self.beat_patterns[pattern_num]['name']}' selected")
                                    self.setup_layout()
                            else:
                                print(f"❌ Pattern must be 1-{len(self.beat_patterns)}")
                        except ValueError:
                            print("❌ Invalid pattern number")
                    else:
                        print(f"Current pattern: {self.beat_patterns[self.current_beat_pattern]['name']}")

                elif command == 'beat' or command == 'b':
                    self.beat_on = not self.beat_on
                    if self.beat_on:
                        self.beat_position = 0
                        self.last_beat_time = time.time()
                        print("▶️  Beat started")
                    else:
                        print("⏸️  Beat stopped")
                    self.setup_layout()

                elif command == 'arp' or command == 'a':
                    self.arpeggiator_on = not self.arpeggiator_on
                    print(f"🎹 Arpeggiator: {'ON' if self.arpeggiator_on else 'OFF'}")
                    self.setup_layout()

                elif command == 'volume' or command == 'v':
                    if len(parts) >= 3:
                        vol_type = parts[1]
                        try:
                            vol_value = float(parts[2])
                            if 0.0 <= vol_value <= 2.0:
                                if vol_type == 'drums' or vol_type == 'd':
                                    self.drum_volume = vol_value
                                    print(f"🥁 Drum volume: {vol_value}")
                                elif vol_type == 'bass' or vol_type == 'b':
                                    self.bass_volume = vol_value
                                    print(f"🎸 Bass volume: {vol_value}")
                                elif vol_type == 'melody' or vol_type == 'm':
                                    self.melody_volume = vol_value
                                    print(f"🎵 Melody volume: {vol_value}")
                                else:
                                    print("❌ Type must be: drums, bass, or melody")
                            else:
                                print("❌ Volume must be 0.0-2.0")
                        except ValueError:
                            print("❌ Invalid volume value")
                    else:
                        print(f"Drums: {self.drum_volume}, Bass: {self.bass_volume}, Melody: {self.melody_volume}")

                elif command == 'octave' or command == 'o':
                    if len(parts) > 1:
                        try:
                            octave = int(parts[1])
                            if -2 <= octave <= self.max_octave:
                                self.octave_shift = octave
                                print(f"🎹 Octave shift: {octave:+d}")
                            else:
                                print(f"❌ Octave must be -2 to +{self.max_octave}")
                        except ValueError:
                            print("❌ Invalid octave value")
                    else:
                        print(f"Current octave: {self.octave_shift:+d}")

                elif command == 'instrument' or command == 'i':
                    if len(parts) > 1:
                        inst = parts[1]
                        if inst in ['lead', 'bass', 'chords']:
                            self.current_instrument = inst
                            print(f"🎸 Instrument: {inst}")
                            self.setup_layout()
                        else:
                            print("❌ Instrument must be: lead, bass, or chords")
                    else:
                        print(f"Current instrument: {self.current_instrument}")

                elif command == 'list' or command == 'l':
                    print(f"\n📋 AVAILABLE PATTERNS ({len(self.beat_patterns)}):")
                    for i, pattern in enumerate(self.beat_patterns):
                        marker = "→" if i == self.current_beat_pattern else " "
                        print(f"  {marker} [{i+1}] {pattern['name']}")
                    print()

                elif command == 'status' or command == 's':
                    print(f"\n📊 CURRENT STATUS:")
                    print(f"  Song: {self.song_name}")
                    print(f"  Tempo: {self.current_tempo} BPM")
                    print(f"  Beat: {'ON ▶️' if self.beat_on else 'OFF ⏸️'}")
                    print(f"  Arpeggiator: {'ON 🎹' if self.arpeggiator_on else 'OFF'}")
                    print(f"  Pattern: {self.beat_patterns[self.current_beat_pattern]['name']}")
                    print(f"  Instrument: {self.current_instrument}")
                    print(f"  Octave: {self.octave_shift:+d}")
                    print(f"  Volumes - Drums: {self.drum_volume}, Bass: {self.bass_volume}, Melody: {self.melody_volume}")
                    print()

                elif command == 'quit' or command == 'exit' or command == 'q':
                    print("👋 Exiting...")
                    self.running = False
                    break

                else:
                    print(f"❌ Unknown command '{command}'. Type 'help' for commands.")

            except EOFError:
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def event_loop(self):
        """Main event loop"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event:
                if button_event.type == ButtonEvent.PRESS:
                    self.handle_button_press(button_event.button)
                elif button_event.type == ButtonEvent.RELEASE:
                    self.handle_button_release(button_event.button)
            time.sleep(0.001)
            
    def start(self):
        """Start the jam station"""
        print(f"\n🥁 {self.song_name.upper()} - DRUM SEQUENCER 🎵")
        print("=" * 60)
        print(f"Key: {self.song['key']} | Tempo: {self.tempo} BPM")
        print(f"\nAvailable Patterns ({len(self.beat_patterns)}):")
        for i, pattern in enumerate(self.beat_patterns):
            print(f"  [{i+1}] {pattern['name']}")

        print("\n" + "=" * 60)
        print("LAUNCHPAD LAYOUT:")
        print("┌─────────────────────────────────────────────────────────┐")
        print("│ TOP ROW (y=0):    Beat pattern selector (1-8)          │")
        print("│ ROW 2 (y=1):      Live sequencer visualization         │")
        print("│                   🔴 Red = Kick  🟢 Green = Snare       │")
        print("│                   🔵 Blue = Hihat  White = Current step │")
        print("│ ROWS 3-7 (y=2-6): Musical scale pads                   │")
        print("│ BOTTOM (y=7):     Lead|Bass|Chords [▶/■][ARP] Oct-|Oct+ │")
        print("└─────────────────────────────────────────────────────────┘")

        print("\n🎮 HOW TO USE:")
        print("  1. Press button 4 (bottom) to START/STOP beat")
        print("  2. Press button 5 (bottom) for ARPEGGIATOR 🎹")
        print("  3. Press TOP ROW buttons to switch patterns")
        print("  4. Watch ROW 2 visualize your beat in real-time")
        print("  5. Play notes on the main grid (rows 3-7)")
        print("  6. Hold notes & turn on ARP for automatic playing!")
        print("  7. Switch instruments with bottom-left buttons")

        print("\n💡 PATTERN SWITCHING:")
        print("  • Cyan = Active pattern")
        print("  • Orange = Queued (will change at next bar)")
        print("  • Dim = Available patterns")

        print("\n🎹 SCALE COLORS:")
        print("  🔴 RED = Root  🟢 GREEN = Fifth  🟡 YELLOW = Third/Fourth")

        print("\n⌨️  Press Ctrl+C to exit.\n")
        
        # Start threads
        beat_thread = threading.Thread(target=self.beat_loop)
        beat_thread.daemon = True
        beat_thread.start()

        arp_thread = threading.Thread(target=self.arpeggiator_loop)
        arp_thread.daemon = True
        arp_thread.start()

        display_thread = threading.Thread(target=self.update_display)
        display_thread.daemon = True
        display_thread.start()

        command_thread = threading.Thread(target=self.command_loop)
        command_thread.daemon = True
        command_thread.start()

        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nJam session ended! 🎸")

if __name__ == "__main__":
    import sys
    song_file = sys.argv[1] if len(sys.argv) > 1 else 'songs/sweet_caroline.yaml'
    jam = JamStation(song_file)
    jam.start()
