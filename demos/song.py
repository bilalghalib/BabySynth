import sys
import os
# Add parent directory to path so we can import note module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yaml
import time
import random
import threading
import numpy as np
import simpleaudio as sa
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import generate_sine_wave, play_wave

class JamStation:
    def __init__(self, song_file='songs/toxic.yaml'):
        # Initialize
        self.running = True
        self.lock = threading.Lock()
        
        # Load song configuration
        self.load_song(song_file)
        
        # Musical state
        self.pressed_keys = set()
        self.drum_hits = {}
        self.visual_effects = []
        self.chord_mode = False
        self.arpeggiator_on = False
        self.arp_index = 0
        self.last_arp_time = time.time()
        self.octave_shift = 0
        
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
        
        # Generate scale frequencies
        self.scale_notes = []
        for interval in self.song['scale']['intervals']:
            freq = self.root_note * (2 ** (interval / 12))
            self.scale_notes.append(freq)
            
        # Parse chords
        self.chords = {}
        for chord_name, intervals in self.song['chords'].items():
            self.chords[chord_name] = [
                self.root_note * (2 ** (interval / 12)) 
                for interval in intervals
            ]
            
        # Load drum kit
        self.drums = self.song['drums']
        
        # Load signature sounds if defined
        self.signature_sounds = self.song.get('signature_sounds', [])
        
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
                
    def generate_drum_sound(self, drum_name):
        """Generate improved drum sounds with more bass and depth"""
        drum = self.drums[drum_name]
        duration = drum['decay']
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        if drum['type'] == 'kick':
            # Deep kick with sub-bass
            base_freq = drum['freq']
            
            # Sub bass component
            sub_bass = np.sin(2 * np.pi * base_freq * 0.5 * t)  # Half frequency for deep sub
            
            # Main tone with pitch envelope
            pitch_env = np.exp(-drum.get('pitch_decay', 35) * t)
            frequency = base_freq * (1 + drum.get('pitch_mod', 3) * pitch_env)
            main_tone = np.sin(2 * np.pi * frequency * t)
            
            # Click transient
            click_duration = 0.005
            click_samples = int(click_duration * sample_rate)
            click = np.zeros_like(t)
            if click_samples < len(t):
                click[:click_samples] = np.random.normal(0, 0.3, click_samples) * np.linspace(1, 0, click_samples)
            
            # Mix components
            wave = 0.4 * sub_bass + 0.5 * main_tone + 0.1 * click
            
            # Compression-like envelope
            envelope = np.exp(-drum.get('env_decay', 8) * t)
            wave *= envelope
            
        elif drum['type'] == 'snare':
            # Deeper snare with more body
            # Fundamental tone (lower for more body)
            tone1 = np.sin(2 * np.pi * drum['freq'] * t)
            tone2 = np.sin(2 * np.pi * drum['freq'] * 1.5 * t)  # Harmonic
            
            # Snare rattle (noise)
            noise = np.random.normal(0, 1, len(t))
            # Band-pass filter simulation
            noise_hp = np.diff(np.concatenate(([0], noise)))  # Simple high-pass
            
            # Mix with more tone for body
            wave = 0.3 * tone1 + 0.2 * tone2 + 0.5 * noise_hp[:len(t)]
            
            # Snappy envelope with sustain
            attack = int(0.002 * sample_rate)
            wave[:attack] *= np.linspace(0, 1, attack)
            wave[attack:] *= np.exp(-drum.get('env_decay', 15) * t[attack:])
            
        elif drum['type'] == 'hihat':
            # Metallic hi-hat
            # Multiple high frequencies for metallic sound
            frequencies = [drum['freq'], drum['freq'] * 1.23, drum['freq'] * 1.67, drum['freq'] * 2.13]
            wave = np.zeros_like(t)
            
            for freq in frequencies:
                wave += np.sin(2 * np.pi * freq * t) * np.random.uniform(0.5, 1.0)
                
            # Add noise for sizzle
            noise = np.random.normal(0, 0.3, len(t))
            wave = 0.3 * wave + 0.7 * noise
            
            # Quick, sharp envelope
            wave *= np.exp(-drum.get('env_decay', 100) * t)
            
        elif drum['type'] == 'cymbal':
            # Rich crash cymbal
            # Many inharmonic frequencies for realistic cymbal
            fundamentals = [drum['freq'] * ratio for ratio in [1, 1.48, 2.13, 2.89, 3.67, 4.21, 5.33]]
            wave = np.zeros_like(t)
            
            # Build up harmonics
            for i, freq in enumerate(fundamentals):
                # Each partial has slightly different decay
                partial_env = np.exp(-(drum.get('env_decay', 15) + i * 2) * t)
                wave += np.sin(2 * np.pi * freq * t) * partial_env * (1 / (i + 1))
                
            # High frequency shimmer
            shimmer = np.random.normal(0, 0.2, len(t))
            shimmer *= np.exp(-drum.get('env_decay', 15) * t)
            
            wave = 0.7 * wave + 0.3 * shimmer
            
            # Slow attack for realism
            attack_time = 0.01
            attack_samples = int(attack_time * sample_rate)
            wave[:attack_samples] *= np.linspace(0, 1, attack_samples)
            
        elif drum['type'] == 'clap':
            # Multiple short bursts for realistic clap
            wave = np.zeros_like(t)
            # Create 3-4 mini claps
            for i in range(drum.get('bursts', 3)):
                start = int(i * 0.01 * sample_rate)
                if start < len(t):
                    burst_len = min(int(0.02 * sample_rate), len(t) - start)
                    burst = np.random.normal(0, 1, burst_len)
                    burst *= np.exp(-50 * np.linspace(0, 1, burst_len))
                    wave[start:start + burst_len] += burst * (0.7 + 0.3 * np.random.random())
                    
            wave *= np.exp(-drum.get('env_decay', 30) * t)
            
        elif drum['type'] == 'tom':
            # Tom with punch and tone
            freq = drum['freq']
            pitch_env = np.exp(-20 * t)
            frequency = freq * (1 + 0.5 * pitch_env)
            
            # Main tone
            wave = np.sin(2 * np.pi * frequency * t)
            # Add second harmonic for richness
            wave += 0.3 * np.sin(2 * np.pi * frequency * 2 * t)
            
            # Short click
            click = np.random.normal(0, 0.2, int(0.003 * sample_rate))
            wave[:len(click)] += click
            
            wave *= np.exp(-drum.get('env_decay', 10) * t)
            
        else:
            # Generic drum
            wave = np.sin(2 * np.pi * drum['freq'] * t)
            wave *= np.exp(-10 * t)
        
        # Normalize and add compression
        wave = np.tanh(wave * drum.get('gain', 1.0))  # Soft clipping for warmth
        wave = (wave * 32767 * drum.get('volume', 0.7)).astype(np.int16)
        return wave
        
    def generate_synth_sound(self, frequency, sound_config=None):
        """Generate synth sounds based on configuration"""
        if sound_config is None:
            sound_config = {
                'type': 'lead',
                'duration': 0.3,
                'harmonics': [1, 0.3, 0.2],
                'envelope': 'adsr'
            }
            
        duration = sound_config.get('duration', 0.3)
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Generate base waveform
        wave = np.zeros_like(t)
        harmonics = sound_config.get('harmonics', [1])
        
        for i, harmonic_amp in enumerate(harmonics):
            if harmonic_amp > 0:
                harmonic_freq = frequency * (i + 1)
                wave += harmonic_amp * np.sin(2 * np.pi * harmonic_freq * t)
                
        # Apply effects
        if sound_config.get('vibrato'):
            vib_rate = sound_config['vibrato'].get('rate', 5)
            vib_depth = sound_config['vibrato'].get('depth', 0.02)
            vibrato = 1 + vib_depth * np.sin(2 * np.pi * vib_rate * t)
            wave = np.sin(2 * np.pi * frequency * vibrato * t)
            
        if sound_config.get('filter'):
            # Simple lowpass
            cutoff = sound_config['filter'].get('cutoff', 0.5)
            wave = wave * cutoff + np.roll(wave, 1) * (1 - cutoff)
            
        # Apply envelope
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
            
        # Normalize
        wave = np.clip(wave, -1, 1)
        wave = (wave * 32767 * sound_config.get('volume', 0.6)).astype(np.int16)
        return wave
        
    def setup_layout(self):
        """Set up the visual layout based on song configuration"""
        layout = self.song['layout']
        
        # Draw scale/chord pads
        scale_config = layout['scale_pads']
        for pad in scale_config['positions']:
            x, y = pad['x'], pad['y']
            led = self.lp.panel.led(x, y)
            led.color = tuple(c // 3 for c in pad['color'])
            
        # Draw drum pads
        drum_config = layout['drum_pads']
        for pad in drum_config['positions']:
            x, y = pad['x'], pad['y']
            led = self.lp.panel.led(x, y)
            led.color = tuple(c // 3 for c in pad['color'])
            
        # Draw control buttons
        for control in layout['controls']:
            x, y = control['x'], control['y']
            led = self.lp.panel.led(x, y)
            led.color = control['color']
            
        # Draw signature sound pads if configured
        if 'signature_pads' in layout:
            for pad in layout['signature_pads']['positions']:
                x, y = pad['x'], pad['y']
                led = self.lp.panel.led(x, y)
                led.color = pad['color']
                
    def handle_button_press(self, button):
        """Handle button press based on layout"""
        x, y = button.x, button.y
        layout = self.song['layout']
        
        with self.lock:
            self.pressed_keys.add((x, y))
            
        # Check controls
        for control in layout['controls']:
            if control['x'] == x and control['y'] == y:
                self.handle_control(control['function'])
                return
                
        # Check drum pads
        for pad in layout['drum_pads']['positions']:
            if pad['x'] == x and pad['y'] == y:
                self.play_drum(pad['drum'])
                return
                
        # Check scale pads
        for pad in layout['scale_pads']['positions']:
            if pad['x'] == x and pad['y'] == y:
                if self.chord_mode and 'chord' in pad:
                    self.play_chord(pad['chord'])
                else:
                    self.play_note(pad['note'])
                return
                
        # Check signature sounds
        if 'signature_pads' in layout:
            for pad in layout['signature_pads']['positions']:
                if pad['x'] == x and pad['y'] == y:
                    self.play_signature(pad['sound_index'])
                    return
                    
    def handle_control(self, function):
        """Handle control button functions"""
        if function == 'octave_down':
            self.octave_shift = max(-2, self.octave_shift - 1)
            self.update_control_display()
        elif function == 'octave_up':
            self.octave_shift = min(2, self.octave_shift + 1)
            self.update_control_display()
        elif function == 'arpeggiator':
            self.arpeggiator_on = not self.arpeggiator_on
            self.update_control_display()
        elif function == 'chord_mode':
            self.chord_mode = not self.chord_mode
            self.update_control_display()
            
    def play_drum(self, drum_name):
        """Play a drum sound"""
        wave = self.generate_drum_sound(drum_name)
        threading.Thread(target=lambda: play_wave(wave)).start()
        self.drum_hits[drum_name] = time.time()
        
    def play_note(self, note_index):
        """Play a scale note"""
        if note_index < len(self.scale_notes):
            frequency = self.scale_notes[note_index] * (2 ** self.octave_shift)
            sound_config = self.song.get('lead_sound', {})
            wave = self.generate_synth_sound(frequency, sound_config)
            threading.Thread(target=lambda: play_wave(wave)).start()
            
    def play_chord(self, chord_name):
        """Play a chord"""
        if chord_name in self.chords:
            frequencies = self.chords[chord_name]
            waves = []
            sound_config = self.song.get('chord_sound', {})
            
            for freq in frequencies:
                freq_shifted = freq * (2 ** self.octave_shift)
                wave = self.generate_synth_sound(freq_shifted, sound_config)
                waves.append(wave)
                
            # Mix chord notes
            max_len = max(len(w) for w in waves)
            mixed = np.zeros(max_len, dtype=np.float32)
            for wave in waves:
                mixed[:len(wave)] += wave / 32767.0
            mixed = (mixed / len(waves) * 32767 * 0.8).astype(np.int16)
            
            threading.Thread(target=lambda: play_wave(mixed)).start()
            
    def play_signature(self, sound_index):
        """Play a signature sound"""
        if sound_index < len(self.signature_sounds):
            sig_sound = self.signature_sounds[sound_index]
            
            if sig_sound['type'] == 'riff':
                # Play a sequence of notes
                for note in sig_sound['notes']:
                    freq = self.root_note * (2 ** (note['interval'] / 12))
                    duration = 60.0 / self.tempo * note['duration']
                    
                    sound_config = sig_sound.get('sound', {})
                    sound_config['duration'] = duration
                    
                    wave = self.generate_synth_sound(freq, sound_config)
                    play_wave(wave)
                    
                    if 'rest' in note:
                        time.sleep(60.0 / self.tempo * note['rest'])
                        
            elif sig_sound['type'] == 'chord_stab':
                # Play a chord stab
                self.play_chord(sig_sound['chord'])
                
    def update_control_display(self):
        """Update control button visuals"""
        # This would update the LED colors based on state
        # Implementation depends on specific layout
        pass
        
    def handle_button_release(self, button):
        """Handle button release"""
        x, y = button.x, button.y
        with self.lock:
            self.pressed_keys.discard((x, y))
            
    def update_display(self):
        """Update visual effects"""
        while self.running:
            current_time = time.time()
            
            # Update drum hit visuals
            for drum_name, hit_time in list(self.drum_hits.items()):
                age = current_time - hit_time
                if age > 0.2:
                    del self.drum_hits[drum_name]
                else:
                    # Flash effect
                    brightness = 1.0 - (age / 0.2)
                    # Find drum pad position and update LED
                    for pad in self.song['layout']['drum_pads']['positions']:
                        if pad['drum'] == drum_name:
                            led = self.lp.panel.led(pad['x'], pad['y'])
                            flash_color = tuple(int(c * brightness) for c in [255, 255, 255])
                            led.color = flash_color
                            
            # Restore base colors
            if int(current_time * 10) % 5 == 0:
                self.setup_layout()
                
            time.sleep(0.05)
            
    def arpeggiator_loop(self):
        """Arpeggiator implementation"""
        while self.running:
            if self.arpeggiator_on and len(self.pressed_keys) > 0:
                current_time = time.time()
                arp_speed = 60.0 / self.tempo / 4  # 16th notes
                
                if current_time - self.last_arp_time > arp_speed:
                    # Get pressed scale keys
                    scale_positions = []
                    for pad in self.song['layout']['scale_pads']['positions']:
                        if (pad['x'], pad['y']) in self.pressed_keys:
                            scale_positions.append(pad)
                            
                    if scale_positions:
                        # Play next note
                        pad = scale_positions[self.arp_index % len(scale_positions)]
                        self.play_note(pad['note'])
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
        print(f"Tempo: {self.tempo} BPM")
        print(f"Scale: {self.song['scale']['name']}")
        print("\nPress Ctrl+C to exit.\n")
        
        # Start threads
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
    song_file = sys.argv[1] if len(sys.argv) > 1 else 'songs/toxic.yaml'
    jam = JamStation(song_file)
    jam.start()
