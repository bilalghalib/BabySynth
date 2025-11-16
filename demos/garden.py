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
        self.garden = {}  # {(x,y): {'type': 'flower/grass', 'age': 0, 'color': (r,g,b)}}
        self.lock = threading.Lock()
        
        # Nature sounds (musical approximations)
        self.growth_notes = [261.63, 329.63, 392.00, 523.25]  # C major arpeggio
        self.flower_colors = [
            (255, 192, 203),  # Pink
            (255, 255, 0),    # Yellow
            (255, 165, 0),    # Orange
            (238, 130, 238),  # Violet
            (135, 206, 235),  # Sky blue
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
                
    def play_growth_sound(self):
        """Play a pleasant growth sound"""
        # Play ascending arpeggio
        for i, freq in enumerate(self.growth_notes):
            t = np.linspace(0, 0.2, int(44100 * 0.2), False)
            wave = np.sin(2 * np.pi * freq * t)
            # Bell-like envelope
            envelope = np.exp(-3 * t) * (1 - i * 0.15)
            wave = wave * envelope
            wave = (wave * 32767 * 0.5).astype(np.int16)
            threading.Thread(target=play_wave, args=(wave,), daemon=True).start()
            time.sleep(0.08)
            
    def plant_seed(self, x, y):
        """Plant a seed that will grow"""
        with self.lock:
            if (x, y) not in self.garden:
                # Decide type based on position
                plant_type = 'flower' if random.random() > 0.3 else 'grass'
                color = random.choice(self.flower_colors) if plant_type == 'flower' else self.grass_color
                
                self.garden[(x, y)] = {
                    'type': plant_type,
                    'age': 0,
                    'max_age': random.uniform(3, 6),
                    'color': color,
                    'growth_rate': random.uniform(0.02, 0.05)
                }
                
        # Play growth sound
        threading.Thread(target=self.play_growth_sound).start()
        
        # Spread effect - plants encourage nearby growth
        self.spread_growth(x, y)
        
    def spread_growth(self, x, y):
        """Encourage growth in nearby cells"""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < 9 and 0 <= ny < 9:
                    if random.random() < 0.3:  # 30% chance to spread
                        threading.Timer(
                            random.uniform(0.5, 1.5),
                            lambda px=nx, py=ny: self.plant_seed(px, py)
                        ).start()
                        
    def grow_garden(self):
        """Animate plant growth"""
        while self.running:
            with self.lock:
                plants_to_remove = []
                
                for (x, y), plant in self.garden.items():
                    # Age the plant
                    plant['age'] += plant['growth_rate']
                    
                    # Calculate brightness based on age
                    if plant['age'] < 1:
                        # Growing phase
                        brightness = plant['age']
                    elif plant['age'] < plant['max_age']:
                        # Mature phase
                        brightness = 1.0
                    else:
                        # Wilting phase
                        brightness = max(0, 2 - (plant['age'] - plant['max_age']) * 2)
                        if brightness <= 0:
                            plants_to_remove.append((x, y))
                            continue
                    
                    # Update LED
                    led = self.lp.panel.led(x, y)
                    color = tuple(int(c * brightness) for c in plant['color'])
                    led.color = color
                    
                # Remove dead plants
                for pos in plants_to_remove:
                    del self.garden[pos]
                    led = self.lp.panel.led(pos[0], pos[1])
                    led.color = (0, 0, 0)
                    
            time.sleep(0.05)
            
    def create_rainbow_wave(self, start_x, start_y):
        """Create a rainbow wave effect from press point"""
        rainbow = [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)
        ]
        
        for radius in range(1, 6):
            color = rainbow[radius % len(rainbow)]
            for angle in np.linspace(0, 2 * np.pi, 20):
                x = int(start_x + radius * np.cos(angle))
                y = int(start_y + radius * np.sin(angle))
                if 0 <= x < 9 and 0 <= y < 9:
                    led = self.lp.panel.led(x, y)
                    led.color = tuple(int(c * (1 - radius * 0.15)) for c in color)
            time.sleep(0.1)
            
    def handle_button_press(self, button):
        """Handle button press - plant seeds or create effects"""
        x, y = button.x, button.y
        
        # Plant a seed
        self.plant_seed(x, y)
        
        # Create rainbow wave effect
        threading.Thread(
            target=self.create_rainbow_wave,
            args=(x, y),
            daemon=True
        ).start()
        
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
        print("Press buttons to plant flowers and grass!")
        print("Watch your garden grow and spread!")
        print("Press Ctrl+C to exit.")
        
        # Start growth animation
        grow_thread = threading.Thread(target=self.grow_garden)
        grow_thread.daemon = True
        grow_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nColor Garden stopped.")

if __name__ == "__main__":
    garden = ColorGarden()
    garden.start()
