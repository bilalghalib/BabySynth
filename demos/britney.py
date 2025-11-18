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

class ToxicJam:
    def __init__(self, config_file='config.yaml'):
        # Initialize
        self.running = True
        self.lock = threading.Lock()
        
        # Musical setup - C Harmonic Minor (Toxic's scale)
        self.root_note = 261.63  # C4
        self.scale_intervals = [0, 2, 3, 5, 7, 8, 11, 12]  # Harmonic minor
        self.scale_notes = self.generate_scale(self.root_note)
        
        # Extended scale for higher octave
        self.scale_notes.extend(self.generate_scale(self.root_note * 2))
        
        # Drum frequencies (synthetic drums)
        self.drums = {
            'kick': {'freq': 60, 'decay': 0.3, 'noise': 0.1},
            'snare': {'freq': 200, 'decay': 0.1, 'noise': 0.8},
            'hihat': {'freq': 8000, 'decay': 0.05, 'noise': 0.9},
            'clap': {'freq': 1500, 'decay': 0.05, 'noise': 0.7},
        }
        
        # Signature sound frequencies (for the string stabs)
        self.signature_notes = [
            261.63,  # C
            311.13,  # Eb
            349.23,  # F
            311.13,  # Eb
        ]
        
        # Visual states
        self.pressed_keys = set()
        self.drum_hits = {}
        self.visual_effects = []
        
        # Performance modes
        self.octave_shift = 0
        self.arpeggiator_on = False
        self.arp_index = 0
        self.last_arp_time = time.time()
        
        # NOW load config and init
        self.load_config(config_file)
        self.init_launchpad()
        self.setup_layout()
        
    def generate_scale(self, root):
        """Generate scale notes from intervals"""
        notes = []
        for interval in self.scale_intervals:
            # Convert semitone interval to frequency
            freq = root * (2 ** (interval / 12))
            notes.append(freq)
        return notes
        
    def load_config(self, config_file):
        try:
            with open(config_file, 'r') as file:
                config = yaml.safe_load(file)
        except:
            # Continue without config
            pass
            
    def init_launchpad(self):
        self.lp = find_launchpads()[0]
        if self.lp is None:
            print("No Launchpad found. Exiting.")
            exit()
        self.lp.open()
        self.lp.mode = Mode.PROG
        self.clear_grid()
        print("Toxic Jam Station initialized! 🎵")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def setup_layout(self):
        """Set up the visual layout"""
        # Bottom two rows (6-7) for drums
        drum_colors = {
            0: (255, 0, 0),    # Kick - Red
            1: (255, 127, 0),  # Snare - Orange
            2: (255, 255, 0),  # Hihat - Yellow
            3: (255, 0, 255),  # Clap - Magenta
        }
        
        # Drum layout
        for i, color in drum_colors.items():
            if i < 4:
                led = self.lp.panel.led(i, 7)
                led.color = tuple(c // 4 for c in color)  # Dim when not pressed
                led = self.lp.panel.led(i, 6)
                led.color = tuple(c // 4 for c in color)
                
        # Signature sound buttons (right side)
        for i in range(4):
            led = self.lp.panel.led(8, 7 - i)
            led.color = (127, 0, 127)  # Purple for signature sounds
            
        # Scale notes (rows 0-5)
        self.draw_scale()
        
        # Control buttons
        led = self.lp.panel.led(0, 0)  # Octave down
        led.color = (0, 0, 100)
        led = self.lp.panel.led(1, 0)  # Octave up
        led.color = (0, 0, 100)
        led = self.lp.panel.led(7, 0)  # Arpeggiator
        led.color = (100, 0, 100)
        
    def draw_scale(self):
        """Draw the scale notes"""
        # C minor pentatonic positions for easier playing
        scale_layout = [
            [0, 3, 7, 10, 12, 15, 19, 22],  # Row 5
            [2, 5, 8, 12, 14, 17, 20, 24],  # Row 4
            [3, 7, 10, 12, 15, 19, 22, 24], # Row 3
            [5, 8, 12, 14, 17, 20, 24, 26], # Row 2
            [7, 10, 12, 15, 19, 22, 24, 27],# Row 1
        ]
        
        colors = [
            (0, 255, 255),  # Cyan
            (0, 255, 0),    # Green
            (255, 255, 0),  # Yellow
            (255, 127, 0),  # Orange
            (255, 0, 0),    # Red
        ]
        
        for row_idx, row in enumerate(scale_layout):
            y = 5 - row_idx  # Bottom to top
            for x in range(8):
                led = self.lp.panel.led(x, y)
                # Color based on note position in scale
                color_idx = row_idx % len(colors)
                led.color = tuple(c // 3 for c in colors[color_idx])
                
    def generate_drum_sound(self, drum_type):
        """Generate synthetic drum sounds"""
        drum = self.drums[drum_type]
        duration = drum['decay']
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        if drum_type == 'kick':
            # Sine wave with pitch envelope
            pitch_env = np.exp(-35 * t)
            frequency = drum['freq'] * (1 + 2 * pitch_env)
            wave = np.sin(2 * np.pi * frequency * t)
            # Add click
            click = np.random.normal(0, 0.3, len(t)) * np.exp(-100 * t)
            wave = 0.8 * wave + 0.2 * click
            
        elif drum_type == 'snare':
            # Mixed tone and noise
            tone = np.sin(2 * np.pi * drum['freq'] * t)
            noise = np.random.normal(0, 1, len(t))
            wave = (1 - drum['noise']) * tone + drum['noise'] * noise
            # Snappy envelope
            wave *= np.exp(-20 * t)
            
        elif drum_type == 'hihat':
            # High frequency noise
            noise = np.random.normal(0, 1, len(t))
            # High pass filter simulation
            wave = noise * drum['noise']
            wave *= np.exp(-80 * t)
            
        elif drum_type == 'clap':
            # Multiple short bursts
            wave = np.zeros_like(t)
            for i in range(3):
                start = int(i * 0.01 * sample_rate)
                if start < len(t):
                    burst_len = min(int(0.02 * sample_rate), len(t) - start)
                    wave[start:start + burst_len] += np.random.normal(0, 1, burst_len)
            wave *= np.exp(-40 * t)
            
        # Normalize and convert
        wave = np.clip(wave, -1, 1)
        wave = (wave * 32767 * 0.7).astype(np.int16)
        return wave
        
    def generate_synth_sound(self, frequency, duration=0.3, vibrato=False):
        """Generate the signature Eastern-style synth sound"""
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Base wave with harmonics
        wave = np.sin(2 * np.pi * frequency * t)
        wave += 0.3 * np.sin(2 * np.pi * frequency * 2 * t)  # Octave
        wave += 0.2 * np.sin(2 * np.pi * frequency * 3 * t)  # Fifth
        
        if vibrato:
            # Add vibrato for that Eastern feel
            vibrato_freq = 5
            vibrato_amount = 0.02
            frequency_mod = 1 + vibrato_amount * np.sin(2 * np.pi * vibrato_freq * t)
            wave = np.sin(2 * np.pi * frequency * frequency_mod * t)
            
        # Quick attack, sustained release
        attack = 0.01
        attack_samples = int(attack * sample_rate)
        envelope = np.ones_like(t)
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[attack_samples:] = np.exp(-2 * (t[attack_samples:] - attack))
        
        wave *= envelope
        wave = np.clip(wave, -1, 1)
        wave = (wave * 32767 * 0.6).astype(np.int16)
        return wave
        
    def play_signature_riff(self, index):
        """Play one of the signature sound stabs"""
        # Create the characteristic staccato pattern
        note = self.signature_notes[index % len(self.signature_notes)]
        
        # Double the note with slight detuning for thickness
        wave1 = self.generate_synth_sound(note, 0.1, vibrato=True)
        wave2 = self.generate_synth_sound(note * 1.01, 0.1, vibrato=True)
        
        # Mix the waves
        max_len = max(len(wave1), len(wave2))
        mixed = np.zeros(max_len, dtype=np.float32)
        mixed[:len(wave1)] += wave1 / 32767.0
        mixed[:len(wave2)] += wave2 / 32767.0
        mixed = (mixed * 32767 * 0.5).astype(np.int16)
        
        play_wave(mixed)
        
    def handle_button_press(self, button):
        """Handle button press"""
        x, y = button.x, button.y
        
        with self.lock:
            self.pressed_keys.add((x, y))
            
        # Control buttons
        if y == 0:
            if x == 0:  # Octave down
                self.octave_shift = max(-2, self.octave_shift - 1)
                self.update_control_lights()
            elif x == 1:  # Octave up
                self.octave_shift = min(2, self.octave_shift + 1)
                self.update_control_lights()
            elif x == 7:  # Arpeggiator toggle
                self.arpeggiator_on = not self.arpeggiator_on
                led = self.lp.panel.led(x, y)
                led.color = (255, 0, 255) if self.arpeggiator_on else (100, 0, 100)
                
        # Drums (bottom two rows)
        elif y >= 6:
            if x < 4:  # Drum pads
                drum_map = ['kick', 'snare', 'hihat', 'clap']
                drum_type = drum_map[x]
                
                # Play drum
                wave = self.generate_drum_sound(drum_type)
                threading.Thread(target=lambda: play_wave(wave)).start()
                
                # Visual feedback
                self.drum_hits[drum_type] = time.time()
                
            elif x == 8:  # Signature sounds
                sig_index = 7 - y
                threading.Thread(target=self.play_signature_riff, args=(sig_index,)).start()
                
        # Scale notes
        elif 1 <= y <= 5:
            # Calculate note index based on position
            note_index = x + (5 - y) * 2
            
            if note_index < len(self.scale_notes):
                # Apply octave shift
                octave_multiplier = 2 ** self.octave_shift
                frequency = self.scale_notes[note_index] * octave_multiplier
                
                # Play note
                wave = self.generate_synth_sound(frequency, 0.5)
                threading.Thread(target=lambda: play_wave(wave)).start()
                
                # Visual effect
                self.create_note_effect(x, y)
                
    def handle_button_release(self, button):
        """Handle button release"""
        x, y = button.x, button.y
        with self.lock:
            self.pressed_keys.discard((x, y))
            
    def create_note_effect(self, x, y):
        """Create visual effect for played notes"""
        with self.lock:
            self.visual_effects.append({
                'x': x,
                'y': y,
                'radius': 0,
                'max_radius': 2,
                'color': (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            })
            
    def update_control_lights(self):
        """Update octave indicator lights"""
        # Clear octave indicators
        for i in range(5):
            led = self.lp.panel.led(i + 2, 0)
            led.color = (0, 0, 0)
            
        # Show current octave
        octave_pos = 2 + self.octave_shift + 2
        if 2 <= octave_pos <= 6:
            led = self.lp.panel.led(octave_pos, 0)
            led.color = (0, 255, 255)
            
    def arpeggiator_loop(self):
        """Run the arpeggiator"""
        while self.running:
            if self.arpeggiator_on and len(self.pressed_keys) > 0:
                current_time = time.time()
                if current_time - self.last_arp_time > 0.1:  # 10 notes per second
                    # Get pressed scale keys
                    scale_keys = [(x, y) for x, y in self.pressed_keys if 1 <= y <= 5]
                    
                    if scale_keys:
                        # Play next note in sequence
                        key = scale_keys[self.arp_index % len(scale_keys)]
                        x, y = key
                        
                        # Calculate and play note
                        note_index = x + (5 - y) * 2
                        if note_index < len(self.scale_notes):
                            frequency = self.scale_notes[note_index] * (2 ** self.octave_shift)
                            wave = self.generate_synth_sound(frequency, 0.1)
                            threading.Thread(target=lambda: play_wave(wave)).start()
                            
                        self.arp_index += 1
                        self.last_arp_time = current_time
                        
            time.sleep(0.01)
            
    def update_display(self):
        """Update the visual display"""
        while self.running:
            # Update drum hit visuals
            current_time = time.time()
            drum_positions = {
                'kick': (0, 7),
                'snare': (1, 7),
                'hihat': (2, 7),
                'clap': (3, 7)
            }
            
            for drum, pos in drum_positions.items():
                if drum in self.drum_hits:
                    age = current_time - self.drum_hits[drum]
                    if age < 0.1:
                        # Bright flash
                        brightness = 1.0 - (age / 0.1)
                        color = tuple(int(255 * brightness) for _ in range(3))
                        led = self.lp.panel.led(pos[0], pos[1])
                        led.color = color
                        led = self.lp.panel.led(pos[0], 6)
                        led.color = color
                    else:
                        # Return to dim
                        self.setup_layout()
                        
            # Update visual effects
            with self.lock:
                effects_to_remove = []
                for effect in self.visual_effects:
                    effect['radius'] += 0.3
                    if effect['radius'] <= effect['max_radius']:
                        # Draw expanding effect
                        radius = int(effect['radius'])
                        for dx in range(-radius, radius + 1):
                            for dy in range(-radius, radius + 1):
                                if abs(dx) + abs(dy) == radius:  # Diamond shape
                                    ex = effect['x'] + dx
                                    ey = effect['y'] + dy
                                    if 0 <= ex < 9 and 1 <= ey <= 5:
                                        led = self.lp.panel.led(ex, ey)
                                        brightness = 1.0 - (effect['radius'] / effect['max_radius'])
                                        led.color = tuple(int(c * brightness) for c in effect['color'])
                    else:
                        effects_to_remove.append(effect)
                        
                for effect in effects_to_remove:
                    self.visual_effects.remove(effect)
                    
            # Redraw base layout periodically
            if int(current_time * 10) % 10 == 0:
                self.setup_layout()
                
            time.sleep(0.05)
            
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event:
                if button_event.type == ButtonEvent.PRESS:
                    self.handle_button_press(button_event.button)
                elif button_event.type == ButtonEvent.RELEASE:
                    self.handle_button_release(button_event.button)
            time.sleep(0.001)
            
    def start(self):
        """Start the Toxic Jam Station"""
        print("\n🎵 TOXIC JAM STATION 🎵")
        print("=" * 40)
        print("\nLAYOUT:")
        print("• Rows 1-5: C Harmonic Minor Scale (Toxic's key)")
        print("• Row 6-7 (left): Drums - Kick, Snare, HiHat, Clap")
        print("• Right column: Signature sound stabs")
        print("\nCONTROLS:")
        print("• Top left corner: Octave down")
        print("• Next button: Octave up")
        print("• Top right area: Arpeggiator toggle")
        print("\nThe scale is laid out for easy improvisation!")
        print("Press Ctrl+C to exit.\n")
        
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
    jam = ToxicJam()
    jam.start()
