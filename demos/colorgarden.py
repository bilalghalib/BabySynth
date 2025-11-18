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

class ColorGarden:
    def __init__(self, config_file='config.yaml'):
        self.load_config(config_file)
        self.init_launchpad()
        self.running = True
        self.plants = {}  # {(x,y): {'age': 0, 'color': (r,g,b), 'type': 'flower/grass'}}
        self.lock = threading.Lock()
        
        # Nature sounds
        self.growth_notes = [261.63, 329.63, 392.00, 523.25]  # C major arpeggio
        self.flower_colors = [
            (255, 182, 193),  # Light pink
            (255, 255, 0),    # Yellow
            (255, 140, 0),    # Orange
            (218, 112, 214),  # Orchid
            (135, 206, 250),  # Light sky blue
        ]
        self.grass_color = (34, 139, 34)  # Forest green
        
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
        print("Color Garden initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def play_planting_sound(self):
        """Play a simple planting sound"""
        # Just play one pleasant note
        freq = random.choice(self.growth_notes)
        duration = 0.3
        t = np.linspace(0, duration, int(44100 * duration), False)
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-2 * t)
        wave = wave * envelope * 0.4
        wave = (wave * 32767).astype(np.int16)
        play_wave(wave)
        
    def handle_button_press(self, button):
        """Plant a flower or grass"""
        x, y = button.x, button.y
        
        with self.lock:
            # Plant something new or water existing plant
            if (x, y) not in self.plants:
                # New plant
                plant_type = 'flower' if random.random() > 0.3 else 'grass'
                color = random.choice(self.flower_colors) if plant_type == 'flower' else self.grass_color
                
                self.plants[(x, y)] = {
                    'age': 0,
                    'color': color,
                    'type': plant_type,
                    'max_age': 100,  # Simplified - just count frames
                }
                
                # Play sound
                threading.Thread(target=self.play_planting_sound).start()
            else:
                # Water existing plant - reset age
                self.plants[(x, y)]['age'] = 0
                
    def update_garden(self):
        """Simple update loop for all plants"""
        while self.running:
            with self.lock:
                plants_to_remove = []
                
                for (x, y), plant in self.plants.items():
                    # Age the plant
                    plant['age'] += 1
                    
                    # Calculate brightness
                    if plant['age'] < 20:
                        # Growing
                        brightness = plant['age'] / 20.0
                    elif plant['age'] < 80:
                        # Mature
                        brightness = 1.0
                    else:
                        # Wilting
                        brightness = max(0, 1.0 - (plant['age'] - 80) / 20.0)
                        if plant['age'] > plant['max_age']:
                            plants_to_remove.append((x, y))
                            continue
                    
                    # Update LED
                    led = self.lp.panel.led(x, y)
                    color = tuple(int(c * brightness) for c in plant['color'])
                    led.color = color
                    
                # Remove dead plants
                for pos in plants_to_remove:
                    del self.plants[pos]
                    led = self.lp.panel.led(pos[0], pos[1])
                    led.color = (0, 0, 0)
                    
            time.sleep(0.1)  # Update 10 times per second
            
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Color Garden"""
        print("Starting Color Garden!")
        print("Press buttons to plant flowers!")
        print("Press planted flowers to water them!")
        print("Press Ctrl+C to exit.")
        
        # Single update thread
        update_thread = threading.Thread(target=self.update_garden)
        update_thread.daemon = True
        update_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nColor Garden stopped.")

if __name__ == "__main__":
    garden = ColorGarden()
    garden.start()
