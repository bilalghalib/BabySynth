import yaml
import colorsys
import time
import random
import threading
import numpy as np
import simpleaudio as sa
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import generate_sine_wave, play_wave

class BubblePop:
    def __init__(self, config_file='config.yaml'):
        self.load_config(config_file)
        self.init_launchpad()
        self.running = True
        self.bubbles = {}  # {(x,y): {'size': 0-1, 'growing': True, 'color': (r,g,b)}}
        self.lock = threading.Lock()
        self.max_bubbles = 8
        
        # Bubble colors (soft pastels)
        self.bubble_colors = [
            (255, 182, 193),  # Light pink
            (255, 218, 185),  # Peach
            (255, 255, 224),  # Light yellow
            (152, 251, 152),  # Pale green
            (173, 216, 230),  # Light blue
            (221, 160, 221),  # Plum
            (176, 224, 230),  # Powder blue
        ]
        
        # Pop sounds - descending notes
        self.pop_notes = [523.25, 493.88, 440.00, 392.00, 349.23, 329.63, 293.66, 261.63]
        
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
        print("Bubble Pop initialized!")
        
    def clear_grid(self):
        for x in range(8):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def play_pop_sound(self, x, y):
        """Play a pop sound based on position"""
        # Map position to note
        note_index = (x + y) % len(self.pop_notes)
        frequency = self.pop_notes[note_index]
        
        # Create a "pop" sound - short burst with quick decay
        duration = 0.15
        t = np.linspace(0, duration, int(44100 * duration), False)
        
        # Start with noise burst
        noise = np.random.normal(0, 0.1, len(t))
        
        # Add tonal component
        tone = np.sin(2 * np.pi * frequency * t)
        
        # Quick attack, quick decay
        envelope = np.exp(-20 * t)
        
        wave = (0.3 * noise + 0.7 * tone) * envelope
        wave = (wave * 32767).astype(np.int16)
        
        threading.Thread(target=play_wave, args=(wave,)).start()
        
    def create_bubble(self, x, y):
        """Create a new bubble at position"""
        with self.lock:
            if (x, y) not in self.bubbles and len(self.bubbles) < self.max_bubbles:
                self.bubbles[(x, y)] = {
                    'size': 0.1,
                    'growing': True,
                    'color': random.choice(self.bubble_colors),
                    'speed': random.uniform(0.02, 0.04)
                }
                
    def pop_bubble(self, x, y):
        """Pop a bubble with animation"""
        # Create expanding ring effect
        for radius in range(1, 4):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # Only edge
                        px, py = x + dx, y + dy
                        if 0 <= px < 8 and 0 <= py < 8:
                            led = self.lp.panel.led(px, py)
                            # Fade based on radius
                            brightness = 1.0 - (radius - 1) * 0.3
                            #led.color = tuple(int(255 * brightness) for _ in range(3))
                            led.color = tuple(round(i*255) for i in colorsys.hsv_to_rgb(1/4*radius,1,1))
            time.sleep(0.05)
            
        # Clear the effect
        time.sleep(0.1)
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                px, py = x + dx, y + dy
                if 0 <= px < 8 and 0 <= py < 8:
                    led = self.lp.panel.led(px, py)
                    led.color = (0, 0, 0)
                    
    def animate_bubbles(self):
        """Animate all bubbles - growing and shrinking"""
        while self.running:
            with self.lock:
                bubbles_to_remove = []
                
                for (x, y), bubble in self.bubbles.items():
                    # Update size
                    if bubble['growing']:
                        bubble['size'] += bubble['speed']
                        if bubble['size'] >= 1.0:
                            bubble['size'] = 1.0
                            bubble['growing'] = False
                    else:
                        bubble['size'] -= bubble['speed']
                        if bubble['size'] <= 0:
                            bubbles_to_remove.append((x, y))
                            continue
                    
                    # Update LED brightness based on size
                    led = self.lp.panel.led(x, y)
                    brightness = bubble['size']
                    color = tuple(int(c * brightness) for c in bubble['color'])
                    led.color = color
                    
                # Remove dead bubbles
                for pos in bubbles_to_remove:
                    del self.bubbles[pos]
                    led = self.lp.panel.led(pos[0], pos[1])
                    led.color = (0, 0, 0)
                    
            time.sleep(0.09)
            
    def handle_button_press(self, button):
        """Handle button press"""
        x, y = button.x, button.y
        
        with self.lock:
            if (x, y) in self.bubbles:
                self.play_pop_sound(x, y)
                # Pop the bubble!
                del self.bubbles[(x, y)]
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                threading.Thread(target=self.pop_bubble, args=(x, y)).start()
                
        # Play pop sound and animation
        
    def bubble_generator(self):
        """Generate new bubbles periodically"""
        while self.running:
            # Create 1-3 bubbles at random positions
            num_bubbles = random.randint(1, 3)
            for _ in range(num_bubbles):
                x = random.randint(0, 8)
                y = random.randint(0, 8)
                self.create_bubble(x, y)
            
            # Wait before next generation
            time.sleep(random.uniform(0.2, 1.5))
            
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Bubble Pop"""
        print("Starting Bubble Pop!")
        print("Pop the bubbles as they appear!")
        print("Press Ctrl+C to exit.")
        
        # Start animation thread
        anim_thread = threading.Thread(target=self.animate_bubbles)
        anim_thread.daemon = True
        anim_thread.start()
        
        # Start bubble generator
        gen_thread = threading.Thread(target=self.bubble_generator)
        gen_thread.daemon = True
        gen_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nBubble Pop stopped.")

if __name__ == "__main__":
    bubbles = BubblePop()
    bubbles.start()
