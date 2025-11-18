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

class SnakeSymphony:
    def __init__(self, config_file='config.yaml'):
        # Initialize grid_state FIRST before any LED operations
        self.grid_state = {}
        self.running = True
        self.lock = threading.Lock()
        
        # Snake state
        self.snake = [(4, 4)]  # Start in center
        self.direction = (1, 0)  # Moving right
        self.next_direction = (1, 0)
        self.grow_count = 0
        
        # Food and music
        self.food = None
        self.food_type = None
        self.collected_notes = []  # Musical pattern we're building
        self.current_instrument = 'sine'
        self.tempo = 120  # BPM
        self.move_timer = 0
        self.move_speed = 10  # Frames per move
        
        # Static drawn flag
        self.static_drawn = False
        
        # Musical elements
        self.scales = {
            'pentatonic': [261.63, 293.66, 329.63, 392.00, 440.00, 523.25],  # C D E G A C
            'blues': [261.63, 311.13, 349.23, 369.99, 392.00, 466.16],      # C Eb F F# G Bb
            'major': [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25],  # C D E F G A B C
        }
        self.current_scale = 'pentatonic'
        
        # Food types with different instruments/effects
        self.food_types = {
            'red': {
                'color': (255, 0, 0),
                'instrument': 'sine',
                'points': 10,
                'effect': 'none'
            },
            'yellow': {
                'color': (255, 255, 0),
                'instrument': 'square',
                'points': 20,
                'effect': 'staccato'
            },
            'green': {
                'color': (0, 255, 0),
                'instrument': 'triangle',
                'points': 15,
                'effect': 'echo'
            },
            'blue': {
                'color': (0, 0, 255),
                'instrument': 'sawtooth',
                'points': 25,
                'effect': 'harmony'
            },
            'rainbow': {
                'color': (255, 255, 255),
                'instrument': 'bell',
                'points': 50,
                'effect': 'arpeggio'
            }
        }
        
        # Snake colors (gradient from head to tail)
        self.snake_colors = [
            (255, 255, 255),  # Head - white
            (200, 200, 255),  # Light blue
            (150, 150, 255),  # Medium blue
            (100, 100, 255),  # Darker blue
            (50, 50, 200),    # Deep blue
        ]
        
        # Score and patterns
        self.score = 0
        self.pattern_length = 0
        self.playing_pattern = False
        
        # NOW initialize hardware
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
        print("Snake Symphony initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                self.set_led(x, y, (0, 0, 0))
        # Reset grid state after clearing
        self.grid_state = {}
        
    def set_led(self, x, y, color):
        """Only update LED if color changed (anti-flicker)"""
        if 0 <= x < 9 and 0 <= y < 9:
            current = self.grid_state.get((x, y))
            if current != color:
                led = self.lp.panel.led(x, y)
                led.color = color
                self.grid_state[(x, y)] = color
                
    def spawn_food(self):
        """Spawn food with musical properties"""
        # Find empty spots
        occupied = set(self.snake)
        empty_spots = [(x, y) for x in range(9) for y in range(9) 
                       if (x, y) not in occupied]
        
        if empty_spots:
            self.food = random.choice(empty_spots)
            
            # Choose food type based on pattern length
            if self.pattern_length > 0 and self.pattern_length % 10 == 0:
                self.food_type = 'rainbow'  # Special every 10 foods
            else:
                weights = [40, 30, 20, 10, 0]  # Make some foods rarer
                self.food_type = random.choices(
                    list(self.food_types.keys()),
                    weights=weights
                )[0]
                
    def play_note_with_instrument(self, freq, instrument, effect='none'):
        """Play note with different instrument sounds"""
        duration = 0.3
        t = np.linspace(0, duration, int(44100 * duration), False)
        
        # Generate waveform based on instrument
        if instrument == 'sine':
            wave = np.sin(2 * np.pi * freq * t)
        elif instrument == 'square':
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif instrument == 'triangle':
            wave = 2 * np.arcsin(np.sin(2 * np.pi * freq * t)) / np.pi
        elif instrument == 'sawtooth':
            wave = 2 * ((freq * t) % 1) - 1
        elif instrument == 'bell':
            # Bell sound with multiple harmonics
            wave = np.sin(2 * np.pi * freq * t)
            wave += 0.5 * np.sin(2 * np.pi * freq * 2.4 * t)
            wave += 0.25 * np.sin(2 * np.pi * freq * 3.6 * t)
            wave = wave / 1.75
        else:
            wave = np.sin(2 * np.pi * freq * t)
            
        # Apply effects
        if effect == 'staccato':
            envelope = np.exp(-10 * t)
        elif effect == 'echo':
            envelope = np.ones_like(t)
            # Add echo
            echo_delay = int(0.1 * 44100)
            echo_wave = np.zeros_like(wave)
            echo_wave[echo_delay:] = wave[:-echo_delay] * 0.5
            wave = wave + echo_wave
        elif effect == 'harmony':
            # Add a fifth above
            wave += 0.5 * np.sin(2 * np.pi * freq * 1.5 * t)
        else:
            envelope = np.exp(-3 * t)
            
        if effect != 'echo':
            wave = wave * envelope
            
        # Normalize and play
        wave = wave * 0.5
        wave = (wave * 32767).astype(np.int16)
        threading.Thread(target=play_wave, args=(wave,)).start()
        
    def play_collected_pattern(self):
        """Play the musical pattern created by collected food"""
        if self.playing_pattern:
            return
            
        self.playing_pattern = True
        
        def play():
            for note_data in self.collected_notes:
                if not self.running:
                    break
                freq = note_data['freq']
                instrument = note_data['instrument']
                effect = note_data['effect']
                
                self.play_note_with_instrument(freq, instrument, effect)
                time.sleep(60.0 / self.tempo / 4)  # Sixteenth notes
                
            self.playing_pattern = False
            
        threading.Thread(target=play).start()
        
    def handle_button_press(self, button):
        """Change snake direction based on button position"""
        x, y = button.x, button.y
        head_x, head_y = self.snake[0]
        
        # Calculate direction from head to button
        dx = x - head_x
        dy = y - head_y
        
        # Determine primary direction
        if abs(dx) > abs(dy):
            # Horizontal movement
            new_dir = (1 if dx > 0 else -1, 0)
        else:
            # Vertical movement
            new_dir = (0, 1 if dy > 0 else -1)
            
        # Can't reverse into yourself
        if len(self.snake) > 1:
            if (new_dir[0] == -self.direction[0] and 
                new_dir[1] == -self.direction[1]):
                return
                
        self.next_direction = new_dir
        
        # Play directional sound
        if new_dir[0] != 0:
            # Horizontal - play low note
            self.play_note_with_instrument(130.81, 'sine')  # Low C
        else:
            # Vertical - play high note
            self.play_note_with_instrument(261.63, 'sine')  # Middle C
            
    def move_snake(self):
        """Move snake and handle collisions"""
        with self.lock:
            # Update direction
            self.direction = self.next_direction
            
            # Calculate new head position
            head_x, head_y = self.snake[0]
            new_head = (
                head_x + self.direction[0],
                head_y + self.direction[1]
            )
            
            # Check boundaries (wrap around for baby-friendly gameplay)
            new_head = (new_head[0] % 9, new_head[1] % 9)
            
            # Check self-collision (gentle - just stop growing)
            if new_head in self.snake[1:]:
                # Play bonk sound
                self.play_note_with_instrument(100, 'square')
                # Trim tail instead of game over
                if len(self.snake) > 3:
                    self.snake = self.snake[:3]
                return
                
            # Move snake
            self.snake.insert(0, new_head)
            
            # Check food collision
            if new_head == self.food:
                # Eat food!
                food_info = self.food_types[self.food_type]
                self.score += food_info['points']
                self.grow_count += 2  # Grow by 2 segments
                
                # Add to musical pattern
                scale = self.scales[self.current_scale]
                note_index = len(self.collected_notes) % len(scale)
                freq = scale[note_index]
                
                self.collected_notes.append({
                    'freq': freq,
                    'instrument': food_info['instrument'],
                    'effect': food_info['effect']
                })
                
                # Play the note
                self.play_note_with_instrument(
                    freq, 
                    food_info['instrument'], 
                    food_info['effect']
                )
                
                self.pattern_length += 1
                
                # Special effects for rainbow food
                if self.food_type == 'rainbow':
                    # Play entire pattern
                    self.play_collected_pattern()
                    # Speed boost
                    self.move_speed = max(3, self.move_speed - 1)
                    
                # Spawn new food
                self.spawn_food()
            else:
                # Remove tail if not growing
                if self.grow_count > 0:
                    self.grow_count -= 1
                else:
                    self.snake.pop()
                    
    def draw_snake(self):
        """Draw snake with gradient colors"""
        for i, (x, y) in enumerate(self.snake):
            # Color gradient from head to tail
            color_index = min(i, len(self.snake_colors) - 1)
            color = self.snake_colors[color_index]
            
            # Head sparkles
            if i == 0:
                # Pulsing head
                pulse = (np.sin(time.time() * 5) + 1) * 0.5
                color = tuple(int(c * (0.7 + 0.3 * pulse)) for c in color)
                
            self.set_led(x, y, color)
            
    def draw_food(self):
        """Draw food with animation"""
        if self.food:
            x, y = self.food
            food_info = self.food_types[self.food_type]
            color = food_info['color']
            
            # Animate special food
            if self.food_type == 'rainbow':
                # Cycle through rainbow colors
                rainbow = [
                    (255, 0, 0), (255, 127, 0), (255, 255, 0),
                    (0, 255, 0), (0, 0, 255), (148, 0, 211)
                ]
                color_index = int(time.time() * 5) % len(rainbow)
                color = rainbow[color_index]
            else:
                # Pulse regular food
                pulse = (np.sin(time.time() * 3) + 1) * 0.5
                color = tuple(int(c * (0.5 + 0.5 * pulse)) for c in color)
                
            self.set_led(x, y, color)
            
    def draw_pattern_indicator(self):
        """Show pattern length on top row"""
        pattern_lights = min(9, self.pattern_length // 2)
        for i in range(9):
            if i < pattern_lights:
                # Musical note indicator
                hue = (i * 40) % 360
                # Simple HSV to RGB
                c = 1.0
                x = c * (1 - abs((hue / 60) % 2 - 1))
                if hue < 60:
                    r, g, b = c, x, 0
                elif hue < 120:
                    r, g, b = x, c, 0
                elif hue < 180:
                    r, g, b = 0, c, x
                elif hue < 240:
                    r, g, b = 0, x, c
                elif hue < 300:
                    r, g, b = x, 0, c
                else:
                    r, g, b = c, 0, x
                    
                self.set_led(i, 0, (int(r*255), int(g*255), int(b*255)))
            else:
                self.set_led(i, 0, (0, 0, 0))
                
    def clear_game_area(self):
        """Only clear cells that might change"""
        # Clear everything except top row (pattern indicator)
        for y in range(1, 9):
            for x in range(9):
                current = self.grid_state.get((x, y), (0, 0, 0))
                # Only clear if not black
                if current != (0, 0, 0):
                    self.set_led(x, y, (0, 0, 0))
                    
    def update_display(self):
        """Update display with anti-flicker"""
        while self.running:
            # Only clear what needs clearing
            self.clear_game_area()
            
            # Draw game elements
            self.draw_food()
            self.draw_snake()
            self.draw_pattern_indicator()
            
            time.sleep(0.05)
            
    def game_loop(self):
        """Main game loop"""
        self.spawn_food()
        
        while self.running:
            self.move_timer += 1
            
            if self.move_timer >= self.move_speed:
                self.move_timer = 0
                self.move_snake()
                
                # Play pattern every 20 moves
                if len(self.snake) > 5 and self.pattern_length % 20 == 0:
                    self.play_collected_pattern()
                    
            time.sleep(0.05)
            
    def play_background_rhythm(self):
        """Subtle background beat"""
        while self.running:
            # Kick drum
            self.play_note_with_instrument(60, 'sine')
            time.sleep(60.0 / self.tempo)
            
    def event_loop(self):
        """Handle button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Snake Symphony"""
        print("Starting Snake Symphony!")
        print("🐍 Guide the snake to collect food")
        print("🎵 Each food adds a note to your melody")
        print("🎨 Different colored foods = different instruments")
        print("🌈 Rainbow food plays your entire song!")
        print("Press buttons to change direction")
        print("The snake wraps around edges (no walls!)")
        print("Press Ctrl+C to exit.")
        
        # Start threads
        game_thread = threading.Thread(target=self.game_loop)
        game_thread.daemon = True
        game_thread.start()
        
        display_thread = threading.Thread(target=self.update_display)
        display_thread.daemon = True
        display_thread.start()
        
        rhythm_thread = threading.Thread(target=self.play_background_rhythm)
        rhythm_thread.daemon = True
        rhythm_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print(f"\nFinal Score: {self.score}")
            print(f"Pattern Length: {self.pattern_length} notes")
            print("Your symphony was beautiful!")

if __name__ == "__main__":
    snake = SnakeSymphony()
    snake.start()