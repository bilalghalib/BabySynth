import yaml
import time
import random
import threading
import numpy as np
import simpleaudio as sa
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import generate_sine_wave, play_wave

class RainbowRain:
    def __init__(self, config_file='config.yaml'):
        self.load_config(config_file)
        self.init_launchpad()
        self.running = True
        self.raindrops = []  # List of (x, y, color, speed) tuples
        self.max_drops = 6  # Not too many for baby
        self.lock = threading.Lock()
        
        # Xylophone frequencies (pentatonic scale - always sounds nice)
        self.xylophone_notes = [
            261.63,  # C
            293.66,  # D
            329.63,  # E
            392.00,  # G
            440.00,  # A
            523.25,  # C (octave higher)
        ]
        
        # Rainbow colors
        self.rainbow_colors = [
            (255, 0, 0),     # Red
            (255, 127, 0),   # Orange
            (255, 255, 0),   # Yellow
            (0, 255, 0),     # Green
            (0, 127, 255),   # Blue
            (75, 0, 130),    # Indigo
            (148, 0, 211),   # Violet
        ]
        
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
        print("Rainbow Rain initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def play_xylophone_note(self, x):
        """Play a xylophone note based on x position"""
        # Map x position (0-8) to note index
        note_index = int((x / 8) * (len(self.xylophone_notes) - 1))
        frequency = self.xylophone_notes[note_index]
        
        # Create a bell-like sound with quick decay
        duration = 0.5
        t = np.linspace(0, duration, int(44100 * duration), False)
        
        # Add harmonics for xylophone timbre
        wave = 0.5 * np.sin(2 * np.pi * frequency * t)  # Fundamental
        wave += 0.3 * np.sin(4 * np.pi * frequency * t)  # 2nd harmonic
        wave += 0.2 * np.sin(6 * np.pi * frequency * t)  # 3rd harmonic
        
        # Apply exponential decay envelope
        envelope = np.exp(-3 * t)
        wave = wave * envelope
        
        wave = (wave * 32767).astype(np.int16)
        threading.Thread(target=play_wave, args=(wave,)).start()
        
    def create_splash(self, x, y):
        """Create a colorful splash effect"""
        splash_pattern = [
            [(0, 0)],  # Center
            [(0, -1), (1, 0), (0, 1), (-1, 0)],  # Cross
            [(1, 1), (-1, 1), (1, -1), (-1, -1)],  # Diagonals
        ]
        
        for i, ring in enumerate(splash_pattern):
            color = random.choice(self.rainbow_colors)
            # Fade color for outer rings
            faded_color = tuple(int(c * (1 - i * 0.3)) for c in color)
            
            for dx, dy in ring:
                splash_x = x + dx
                splash_y = y + dy
                if 0 <= splash_x < 9 and 0 <= splash_y < 9:
                    led = self.lp.panel.led(splash_x, splash_y)
                    led.color = faded_color
            
            time.sleep(0.1)
            
        # Clear splash after a moment
        time.sleep(0.3)
        for i, ring in enumerate(splash_pattern):
            for dx, dy in ring:
                splash_x = x + dx
                splash_y = y + dy
                if 0 <= splash_x < 9 and 0 <= splash_y < 9:
                    led = self.lp.panel.led(splash_x, splash_y)
                    led.color = (0, 0, 0)
                    
    def create_raindrop(self):
        """Create a new raindrop at the top"""
        x = random.randint(0, 8)
        y = 0
        color = random.choice(self.rainbow_colors)
        speed = random.uniform(0.3, 0.8)  # Varying speeds
        
        with self.lock:
            # Don't create too many drops
            if len(self.raindrops) < self.max_drops:
                self.raindrops.append({
                    'x': x,
                    'y': y,
                    'color': color,
                    'speed': speed,
                    'last_move': time.time()
                })
                
    def move_raindrops(self):
        """Move all raindrops down"""
        current_time = time.time()
        
        with self.lock:
            raindrops_to_remove = []
            
            for drop in self.raindrops:
                # Check if it's time to move this drop
                if current_time - drop['last_move'] >= drop['speed']:
                    # Clear current position
                    led = self.lp.panel.led(drop['x'], drop['y'])
                    led.color = (0, 0, 0)
                    
                    # Move down
                    drop['y'] += 1
                    drop['last_move'] = current_time
                    
                    # Check if drop reached bottom
                    if drop['y'] >= 9:
                        raindrops_to_remove.append(drop)
                        # Small splash at bottom
                        if drop['y'] == 9:
                            threading.Thread(
                                target=self.create_splash, 
                                args=(drop['x'], 8)
                            ).start()
                    else:
                        # Draw at new position
                        led = self.lp.panel.led(drop['x'], drop['y'])
                        led.color = drop['color']
            
            # Remove drops that reached bottom
            for drop in raindrops_to_remove:
                self.raindrops.remove(drop)
                
    def handle_button_press(self, button):
        """Handle button press - create splash and play sound"""
        x, y = button.x, button.y
        
        with self.lock:
            # Check if we hit a raindrop
            hit_drop = None
            for drop in self.raindrops:
                if drop['x'] == x and drop['y'] == y:
                    hit_drop = drop
                    break
                    
            if hit_drop:
                # Remove the raindrop
                self.raindrops.remove(hit_drop)
                # Clear its LED
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
        
        # Always create splash and play sound (fun for baby even if no hit)
        threading.Thread(target=self.create_splash, args=(x, y)).start()
        threading.Thread(target=self.play_xylophone_note, args=(x,)).start()
        
    def rain_generator(self):
        """Generate new raindrops periodically"""
        while self.running:
            self.create_raindrop()
            # Random interval between drops
            time.sleep(random.uniform(0.5, 1.5))
            
    def animation_loop(self):
        """Main animation loop"""
        while self.running:
            self.move_raindrops()
            time.sleep(0.05)  # Update rate
            
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Rainbow Rain"""
        print("Starting Rainbow Rain!")
        print("Press buttons to create splashes and play xylophone notes!")
        print("Press Ctrl+C to exit.")
        
        # Start all threads
        rain_thread = threading.Thread(target=self.rain_generator)
        rain_thread.daemon = True
        rain_thread.start()
        
        animation_thread = threading.Thread(target=self.animation_loop)
        animation_thread.daemon = True
        animation_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nRainbow Rain stopped.")

if __name__ == "__main__":
    rain = RainbowRain()
    rain.start()
