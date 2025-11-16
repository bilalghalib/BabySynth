# Enhanced color_garden.py
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
        self.plants = {}  # {(x,y): plant_data}
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
                
    def play_growth_sound(self, size):
        """Play different sounds based on plant size"""
        # Higher notes for bigger plants
        note_index = min(size - 1, len(self.growth_notes) - 1)
        freq = self.growth_notes[note_index]
        
        duration = 0.3
        t = np.linspace(0, duration, int(44100 * duration), False)
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-2 * t)
        wave = wave * envelope * 0.4
        wave = (wave * 32767).astype(np.int16)
        play_wave(wave)
        
    def get_plant_cells(self, x, y, size):
        """Get all cells occupied by a plant based on its size"""
        cells = [(x, y)]  # Center is always included
        
        if size >= 2:
            # Add adjacent cells for size 2
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 9 and 0 <= ny < 9:
                    cells.append((nx, ny))
                    
        if size >= 3:
            # Add diagonal cells for size 3
            for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 9 and 0 <= ny < 9:
                    cells.append((nx, ny))
                    
        return cells
        
    def handle_button_press(self, button):
        """Plant new or water existing plants"""
        x, y = button.x, button.y
        
        with self.lock:
            # Check if we're clicking on an existing plant
            plant_found = None
            for (px, py), plant in self.plants.items():
                if (x, y) in self.get_plant_cells(px, py, plant['size']):
                    plant_found = (px, py)
                    break
                    
            if plant_found:
                # Water the plant - make it grow!
                plant = self.plants[plant_found]
                if plant['size'] < 3 and plant['water_count'] < 3:
                    plant['water_count'] += 1
                    if plant['water_count'] >= 2:
                        # Grow bigger!
                        plant['size'] = min(3, plant['size'] + 1)
                        plant['water_count'] = 0
                        plant['age'] = 0  # Reset age when growing
                        self.play_growth_sound(plant['size'])
                        
                        # Chance to create seeds nearby
                        if random.random() < 0.3:
                            self.create_seed_nearby(plant_found[0], plant_found[1])
                else:
                    # Just refresh it
                    plant['age'] = max(0, plant['age'] - 30)
                    self.play_growth_sound(1)
            else:
                # Plant new seed
                # Check if spot is clear
                can_plant = True
                for (px, py), plant in self.plants.items():
                    if (x, y) in self.get_plant_cells(px, py, plant['size']):
                        can_plant = False
                        break
                        
                if can_plant:
                    plant_type = 'flower' if random.random() > 0.3 else 'grass'
                    color = random.choice(self.flower_colors) if plant_type == 'flower' else self.grass_color
                    
                    self.plants[(x, y)] = {
                        'age': 0,
                        'color': color,
                        'type': plant_type,
                        'size': 1,  # Start small
                        'water_count': 0,
                        'max_age': 150,
                    }
                    
                    self.play_growth_sound(1)
                    
    def create_seed_nearby(self, x, y):
        """Create a small seed near a mature plant"""
        # Try to find empty spot nearby
        positions = [(x+dx, y+dy) for dx in [-2, -1, 0, 1, 2] 
                     for dy in [-2, -1, 0, 1, 2] 
                     if abs(dx) + abs(dy) > 1]
        random.shuffle(positions)
        
        for nx, ny in positions:
            if 0 <= nx < 9 and 0 <= ny < 9:
                # Check if spot is clear
                can_plant = True
                for (px, py), plant in self.plants.items():
                    if (nx, ny) in self.get_plant_cells(px, py, plant['size']):
                        can_plant = False
                        break
                        
                if can_plant:
                    # Plant a baby version
                    parent = self.plants[(x, y)]
                    self.plants[(nx, ny)] = {
                        'age': 0,
                        'color': parent['color'],
                        'type': parent['type'],
                        'size': 1,
                        'water_count': 0,
                        'max_age': 150,
                    }
                    break
                    
    def update_garden(self):
        """Update all plants"""
        while self.running:
            with self.lock:
                plants_to_remove = []
                cells_to_update = {}  # Track which cells to light up
                
                for (x, y), plant in self.plants.items():
                    # Age the plant
                    plant['age'] += 1
                    
                    # Calculate brightness based on age and size
                    if plant['age'] < 20:
                        # Growing
                        brightness = plant['age'] / 20.0
                    elif plant['age'] < plant['max_age'] - 30:
                        # Mature
                        brightness = 1.0
                    else:
                        # Wilting
                        brightness = max(0, 1.0 - (plant['age'] - (plant['max_age'] - 30)) / 30.0)
                        if plant['age'] > plant['max_age']:
                            plants_to_remove.append((x, y))
                            continue
                    
                    # Get all cells for this plant
                    for cell in self.get_plant_cells(x, y, plant['size']):
                        if cell not in cells_to_update or brightness > cells_to_update[cell][1]:
                            cells_to_update[cell] = (plant['color'], brightness)
                    
                # Remove dead plants
                for pos in plants_to_remove:
                    plant = self.plants[pos]
                    # Clear all cells
                    for cell in self.get_plant_cells(pos[0], pos[1], plant['size']):
                        if cell in cells_to_update:
                            del cells_to_update[cell]
                    del self.plants[pos]
                
                # Clear grid first
                self.clear_grid()
                
                # Update all LEDs
                for (cx, cy), (color, brightness) in cells_to_update.items():
                    led = self.lp.panel.led(cx, cy)
                    led.color = tuple(int(c * brightness) for c in color)
                    
            time.sleep(0.1)
            
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Color Garden"""
        print("Starting Enhanced Color Garden!")
        print("🌱 Press to plant seeds (size 1)")
        print("💧 Press plants to water them - water 2x to grow!")
        print("🌸 Plants can grow to size 3 and create baby plants")
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
