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

class SleepyStars:
    def __init__(self, config_file='config.yaml'):
        self.load_config(config_file)
        self.init_launchpad()
        self.running = True
        self.stars = {}  # {(x,y): {'brightness': 0-1, 'sleepiness': 0-1, 'twinkle_phase': 0-2π}}
        self.moon_phase = 0
        self.lock = threading.Lock()
        
        # Lullaby notes (pentatonic for pleasant sound)
        self.lullaby_notes = [
            261.63,   # C
            293.66,   # D  
            329.63,   # E
            392.00,   # G
            440.00,   # A
        ]
        
        # Star colors (warm whites and soft yellows)
        self.star_colors = [
            (255, 248, 220),  # Cornsilk
            (255, 250, 205),  # Lemon chiffon
            (255, 255, 224),  # Light yellow
            (245, 245, 220),  # Beige
            (255, 239, 213),  # Papaya whip
        ]
        
        # Create initial stars
        self.create_night_sky()
        
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
        print("Sleepy Stars initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def create_night_sky(self):
        """Create initial star field"""
        # Create 15-20 stars randomly placed
        num_stars = random.randint(15, 20)
        for _ in range(num_stars):
            x = random.randint(0, 8)
            y = random.randint(0, 8)
            if (x, y) not in self.stars:
                self.stars[(x, y)] = {
                    'brightness': random.uniform(0.3, 1.0),
                    'sleepiness': 0,
                    'twinkle_phase': random.uniform(0, 2 * np.pi),
                    'twinkle_speed': random.uniform(0.02, 0.05),
                    'color': random.choice(self.star_colors),
                    'yawning': False,
                    'yawn_progress': 0
                }
                
    def play_yawn_sound(self, x, y):
        """Play a sleepy yawn sound (descending notes)"""
        # Map position to starting note
        base_index = (x + y) % len(self.lullaby_notes)
        
        # Play 3 descending notes
        for i in range(3):
            note_index = (base_index - i) % len(self.lullaby_notes)
            freq = self.lullaby_notes[note_index]
            
            # Lower frequency for sleepier sound
            freq = freq * 0.5
            
            duration = 0.3
            t = np.linspace(0, duration, int(44100 * duration), False)
            
            # Soft, mellow tone
            wave = np.sin(2 * np.pi * freq * t)
            # Add slight vibrato for yawn effect
            vibrato = 1 + 0.02 * np.sin(2 * np.pi * 6 * t)
            wave = wave * vibrato
            
            # Soft envelope
            envelope = np.sin(np.pi * t / duration) * 0.3
            wave = wave * envelope
            
            wave = (wave * 32767).astype(np.int16)
            play_wave(wave)
            time.sleep(0.2)
            
    def make_star_yawn(self, x, y):
        """Make a star yawn when pressed"""
        with self.lock:
            if (x, y) in self.stars:
                star = self.stars[(x, y)]
                star['yawning'] = True
                star['yawn_progress'] = 0
                star['sleepiness'] = min(1.0, star['sleepiness'] + 0.3)
                
        # Play yawn sound
        threading.Thread(target=self.play_yawn_sound, args=(x, y)).start()
        
        # Create "yawn" effect - star grows and shrinks
        threading.Thread(target=self.yawn_animation, args=(x, y)).start()
        
    def yawn_animation(self, x, y):
        """Animate a yawning star"""
        # Make nearby stars sleepy too
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 9 and 0 <= ny < 9 and (nx, ny) in self.stars:
                    with self.lock:
                        neighbor = self.stars[(nx, ny)]
                        neighbor['sleepiness'] = min(1.0, neighbor['sleepiness'] + 0.1)
                        
    def handle_button_press(self, button):
        """Handle button press"""
        x, y = button.x, button.y
        
        if (x, y) in self.stars:
            # Make existing star yawn
            self.make_star_yawn(x, y)
        else:
            # Create a new sleepy star
            with self.lock:
                self.stars[(x, y)] = {
                    'brightness': 0.1,  # Starts dim
                    'sleepiness': 0.5,  # Already a bit sleepy
                    'twinkle_phase': 0,
                    'twinkle_speed': 0.03,
                    'color': random.choice(self.star_colors),
                    'yawning': True,
                    'yawn_progress': 0
                }
            self.make_star_yawn(x, y)
            
    def update_stars(self):
        """Update all stars - twinkling and sleepiness"""
        while self.running:
            with self.lock:
                # Update moon phase for ambient effect
                self.moon_phase += 0.01
                moon_brightness = (np.sin(self.moon_phase) + 1) * 0.1
                
                stars_to_remove = []
                
                for (x, y), star in self.stars.items():
                    # Update twinkle
                    star['twinkle_phase'] += star['twinkle_speed']
                    twinkle = (np.sin(star['twinkle_phase']) + 1) * 0.5
                    
                    # Sleepier stars twinkle slower
                    if star['sleepiness'] > 0:
                        star['twinkle_speed'] = max(0.005, star['twinkle_speed'] - 0.0001)
                        
                    # Calculate brightness
                    base_brightness = star['brightness'] * (1 - star['sleepiness'] * 0.7)
                    
                    # Yawning effect
                    if star['yawning']:
                        star['yawn_progress'] += 0.05
                        if star['yawn_progress'] < 0.5:
                            # Growing phase
                            yawn_effect = 1 + star['yawn_progress']
                        else:
                            # Shrinking phase
                            yawn_effect = 2 - star['yawn_progress']
                            
                        base_brightness *= yawn_effect
                        
                        if star['yawn_progress'] >= 1.0:
                            star['yawning'] = False
                            
                    # Apply twinkle and moon
                    final_brightness = base_brightness * twinkle + moon_brightness
                    
                    # Very sleepy stars might fall asleep (disappear)
                    if star['sleepiness'] >= 1.0 and random.random() < 0.01:
                        stars_to_remove.append((x, y))
                        continue
                        
                    # Update LED
                    led = self.lp.panel.led(x, y)
                    color = tuple(int(c * final_brightness) for c in star['color'])
                    led.color = color
                    
                # Remove sleeping stars
                for pos in stars_to_remove:
                    del self.stars[pos]
                    led = self.lp.panel.led(pos[0], pos[1])
                    led.color = (0, 0, 0)
                    
            time.sleep(0.05)
            
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Sleepy Stars"""
        print("Starting Sleepy Stars!")
        print("Press stars to make them yawn and get sleepy!")
        print("Sleepy stars twinkle slower and dimmer")
        print("Very sleepy stars might fall asleep!")
        print("Press Ctrl+C to exit.")
        
        # Start star update thread
        update_thread = threading.Thread(target=self.update_stars)
        update_thread.daemon = True
        update_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nSleepy Stars stopped. Sweet dreams!")

if __name__ == "__main__":
    stars = SleepyStars()
    stars.start()
