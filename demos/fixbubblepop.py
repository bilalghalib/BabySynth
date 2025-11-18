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

class BubblePop:
    def __init__(self, config_file='config.yaml'):
        self.load_config(config_file)
        self.init_launchpad()
        self.running = True
        self.bubbles = {}  # {(x,y): bubble_data}
        self.lock = threading.Lock()
        self.max_bubbles = 10
        self.bubble_count = 0  # Track total bubbles for special ones
        self.score = 0
        self.combo = 0
        
        # Bubble colors (soft pastels)
        self.bubble_colors = [
            (255, 182, 193),  # Light pink
            (255, 218, 185),  # Peach
            (255, 255, 224),  # Light yellow
            (152, 251, 152),  # Pale green
            (173, 216, 230),  # Light blue
            (221, 160, 221),  # Plum
            (176, 224, 230),  # Powder blue
            (255, 192, 203),  # Pink
        ]
        
        # Rainbow burst colors
        self.rainbow_colors = [
            (255, 0, 0),     # Red
            (255, 127, 0),   # Orange
            (255, 255, 0),   # Yellow
            (0, 255, 0),     # Green
            (0, 127, 255),   # Blue
            (75, 0, 130),    # Indigo
            (148, 0, 211),   # Violet
        ]
        
        # Musical scale for pops (major pentatonic - always sounds happy)
        self.pop_scale = [
            261.63,  # C
            293.66,  # D
            329.63,  # E
            392.00,  # G
            440.00,  # A
            523.25,  # C (octave)
            659.25,  # E (octave)
            783.99,  # G (octave)
        ]
        
        # Special bubble properties
        self.special_bubble_types = ['golden', 'rainbow', 'mega', 'musical']
        
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
        print("Enhanced Bubble Pop initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def play_pop_sound(self, bubble_data):
        """Play a pop sound based on bubble properties"""
        if bubble_data.get('special_type') == 'musical':
            # Play a little melody for musical bubbles
            threading.Thread(target=self.play_bubble_melody).start()
            return
            
        # Regular pop with pitch based on size
        size_factor = bubble_data['size']
        base_note_idx = int(size_factor * (len(self.pop_scale) - 1))
        frequency = self.pop_scale[base_note_idx]
        
        # Special bubbles get chord
        if bubble_data.get('is_special'):
            frequencies = [frequency, frequency * 1.25, frequency * 1.5]  # Major chord
        else:
            frequencies = [frequency]
            
        duration = 0.2
        t = np.linspace(0, duration, int(44100 * duration), False)
        
        wave = np.zeros_like(t)
        for freq in frequencies:
            # Create bubble pop sound
            tone = np.sin(2 * np.pi * freq * t)
            # Add some harmonics for richness
            tone += 0.3 * np.sin(4 * np.pi * freq * t)
            tone += 0.1 * np.sin(6 * np.pi * freq * t)
            wave += tone
            
        wave = wave / len(frequencies)
        
        # Bubble pop envelope (quick attack, quick decay)
        envelope = np.exp(-15 * t) * (1 + 0.5 * np.sin(20 * np.pi * t))
        wave = wave * envelope
        
        wave = (wave * 32767 * 0.5).astype(np.int16)
        threading.Thread(target=play_wave, args=(wave,)).start()
        
    def play_bubble_melody(self):
        """Play a short melody for musical bubbles"""
        melody = [261.63, 329.63, 392.00, 523.25]  # C E G C
        for freq in melody:
            t = np.linspace(0, 0.15, int(44100 * 0.15), False)
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-5 * t)
            wave = wave * envelope * 0.3
            wave = (wave * 32767).astype(np.int16)
            play_wave(wave)
            time.sleep(0.1)
            
    def create_bubble(self, x, y):
        """Create a new bubble at position"""
        with self.lock:
            if (x, y) not in self.bubbles and len(self.bubbles) < self.max_bubbles:
                self.bubble_count += 1
                
                # Every 10th bubble is special!
                is_special = (self.bubble_count % 10 == 0)
                
                # Bubble properties
                bubble_data = {
                    'size': 0.1,
                    'growing': True,
                    'color': random.choice(self.bubble_colors),
                    'speed': random.uniform(0.01, 0.03) if not is_special else 0.005,  # Special ones are slower
                    'lifetime': random.uniform(3, 6) if not is_special else 10,  # Special ones last longer
                    'age': 0,
                    'float_phase': random.uniform(0, 2 * np.pi),
                    'float_speed': random.uniform(0.02, 0.05),
                    'float_amount': random.uniform(0.3, 0.7),
                    'is_special': is_special,
                    'birth_time': time.time(),
                }
                
                if is_special:
                    special_type = random.choice(self.special_bubble_types)
                    bubble_data['special_type'] = special_type
                    
                    if special_type == 'golden':
                        bubble_data['color'] = (255, 215, 0)  # Gold
                    elif special_type == 'rainbow':
                        bubble_data['rainbow_phase'] = 0
                    elif special_type == 'mega':
                        bubble_data['max_size'] = 1.5  # Grows bigger
                    elif special_type == 'musical':
                        bubble_data['color'] = (255, 0, 255)  # Magenta
                        
                self.bubbles[(x, y)] = bubble_data
                
    def pop_bubble_rainbow(self, x, y, bubble_data):
        """Create rainbow burst effect"""
        # Create expanding rainbow rings
        for radius in range(1, 5):
            ring_positions = []
            
            # Calculate ring positions
            for angle in np.linspace(0, 2 * np.pi, radius * 8):
                rx = int(x + radius * np.cos(angle))
                ry = int(y + radius * np.sin(angle))
                if 0 <= rx < 9 and 0 <= ry < 9:
                    ring_positions.append((rx, ry))
                    
            # Light up ring with rainbow colors
            for i, (rx, ry) in enumerate(ring_positions):
                led = self.lp.panel.led(rx, ry)
                color_idx = (i + radius) % len(self.rainbow_colors)
                color = self.rainbow_colors[color_idx]
                # Fade based on radius
                brightness = 1.0 - (radius - 1) * 0.2
                led.color = tuple(int(c * brightness) for c in color)
                
            time.sleep(0.08)
            
        # Sparkle effect for special bubbles
        if bubble_data.get('is_special'):
            sparkle_positions = [(x + dx, y + dy) 
                               for dx in range(-2, 3) 
                               for dy in range(-2, 3)
                               if 0 <= x + dx < 9 and 0 <= y + dy < 9]
            
            for _ in range(3):
                # Random sparkles
                for _ in range(5):
                    if sparkle_positions:
                        sx, sy = random.choice(sparkle_positions)
                        led = self.lp.panel.led(sx, sy)
                        led.color = (255, 255, 255)
                time.sleep(0.05)
                
                # Clear sparkles
                for sx, sy in sparkle_positions:
                    led = self.lp.panel.led(sx, sy)
                    led.color = (0, 0, 0)
                time.sleep(0.05)
        else:
            # Clear the burst
            time.sleep(0.2)
            
        # Clear everything
        for radius in range(1, 5):
            for angle in np.linspace(0, 2 * np.pi, radius * 8):
                rx = int(x + radius * np.cos(angle))
                ry = int(y + radius * np.sin(angle))
                if 0 <= rx < 9 and 0 <= ry < 9:
                    led = self.lp.panel.led(rx, ry)
                    #led.color = (0, 0, 0)
                    
    def update_floating_position(self, x, y, bubble):
        """Calculate floating bubble display position"""
        # Original position floats in a gentle pattern
        float_offset = np.sin(bubble['float_phase']) * bubble['float_amount']
        
        # Update phase for next frame
        bubble['float_phase'] += bubble['float_speed']
        
        # Return display coordinates (may be fractional, will be rounded)
        display_y = y + float_offset
        
        # Slight horizontal sway too
        display_x = x + np.sin(bubble['float_phase'] * 0.5) * 0.3
        
        return display_x, display_y
        
    def animate_bubbles(self):
        """Animate all bubbles - growing, shrinking, and floating"""
        while self.running:
            with self.lock:
                bubbles_to_remove = []
                
                # Clear grid first for floating movement
                self.clear_grid()
                
                for (x, y), bubble in self.bubbles.items():
                    # Update age
                    bubble['age'] = time.time() - bubble['birth_time']
                    
                    # Update size
                    if bubble['growing']:
                        max_size = bubble.get('max_size', 1.0)
                        bubble['size'] += bubble['speed']
                        if bubble['size'] >= max_size:
                            bubble['size'] = max_size
                            bubble['growing'] = False
                    else:
                        # Start shrinking after lifetime
                        if bubble['age'] > bubble['lifetime']:
                            bubble['size'] -= bubble['speed'] * 2  # Shrink faster
                            if bubble['size'] <= 0:
                                bubbles_to_remove.append((x, y))
                                continue
                    
                    # Get floating position
                    float_x, float_y = self.update_floating_position(x, y, bubble)
                    
                    # Round to nearest LED position
                    led_x = max(0, min(8, round(float_x)))
                    led_y = max(0, min(8, round(float_y)))
                    
                    # Update LED with color
                    led = self.lp.panel.led(led_x, led_y)
                    
                    # Special bubble colors
                    if bubble.get('special_type') == 'rainbow':
                        # Cycle through rainbow colors
                        bubble['rainbow_phase'] = (bubble.get('rainbow_phase', 0) + 0.1) % len(self.rainbow_colors)
                        color = self.rainbow_colors[int(bubble['rainbow_phase'])]
                    else:
                        color = bubble['color']
                    
                    # Apply size-based brightness
                    brightness = min(1.0, bubble['size'])
                    
                    # Special bubbles pulse
                    if bubble.get('is_special'):
                        pulse = (np.sin(time.time() * 5) + 1) * 0.5
                        brightness = brightness * (0.5 + 0.5 * pulse)
                    
                    led.color = tuple(int(c * brightness) for c in color)
                    
                    # Add glow effect for large bubbles
                    if bubble['size'] > 0.7:
                        # Dim glow on adjacent cells
                        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            glow_x = led_x + dx
                            glow_y = led_y + dy
                            if 0 <= glow_x < 9 and 0 <= glow_y < 9:
                                glow_led = self.lp.panel.led(glow_x, glow_y)
                                # Check if color exists before comparing
                                current_color = glow_led.color if glow_led.color else (0, 0, 0)
                                glow_brightness = brightness * 0.3
                                glow_color = tuple(int(c * glow_brightness) for c in color)
                                # Only set if not already brighter
                                if sum(current_color) < sum(glow_color):
                                    glow_led.color = glow_color
                    
                # Remove dead bubbles
                for pos in bubbles_to_remove:
                    del self.bubbles[pos]
                    
            time.sleep(0.03)
            
    def handle_button_press(self, button):
        """Handle button press"""
        x, y = button.x, button.y
        bubble_popped = False
        bubble_data = None
        
        with self.lock:
            # Check if we hit any bubble (including floating positions)
            for (bx, by), bubble in self.bubbles.items():
                float_x, float_y = self.update_floating_position(bx, by, bubble)
                led_x = round(float_x)
                led_y = round(float_y)
                
                if led_x == x and led_y == y:
                    # Pop the bubble!
                    bubble_data = bubble.copy()
                    del self.bubbles[(bx, by)]
                    bubble_popped = True
                    
                    # Score and combo
                    if bubble.get('is_special'):
                        self.score += 50
                        self.combo += 3
                    else:
                        self.score += 10
                        self.combo += 1
                    break
        
        # Only play sound and animation if we actually popped a bubble
        if bubble_popped and bubble_data:
            self.play_pop_sound(bubble_data)
            threading.Thread(
                target=self.pop_bubble_rainbow, 
                args=(x, y, bubble_data)
            ).start()
            
            # Chain reaction for mega bubbles
            if bubble_data.get('special_type') == 'mega':
                self.create_chain_reaction(x, y)
                
    def create_chain_reaction(self, x, y):
        """Create chain reaction for mega bubbles"""
        time.sleep(0.2)  # Small delay
        
        # Pop all nearby bubbles
        with self.lock:
            positions_to_pop = []
            for (bx, by), bubble in self.bubbles.items():
                if abs(bx - x) <= 2 and abs(by - y) <= 2:
                    positions_to_pop.append((bx, by))
                    
            for pos in positions_to_pop:
                if pos in self.bubbles:
                    bubble_data = self.bubbles[pos]
                    del self.bubbles[pos]
                    self.play_pop_sound(bubble_data)
                    
        # Visual chain reaction
        for radius in range(1, 4):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:
                        px, py = x + dx, y + dy
                        if 0 <= px < 9 and 0 <= py < 9:
                            led = self.lp.panel.led(px, py)
                            led.color = (255, 255, 255)
            time.sleep(0.1)
            
    def show_combo_indicator(self):
        """Show combo on top row"""
        if self.combo > 5:
            # Rainbow wave for high combo
            for x in range(min(self.combo, 9)):
                led = self.lp.panel.led(x, 0)
                color_idx = (x + int(time.time() * 5)) % len(self.rainbow_colors)
                led.color = self.rainbow_colors[color_idx]
                
    def bubble_generator(self):
        """Generate new bubbles periodically"""
        while self.running:
            # Generate 1-3 bubbles
            num_bubbles = random.randint(1, 2 if len(self.bubbles) < 5 else 1)
            
            for _ in range(num_bubbles):
                # Try to find empty spot
                attempts = 0
                while attempts < 10:
                    x = random.randint(1, 7)  # Avoid edges for better floating
                    y = random.randint(1, 7)
                    
                    # Check if spot is clear
                    spot_clear = True
                    with self.lock:
                        for (bx, by) in self.bubbles:
                            if abs(bx - x) < 2 and abs(by - y) < 2:
                                spot_clear = False
                                break
                                
                    if spot_clear:
                        self.create_bubble(x, y)
                        break
                        
                    attempts += 1
            
            # Wait before next generation
            # Faster generation if few bubbles
            wait_time = random.uniform(0.5, 1.5) if len(self.bubbles) < 3 else random.uniform(1.0, 2.5)
            time.sleep(wait_time)
            
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            # Update combo display
            self.show_combo_indicator()
            
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
            # Decay combo over time
            if self.combo > 0 and random.random() < 0.01:
                self.combo = max(0, self.combo - 1)
                
    def start(self):
        """Start Bubble Pop"""
        print("Starting Enhanced Bubble Pop!")
        print("🫧 Pop the floating bubbles!")
        print("🌈 All bubbles burst in rainbow colors")
        print("⭐ Every 10th bubble is SPECIAL:")
        print("   - 💛 Golden: Extra points")
        print("   - 🌈 Rainbow: Color changing")
        print("   - 💥 Mega: Chain reaction")
        print("   - 🎵 Musical: Plays melody")
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
            print(f"\nBubble Pop stopped. Final score: {self.score}!")

if __name__ == "__main__":
    bubbles = BubblePop()
    bubbles.start()
