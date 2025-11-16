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
        self.chord_mode = False
        self.arpeggiator_on = False
        self.arp_index = 0
        self.last_arp_time = time.time()
        self.octave_shift = 0
        
        # Beat system
        self.beat_on = False
        self.current_beat_pattern = 0
        self.next_beat_pattern = None
        self.beat_position = 0
        self.last_beat_time = time.time()
        self.beats_per_bar = 16  # 16th notes
        self.current_tempo = self.tempo
        
        # Instrument modes
        self.current_instrument = 'lead'  # 'lead', 'bass', 'chords'
        
        # Scale guidance
        self.scale_degrees = {
            0: 'root',      # Tonic - Always safe
            2: 'second',    # Passing tone
            3: 'third',     # Chord tone
            4: 'third',     # Minor/major third
            5: 'fourth',    # Subdominant
            7: 'fifth',     # Dominant - Very safe
            8: 'sixth',     # Color tone
            9: 'sixth',     # Minor/major sixth
            10: 'seventh',  # Leading tone
            11: 'seventh',  # Major seventh
            12: 'octave'   # Root again
        }
        
        # Initialize hardware
        self.init_launchpad()
        self.setup_layout()
        
    def load_song(self, song_file):
        """Load song configuration from YAML"""
        with open(song_file, 'r') as file:
            self.song = yaml.safe_load(file)
            
        # Parse musical data
        self.song_name = self.song['name']
        self.tempo = self.song['tempo']
        self.root_note = self.song['root_note']
        
        # Generate scale frequencies for multiple octaves
        self.scale_notes = []
        octave_range = 3  # Cover 3 octaves
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
        self.beat_patterns = self.song['beat_patterns']
        
        # Load tempo changes if specified
        self.tempo_changes = self.song.get('tempo_changes', {})
        
    def get_note_color(self, note_index):
        """Get color for a note based on its scale degree"""
        degree = note_index % len(self.song['scale']['intervals'])
        interval = self.song['scale']['intervals'][degree]
        
        # Color coding for scale degrees
        colors = {
            0: (255, 0, 0),      # Root - Red (home)
            1: (255, 64, 0),     # 2nd - Orange-red
            2: (255, 127, 0),    # Minor 3rd - Orange
            3: (255, 191, 0),    # Major 3rd - Yellow-orange
            4: (255, 255, 0),    # 4th - Yellow
            5: (127, 255, 0),    # Tritone - Yellow-green
            6: (0, 255, 0),      # 5th - Green (very stable)
            7: (0, 255, 127),    # Minor 6th - Cyan-green
            8: (0, 255, 255),    # Major 6th - Cyan
            9: (0, 127, 255),    # Minor 7th - Blue-cyan
            10: (0, 0, 255),     # Major 7th - Blue
            11: (127, 0, 255),   # Leading tone - Purple
            12: (255, 0, 255),   # Octave - Magenta (home)
        }
        
        # Brightness based on stability
        stability = {
            0: 1.0,   # Root - brightest
            7: 0.9,   # Fifth - very bright
            4: 0.7,   # Third - bright
            3: 0.7,
            5: 0.6,   # Fourth - medium
            2: 0.5,   # Second - dimmer
            9: 0.5,   # Sixth
            8: 0.5,
            10: 0.4,  # Seventh - dim
            11: 0.4,
        }
        
        base_color = colors.get(interval, (128, 128, 128))
        brightness = stability.get(interval, 0.5)
        
        # Adjust for instrument mode
        if self.current_instrument == 'bass':
            brightness *= 0.7  # Darker for bass
        elif self.current_instrument == 'chords':
            brightness *= 0.8
            
        return tuple(int(c * brightness) for c in base_color)
        
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
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def generate_bass_sound(self, frequency, duration=0.3):
        """Generate deep bass sounds"""
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Sub bass with harmonics
        wave = np.sin(2 * np.pi * frequency * t)
        wave += 0.5 * np.sin(2 * np.pi * frequency * 2 * t)  # Octave
        wave += 0.3 * np.sin(2 * np.pi * frequency * 3 * t)  # Fifth
        
        # Pluck envelope
        pluck_envelope = np.exp(-4 * t)
        sustain_level = 0.3
        envelope = pluck_envelope * (1 - sustain_level) + sustain_level
        envelope *= np.exp(-1 * t)  # Overall decay
        
        wave *= envelope
        
        # Soft saturation for warmth
        wave = np.tanh(wave * 1.5)
        
        wave = (wave * 32767 * 0.8).astype(np.int16)
        return wave
        
    def generate_drum_sound(self, drum_name):
        """Enhanced drum sounds"""
        drum = self.drums[drum_name]
        duration = drum['decay']
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        if drum['type'] == 'kick':
            # Deep kick with punch
            base_freq = drum['freq']
            
            # Sub component
            sub = np.sin(2 * np.pi * base_freq * 0.5 * t)
            
            # Main body with pitch sweep
            pitch_env = np.exp(-drum.get('pitch_decay', 35) * t)
            frequency = base_freq * (1 + drum.get('pitch_mod', 4) * pitch_env)
            body = np.sin(2 * np.pi * frequency * t)
            
            # Click transient
            click = np.zeros_like(t)
            click_samples = int(0.005 * sample_rate)
            if click_samples < len(t):
                click[:click_samples] = np.random.normal(0, 0.5, click_samples)
                click[:click_samples] *= np.linspace(1, 0, click_samples)
            
            # Mix
            wave = 0.4 * sub + 0.5 * body + 0.1 * click
            wave *= np.exp(-drum.get('env_decay', 8) * t)
            
        elif drum['type'] == 'snare':
            # Punchy snare
            tone1 = np.sin(2 * np.pi * drum['freq'] * t)
            tone2 = np.sin(2 * np.pi * drum['freq'] * 1.7 * t)
            
            noise = np.random.normal(0, 1, len(t))
            # Simple high-pass effect
            noise_hp = np.diff(np.concatenate(([0], noise)))
            
            wave = 0.3 * tone1 + 0.2 * tone2 + 0.5 * noise_hp[:len(t)]
            
            # Snappy envelope
            attack = int(0.002 * sample_rate)
            wave[:attack] *= np.linspace(0, 1, attack)
            wave[attack:] *= np.exp(-drum.get('env_decay', 20) * t[attack:])
            
        elif drum['type'] == 'hihat':
            # Crisp hi-hat
            frequencies = [drum['freq'], drum['freq'] * 1.23, drum['freq'] * 1.67]
            wave = np.zeros_like(t)
            
            for freq in frequencies:
                wave += np.sin(2 * np.pi * freq * t) * np.random.uniform(0.3, 1.0)
                
            noise = np.random.normal(0, 0.4, len(t))
            wave = 0.4 * wave + 0.6 * noise
            wave *= np.exp(-drum.get('env_decay', 100) * t)
            
        elif drum['type'] == 'crash':
            # Big crash cymbal
            fundamentals = [drum['freq'] * ratio for ratio in [1, 1.48, 2.13, 2.89, 3.67, 4.21, 5.33, 6.79]]
            wave = np.zeros_like(t)
            
            for i, freq in enumerate(fundamentals):
                partial_env = np.exp(-(drum.get('env_decay', 12) + i * 1.5) * t)
                wave += np.sin(2 * np.pi * freq * t) * partial_env * (1 / (i + 1))
                
            shimmer = np.random.normal(0, 0.3, len(t))
            shimmer *= np.exp(-drum.get('env_decay', 12) * t)
            
            wave = 0.6 * wave + 0.4 * shimmer
            
            # Slow attack
            attack_samples = int(0.02 * sample_rate)
            wave[:attack_samples] *= np.linspace(0, 1, attack_samples)
            
        elif drum['type'] == 'tom':
            freq = drum['freq']
            pitch_env = np.exp(-25 * t)
            frequency = freq * (1 + 1.0 * pitch_env)
            
            wave = np.sin(2 * np.pi * frequency * t)
            wave += 0.3 * np.sin(2 * np.pi * frequency * 2 * t)
            
            # Punch
            punch_samples = int(0.003 * sample_rate)
            wave[:punch_samples] += np.random.normal(0, 0.3, min(punch_samples, len(wave)))
            
            wave *= np.exp(-drum.get('env_decay', 12) * t)
            
        elif drum['type'] == 'clap':
            wave = np.zeros_like(t)
            for i in range(4):
                start = int(i * 0.01 * sample_rate)
                if start < len(t):
                    burst_len = min(int(0.015 * sample_rate), len(t) - start)
                    burst = np.random.normal(0, 1, burst_len)
                    burst *= np.exp(-60 * np.linspace(0, 1, burst_len))
                    wave[start:start + burst_len] += burst * (0.6 + 0.4 * np.random.random())
                    
            wave *= np.exp(-drum.get('env_decay', 30) * t)
            
        elif drum['type'] == 'cowbell':
            # Classic cowbell
            freq1 = drum['freq']
            freq2 = freq1 * 1.48  # Inharmonic interval
            
            wave = np.sin(2 * np.pi * freq1 * t)
            wave += 0.6 * np.sin(2 * np.pi * freq2 * t)
            
            # Metallic attack
            wave *= np.exp(-drum.get('env_decay', 25) * t)
            
        else:
            wave = np.sin(2 * np.pi * drum['freq'] * t)
            wave *= np.exp(-10 * t)
        
        # Normalize and compress
        wave = np.tanh(wave * drum.get('gain', 1.0))
        wave = (wave * 32767 * drum.get('volume', 0.7)).astype(np.int16)
        return wave
        
    def play_beat_step(self):
        """Play a single step of the current beat pattern"""
        if not self.beat_on:
            return
            
        pattern = self.beat_patterns[self.current_beat_pattern]
        
        # Check for pattern transition
        if self.next_beat_pattern is not None and self.beat_position == 0:
            self.current_beat_pattern = self.next_beat_pattern
            self.next_beat_pattern = None
            pattern = self.beat_patterns[self.current_beat_pattern]
            
        # Play drums for this step
        for drum_name, drum_pattern in pattern['drums'].items():
            if drum_pattern[self.beat_position] == 1:
                wave = self.generate_drum_sound(drum_name)
                threading.Thread(target=lambda: play_wave(wave)).start()
                
        # Update beat position
        self.beat_position = (self.beat_position + 1) % self.beats_per_bar
        
        # Update tempo if needed
        self.update_tempo()
        
    def update_tempo(self):
        """Handle tempo changes"""
        if 'gradual_speedup' in self.tempo_changes:
            speedup = self.tempo_changes['gradual_speedup']
            elapsed_bars = self.beat_position // self.beats_per_bar
            tempo_increase = speedup['rate'] * elapsed_bars
            self.current_tempo = min(self.tempo + tempo_increase, speedup['max_tempo'])
            
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
            
    def generate_synth_sound(self, frequency, sound_config=None):
        """Generate various synth sounds"""
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
                
        # Effects
        if sound_config.get('vibrato'):
            vib_rate = sound_config['vibrato'].get('rate', 5)
            vib_depth = sound_config['vibrato'].get('depth', 0.02)
            vibrato = 1 + vib_depth * np.sin(2 * np.pi * vib_rate * t)
            wave = np.sin(2 * np.pi * frequency * vibrato * t)
            
        # Envelope
        env_type = sound_config.get('envelope', 'adsr')
        if env_type == 'adsr':
            attack = sound_config.get('attack', 0.01)
            decay = sound_config.get('decay', 0.1)
            sustain = sound_config.get('sustain', 0.7)
            release = sound_config.get('release', 0.2)
            
            attack_samples = int(attack * sample_rate)
            decay_samples = int(decay * sample_rate)
            
            envelope = np.ones_like(t) * sustain
            if attack_samples > 0:
                envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
            if decay_samples > 0 and attack_samples + decay_samples < len(t):
                envelope[attack_samples:attack_samples + decay_samples] = np.linspace(1, sustain, decay_samples)
                
            wave *= envelope
            
        elif env_type == 'percussive':
            wave *= np.exp(-sound_config.get('decay_rate', 5) * t)
            
        wave = np.clip(wave, -1, 1)
        wave = (wave * 32767 * sound_config.get('volume', 0.6)).astype(np.int16)
        return wave
        
    def setup_layout(self):
        """Set up the visual layout with color-coded scales"""
        # Clear first
        self.clear_grid()
        
        # Scale pads - 3 octaves (rows 2-6)
        note_index = 0
        for y in range(5, 1, -1):  # Bottom to top
            for x in range(8):
                if note_index < len(self.scale_notes):
                    led = self.lp.panel.led(x, y)
                    led.color = self.get_note_color(note_index)
                    note_index += 1
                    
        # Instrument selector (top row)
        instruments = [
            ('lead', (255, 255, 0)),
            ('bass', (255, 0, 255)),
            ('chords', (0, 255, 255))
        ]
        for i, (inst, color) in enumerate(instruments):
            led = self.lp.panel.led(i + 3, 0)
            if self.current_instrument == inst:
                led.color = color
            else:
                led.color = tuple(c // 4 for c in color)
                
        # Beat controls (right column)
        # Beat on/off
        led = self.lp.panel.led(8, 7)
        led.color = (0, 255, 0) if self.beat_on else (255, 0, 0)
        
        # Beat patterns
        for i in range(min(4, len(self.beat_patterns))):
            led = self.lp.panel.led(8, 6 - i)
            if i == self.current_beat_pattern:
                led.color = (255, 255, 0)
            else:
                led.color = (100, 100, 0)
                
        # Control buttons
        led = self.lp.panel.led(0, 0)  # Octave down
        led.color = (0, 0, 100)
        led = self.lp.panel.led(1, 0)  # Octave up  
        led.color = (0, 0, 100)
        led = self.lp.panel.led(7, 0)  # Arpeggiator
        led.color = (100, 0, 100) if not self.arpeggiator_on else (255, 0, 255)
        
        # Visual hint for root notes
        self.highlight_root_notes()
        
    def highlight_root_notes(self):
        """Make root notes pulse gently"""
        # This would be called periodically to make root notes more visible
        pass
        
    def handle_button_press(self, button):
        """Handle button press"""
        x, y = button.x, button.y
        
        with self.lock:
            self.pressed_keys.add((x, y))
            
        # Instrument selector
        if y == 0:
            if x == 0:  # Octave down
                self.octave_shift = max(-2, self.octave_shift - 1)
                self.setup_layout()
            elif x == 1:  # Octave up
                self.octave_shift = min(2, self.octave_shift + 1)
                self.setup_layout()
            elif x == 3:  # Lead
                self.current_instrument = 'lead'
                self.setup_layout()
            elif x == 4:  # Bass
                self.current_instrument = 'bass'
                self.setup_layout()
            elif x == 5:  # Chords
                self.current_instrument = 'chords'
                self.setup_layout()
            elif x == 7:  # Arpeggiator
                self.arpeggiator_on = not self.arpeggiator_on
                self.setup_layout()
                
        # Beat controls
        elif x == 8:
            if y == 7:  # Beat on/off
                self.beat_on = not self.beat_on
                if self.beat_on:
                    self.beat_position = 0
                    self.last_beat_time = time.time()
                self.setup_layout()
            elif y >= 2 and y <= 6:  # Beat patterns
                pattern_index = 6 - y
                if pattern_index < len(self.beat_patterns):
                    if self.beat_on:
                        # Queue pattern change for next bar
                        self.next_beat_pattern = pattern_index
                    else:
                        self.current_beat_pattern = pattern_index
                    self.setup_layout()
                    
        # Scale notes
        elif y >= 2 and y <= 6:
            note_index = (6 - y) * 8 + x
            if note_index < len(self.scale_notes):
                frequency = self.scale_notes[note_index] * (2 ** self.octave_shift)
                
                if self.current_instrument == 'lead':
                    wave = self.generate_synth_sound(frequency)
                elif self.current_instrument == 'bass':
                    wave = self.generate_bass_sound(frequency)
                elif self.current_instrument == 'chords':
                    # Play a chord based on scale degree
                    self.play_scale_chord(note_index)
                    return
                    
                threading.Thread(target=lambda: play_wave(wave)).start()
                self.create_note_effect(x, y, note_index)
                
    def play_scale_chord(self, note_index):
        """Play a chord built from the scale"""
        # Build triad from scale
        chord_notes = []
        scale_intervals = self.song['scale']['intervals']
        base_degree = note_index % len(scale_intervals)
        
        # Get root, third, fifth from scale
        for offset in [0, 2, 4]:  # Scale degrees
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
        
    def create_note_effect(self, x, y, note_index):
        """Create visual effect showing scale degree"""
        with self.lock:
            color = self.get_note_color(note_index)
            self.visual_effects.append({
                'x': x,
                'y': y,
                'radius': 0,
                'max_radius': 2,
                'color': color,
                'start_time': time.time()
            })
            
    def handle_button_release(self, button):
        """Handle button release"""
        x, y = button.x, button.y
        with self.lock:
            self.pressed_keys.discard((x, y))
            
    def update_display(self):
        """Update visual effects and beat indicators"""
        while self.running:
            current_time = time.time()
            
            # Update beat indicator
            if self.beat_on:
                # Flash on beat
                if self.beat_position % 4 == 0:  # Every quarter note
                    led = self.lp.panel.led(8, 7)
                    led.color = (255, 255, 255)
                else:
                    led = self.lp.panel.led(8, 7)
                    led.color = (0, 255, 0)
                    
            # Update visual effects
            with self.lock:
                effects_to_remove = []
                for effect in self.visual_effects:
                    age = current_time - effect['start_time']
                    if age < 0.5:
                        effect['radius'] = age * 4
                        # Redraw effect
                        radius = int(effect['radius'])
                        for dx in range(-radius, radius + 1):
                            for dy in range(-radius, radius + 1):
                                if abs(dx) + abs(dy) == radius:
                                    ex = effect['x'] + dx
                                    ey = effect['y'] + dy
                                    if 0 <= ex < 9 and 2 <= ey <= 6:
                                        led = self.lp.panel.led(ex, ey)
                                        brightness = 1.0 - (age / 0.5)
                                        flash_color = tuple(int(255 * brightness) for _ in range(3))
                                        led.color = flash_color
                    else:
                        effects_to_remove.append(effect)
                        
                for effect in effects_to_remove:
                    self.visual_effects.remove(effect)
                    
            # Refresh layout periodically
            if int(current_time * 2) % 2 == 0:
                self.setup_layout()
                
            time.sleep(0.05)
            
    def arpeggiator_loop(self):
        """Arpeggiator with scale awareness"""
        while self.running:
            if self.arpeggiator_on and len(self.pressed_keys) > 0:
                current_time = time.time()
                arp_speed = 60.0 / self.current_tempo / 4
                
                if current_time - self.last_arp_time > arp_speed:
                    # Get pressed scale keys
                    scale_keys = [(x, y) for x, y in self.pressed_keys if 2 <= y <= 6]
                    
                    if scale_keys:
                        key = scale_keys[self.arp_index % len(scale_keys)]
                        x, y = key
                        note_index = (6 - y) * 8 + x
                        
                        if note_index < len(self.scale_notes):
                            frequency = self.scale_notes[note_index] * (2 ** self.octave_shift)
                            
                            if self.current_instrument == 'bass':
                                wave = self.generate_bass_sound(frequency, 0.1)
                            else:
                                wave = self.generate_synth_sound(frequency)
                                
                            threading.Thread(target=lambda: play_wave(wave)).start()
                            
                        self.arp_index += 1
                        self.last_arp_time = current_time
                        
            time.sleep(0.01)
            
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
        print(f"\n🎵 {self.song_name.upper()} JAM STATION 🎵")
        print("=" * 50)
        print(f"Key: {self.song['key']}")
        print(f"Starting Tempo: {self.tempo} BPM")
        print(f"Scale: {self.song['scale']['name']}")
        print("\nCOLOR GUIDE:")
        print("🔴 RED = Root note (home)")
        print("🟢 GREEN = Fifth (very stable)")
        print("🟡 YELLOW = Third/Fourth (chord tones)")
        print("🔵 BLUE = Seventh (tension)")
        print("🟣 PURPLE = Leading tones")
        print("\nCONTROLS:")
        print("• Top Row: Instrument selector (Lead/Bass/Chords)")
        print("• Right Column: Beat on/off and patterns")
        print("• Main Grid: 3 octaves of scale notes")
        print("\nPress Ctrl+C to exit.\n")
        
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
