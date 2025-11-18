import sys
import os
# Add parent directory to path so we can import note module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Enhanced simon_says_baby.py with quadrants
import yaml
import time
import random
import threading
import numpy as np
import simpleaudio as sa
import os
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import generate_sine_wave, play_wave

class SimonSaysBaby:
    def __init__(self, config_file='config.yaml'):
        self.running = True
        
        # Game state
        self.pattern = []
        self.player_position = 0
        self.showing_pattern = False
        self.level = 1
        
        # Define quadrants (each is 4x4 area)
        self.quadrants = {
            0: [(x, y) for x in range(0, 4) for y in range(0, 4)],      # Top-left
            1: [(x, y) for x in range(5, 9) for y in range(0, 4)],      # Top-right
            2: [(x, y) for x in range(0, 4) for y in range(5, 9)],      # Bottom-left
            3: [(x, y) for x in range(5, 9) for y in range(5, 9)],      # Bottom-right
        }
        
        self.quadrant_colors = [
            (255, 0, 0),    # Red
            (255, 255, 0),  # Yellow
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
        ]
        
        # Fun patterns for each quadrant when lit
        self.quadrant_patterns = [
            'heart',    # Top-left
            'star',     # Top-right
            'smile',    # Bottom-left
            'diamond',  # Bottom-right
        ]
        
        # Animal sounds
        self.animal_sounds = [
            "./sounds/cow.wav",
            "./sounds/duck.wav",
            "./sounds/cat.wav",
            "./sounds/dog.wav",
        ]
        
        # Musical notes as fallback
        self.musical_notes = [
            261.63,  # C
            329.63,  # E
            392.00,  # G
            523.25,  # C (higher)
        ]
        
        self.success_sounds = [
            "./sounds/yay.wav",
            "./sounds/giggle.wav",
            "./sounds/applause.wav"
        ]
        
        # Fun features
        self.streak_count = 0
        self.perfect_timing_window = 0.3
        self.last_press_time = 0
        
        # NOW initialize
        self.load_config(config_file)
        self.init_launchpad()
        
    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            
    def init_launchpad(self):
        self.lp = find_launchpads()[0]
        if self.lp is None:
            print("No Launchpad found. Exiting.")
            exit()
        self.lp.open()
        self.lp.mode = Mode.PROG
        self.clear_grid()
        self.setup_quadrants()
        print("Simon Says Baby (Quadrant Edition) initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def setup_quadrants(self):
        """Set up quadrants with dim colors and divider lines"""
        # Draw dim quadrants
        for quad_idx, positions in self.quadrants.items():
            dim_color = tuple(int(c * 0.1) for c in self.quadrant_colors[quad_idx])
            for x, y in positions:
                led = self.lp.panel.led(x, y)
                led.color = dim_color
                
        # Draw divider cross (column 4 and row 4)
        divider_color = (30, 30, 30)
        for i in range(9):
            led = self.lp.panel.led(4, i)
            led.color = divider_color
            led = self.lp.panel.led(i, 4)
            led.color = divider_color
            
    def get_pattern_positions(self, pattern_type, quadrant):
        """Get positions for fun patterns within a quadrant"""
        base_positions = self.quadrants[quadrant]
        min_x = min(pos[0] for pos in base_positions)
        min_y = min(pos[1] for pos in base_positions)
        
        patterns = {
            'heart': [
                (1, 0), (2, 0),
                (0, 1), (1, 1), (2, 1), (3, 1),
                (0, 2), (1, 2), (2, 2), (3, 2),
                (1, 3), (2, 3),
            ],
            'star': [
                (2, 0),
                (1, 1), (2, 1), (3, 1),
                (0, 2), (1, 2), (2, 2), (3, 2),
                (1, 3), (3, 3),
            ],
            'smile': [
                (0, 1), (3, 1),
                (0, 2), (3, 2),
                (1, 3), (2, 3),
            ],
            'diamond': [
                (1, 0), (2, 0),
                (0, 1), (1, 1), (2, 1), (3, 1),
                (0, 2), (1, 2), (2, 2), (3, 2),
                (1, 3), (2, 3),
            ],
        }
        
        pattern = patterns.get(pattern_type, [])
        return [(min_x + dx, min_y + dy) for dx, dy in pattern 
                if 0 <= min_x + dx < 9 and 0 <= min_y + dy < 9]
        
    def light_quadrant(self, quad_idx, bright=True, pattern=False):
        """Light up a quadrant with optional pattern"""
        if pattern and bright:
            # Show fun pattern
            positions = self.get_pattern_positions(self.quadrant_patterns[quad_idx], quad_idx)
        else:
            # Show full quadrant
            positions = self.quadrants[quad_idx]
            
        color = self.quadrant_colors[quad_idx] if bright else tuple(int(c * 0.1) for c in self.quadrant_colors[quad_idx])
        
        for x, y in positions:
            led = self.lp.panel.led(x, y)
            led.color = color
            
    def play_quadrant_sound(self, quad_idx):
        """Play sound for quadrant with pitch based on timing"""
        # Check timing for perfect hit bonus
        current_time = time.time()
        time_since_show = current_time - self.last_press_time
        
        # Try animal sound first
        if quad_idx < len(self.animal_sounds) and os.path.exists(self.animal_sounds[quad_idx]):
            try:
                wave_obj = sa.WaveObject.from_wave_file(self.animal_sounds[quad_idx])
                wave_obj.play()
                return
            except:
                pass
                
        # Musical note with timing bonus
        freq = self.musical_notes[quad_idx]
        
        # Perfect timing = higher pitch
        if time_since_show < self.perfect_timing_window:
            freq *= 1.2  # Slightly higher for perfect timing
            
        duration = 0.5
        t = np.linspace(0, duration, int(44100 * duration), False)
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-2 * t)
        wave = wave * envelope
        wave = (wave * 32767).astype(np.int16)
        play_wave(wave)
        
    def show_pattern(self):
        """Show pattern with fun animations"""
        self.showing_pattern = True
        time.sleep(0.5)
        
        for i, quad_idx in enumerate(self.pattern):
            # Light up with pattern
            self.light_quadrant(quad_idx, bright=True, pattern=True)
            self.play_quadrant_sound(quad_idx)
            self.last_press_time = time.time()
            
            time.sleep(0.6)
            
            # Dim it
            self.setup_quadrants()
            time.sleep(0.2)
            
        self.showing_pattern = False
        self.player_position = 0
        
    def create_ripple(self, quad_idx):
        """Create ripple effect in quadrant"""
        positions = self.quadrants[quad_idx]
        center_x = sum(p[0] for p in positions) // len(positions)
        center_y = sum(p[1] for p in positions) // len(positions)
        
        for radius in range(1, 4):
            for x, y in positions:
                dist = abs(x - center_x) + abs(y - center_y)
                if dist == radius:
                    led = self.lp.panel.led(x, y)
                    led.color = (255, 255, 255)
            time.sleep(0.05)
            
        # Clear ripple
        self.setup_quadrants()
        
    def handle_button_press(self, button):
        """Handle button press"""
        if self.showing_pattern:
            return
            
        x, y = button.x, button.y
        
        # Find which quadrant was pressed
        quad_pressed = None
        for quad_idx, positions in self.quadrants.items():
            if (x, y) in positions:
                quad_pressed = quad_idx
                break
                
        if quad_pressed is not None:
            # Light up and play sound
            self.light_quadrant(quad_pressed, bright=True, pattern=True)
            self.play_quadrant_sound(quad_pressed)
            
            # Create ripple effect
            threading.Thread(target=self.create_ripple, args=(quad_pressed,)).start()
            
            # Check if correct
            if quad_pressed == self.pattern[self.player_position]:
                self.player_position += 1
                
                # Check timing for streak
                current_time = time.time()
                if current_time - self.last_press_time < self.perfect_timing_window:
                    self.streak_count += 1
                    if self.streak_count >= 3:
                        # Bonus celebration for streak!
                        threading.Thread(target=self.streak_celebration).start()
                
                # Completed pattern!
                if self.player_position >= len(self.pattern):
                    time.sleep(0.3)
                    self.success_animation()
                    self.play_success_sound()
                    
                    # Add to pattern
                    self.add_to_pattern()
                    time.sleep(1.0)
                    self.setup_quadrants()
                    threading.Thread(target=self.show_pattern).start()
            else:
                # Wrong - be gentle
                self.streak_count = 0
                time.sleep(0.5)
                self.gentle_retry()
                
            # Dim after press
            threading.Timer(0.3, self.setup_quadrants).start()
            
    def streak_celebration(self):
        """Special celebration for perfect timing streak"""
        # Rainbow wave across all quadrants
        for _ in range(2):
            for quad_idx in range(4):
                self.light_quadrant(quad_idx, bright=True, pattern=False)
                time.sleep(0.1)
            for quad_idx in range(4):
                self.setup_quadrants()
                time.sleep(0.1)
                
    def add_to_pattern(self):
        """Add to pattern"""
        if len(self.pattern) < 6:  # Max 6 for baby
            self.pattern.append(random.randint(0, 3))
        else:
            self.pattern = [random.randint(0, 3)]
            self.streak_count = 0
            
    def gentle_retry(self):
        """Gentle retry"""
        # Soft pulse all quadrants
        for _ in range(2):
            for quad_idx in range(4):
                self.light_quadrant(quad_idx, bright=True, pattern=False)
            time.sleep(0.2)
            self.setup_quadrants()
            time.sleep(0.2)
            
        time.sleep(0.5)
        threading.Thread(target=self.show_pattern).start()
        
    def success_animation(self):
        """Fun success animation"""
        # Each quadrant shows its pattern in sequence
        for quad_idx in range(4):
            self.light_quadrant(quad_idx, bright=True, pattern=True)
            time.sleep(0.15)
        time.sleep(0.5)
        self.setup_quadrants()
        
    def play_success_sound(self):
        """Play success sound"""
        for sound_file in self.success_sounds:
            if os.path.exists(sound_file):
                try:
                    wave_obj = sa.WaveObject.from_wave_file(sound_file)
                    wave_obj.play()
                    return
                except:
                    pass
                    
        # Fallback chord
        frequencies = [261.63, 329.63, 392.00, 523.25]
        waves = []
        for freq in frequencies:
            t = np.linspace(0, 0.5, int(44100 * 0.5), False)
            wave = np.sin(2 * np.pi * freq * t) * 0.25
            waves.append(wave)
        combined = np.sum(waves, axis=0)
        combined = (combined * 32767).astype(np.int16)
        play_wave(combined)
        
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Simon Says Baby"""
        print("Starting Simon Says Baby - Quadrant Edition!")
        print("🔴 Top-left    🟡 Top-right")
        print("🟢 Bottom-left 🔵 Bottom-right")
        print("⚡ Press quickly for perfect timing streaks!")
        print("Press Ctrl+C to exit.")
        
        self.add_to_pattern()
        threading.Timer(1.0, self.show_pattern).start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nSimon Says Baby stopped.")

if __name__ == "__main__":
    simon = SimonSaysBaby()
    simon.start()
