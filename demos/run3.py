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

class MusicalRunner:
    def __init__(self, config_file='config.yaml'):
        # Initialize ALL attributes BEFORE init_launchpad
        self.running = True
        self.lock = threading.Lock()
        
        # Game elements
        self.runner_pos = 2  # Fixed X position for runner
        self.runner_y = 6    # Ground level
        self.jumping = False
        self.jump_height = 0
        self.jump_progress = 0
        self.double_jump_available = True
        
        # Obstacles and terrain
        self.obstacles = []  # List of (x, type) where type is 'cactus', 'mountain', or 'bird'
        self.collectibles = []  # Stars to collect!
        self.ground_level = 6
        self.scroll_speed = 0.4  # Slower for babies
        
        # Music - simplified melody
        self.melody_notes = [
            261.63,  # C
            293.66,  # D
            329.63,  # E
            392.00,  # G
            329.63,  # E
            293.66,  # D
            261.63,  # C
        ]
        self.melody_index = 0
        
        # Sound effects for different obstacles
        self.obstacle_sounds = {
            'cactus': 220.00,    # A3 - middle sound
            'mountain': 146.83,  # D3 - low sound
            'bird': 440.00,      # A4 - high sound
        }
        
        # Visual elements
        self.runner_color = (255, 255, 0)  # Yellow
        self.ground_color = (0, 100, 0)     # Dark green (grass)
        self.cactus_color = (0, 255, 0)     # Bright green
        self.mountain_color = (139, 69, 19)  # Brown
        self.bird_color = (255, 100, 100)   # Pink
        self.star_color = (255, 215, 0)     # Gold
        self.sky_colors = [
            (50, 100, 150),   # Darker blue (top)
            (100, 150, 200),  # Medium blue
            (150, 200, 250),  # Light blue
            (255, 200, 150),  # Sunset orange
        ]
        
        # Score and feedback
        self.score = 0
        self.stars_collected = 0
        self.obstacles_jumped = 0
        self.perfect_jumps = 0
        self.combo = 0
        
        # Grid state tracking (to reduce flicker)
        self.grid_state = {}  # (x,y): color
        self.static_elements_drawn = False
        
        # NOW load config and init
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
        print("Musical Runner initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                self.set_led(x, y, (0, 0, 0))
        self.grid_state = {}
                
    def set_led(self, x, y, color):
        """Only update LED if color changed (reduces flicker)"""
        if 0 <= x < 9 and 0 <= y < 9:
            current = self.grid_state.get((x, y))
            if current != color:
                led = self.lp.panel.led(x, y)
                led.color = color
                self.grid_state[(x, y)] = color
                
    def draw_static_elements(self):
        """Draw sky and ground once (they don't move)"""
        if not self.static_elements_drawn:
            # Sky gradient
            for y in range(5):
                if y < len(self.sky_colors):
                    color = self.sky_colors[y]
                    brightness = 0.3 + (y * 0.1)
                    color = tuple(int(c * brightness) for c in color)
                    for x in range(9):
                        self.set_led(x, y, color)
                        
            # Ground
            for x in range(9):
                self.set_led(x, self.ground_level + 1, self.ground_color)
                if self.ground_level + 2 < 9:
                    darker = tuple(int(c * 0.5) for c in self.ground_color)
                    self.set_led(x, self.ground_level + 2, darker)
                    
            self.static_elements_drawn = True
            
    def clear_game_area(self):
        """Only clear the area where things move"""
        for x in range(9):
            for y in range(5, self.ground_level + 1):  # Sky to ground level
                self.set_led(x, y, self.grid_state.get((x, y if y < 5 else 4), (0, 0, 0)))
                
    def draw_runner(self):
        """Draw the runner character"""
        y = self.runner_y - int(self.jump_height)
        
        # Head
        if 0 <= y < 9:
            self.set_led(self.runner_pos, y, self.runner_color)
            
        # Body (only when not jumping high)
        if 0 <= y + 1 < 9 and self.jump_height < 2:
            body_color = tuple(int(c * 0.7) for c in self.runner_color)
            self.set_led(self.runner_pos, y + 1, body_color)
            
        # Show combo stars above runner
        if self.combo > 0 and y - 1 >= 0:
            star_brightness = min(1.0, self.combo * 0.2)
            star_color = tuple(int(255 * star_brightness) for _ in range(3))
            self.set_led(self.runner_pos, y - 1, star_color)
            
    def draw_obstacles(self):
        """Draw all obstacles"""
        with self.lock:
            for x, obstacle_type in self.obstacles:
                x_pos = int(x)
                if 0 <= x_pos < 9:
                    if obstacle_type == 'cactus':
                        # Small cactus (1 block)
                        self.set_led(x_pos, self.ground_level, self.cactus_color)
                    elif obstacle_type == 'mountain':
                        # Mountain (2 blocks tall)
                        self.set_led(x_pos, self.ground_level, self.mountain_color)
                        if self.ground_level - 1 >= 0:
                            lighter = tuple(int(c * 0.7) for c in self.mountain_color)
                            self.set_led(x_pos, self.ground_level - 1, lighter)
                    elif obstacle_type == 'bird':
                        # Flying bird (in the air)
                        bird_y = self.ground_level - 2
                        if bird_y >= 0:
                            self.set_led(x_pos, bird_y, self.bird_color)
                            # Wing effect
                            if x_pos - 1 >= 0:
                                wing_color = tuple(int(c * 0.5) for c in self.bird_color)
                                self.set_led(x_pos - 1, bird_y, wing_color)
                                
    def draw_collectibles(self):
        """Draw stars and other collectibles"""
        with self.lock:
            for x, y, item_type in self.collectibles:
                x_pos = int(x)
                if 0 <= x_pos < 9:
                    if item_type == 'star':
                        # Pulsing star effect
                        pulse = (np.sin(time.time() * 5) + 1) * 0.5
                        color = tuple(int(c * (0.5 + 0.5 * pulse)) for c in self.star_color)
                        self.set_led(x_pos, y, color)
                        
    def play_hit_sound(self, obstacle_type):
        """Play different sounds for hitting different obstacles"""
        freq = self.obstacle_sounds.get(obstacle_type, 200)
        duration = 0.2
        t = np.linspace(0, duration, int(44100 * duration), False)
        
        if obstacle_type == 'cactus':
            # Sharp prickly sound
            wave = np.sin(2 * np.pi * freq * t)
            # Add some noise for prickly effect
            noise = np.random.normal(0, 0.1, len(t))
            wave = 0.8 * wave + 0.2 * noise
            envelope = np.exp(-10 * t)
        elif obstacle_type == 'mountain':
            # Deep thud
            wave = np.sin(2 * np.pi * freq * t)
            wave += 0.5 * np.sin(2 * np.pi * freq * 0.5 * t)  # Sub harmonic
            envelope = np.exp(-20 * t)
        elif obstacle_type == 'bird':
            # High chirp
            freq_sweep = freq * (1 + np.sin(10 * np.pi * t) * 0.2)  # Vibrato
            wave = np.sin(2 * np.pi * freq_sweep * t)
            envelope = np.exp(-5 * t)
        else:
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-10 * t)
            
        wave = wave * envelope * 0.3
        wave = (wave * 32767).astype(np.int16)
        threading.Thread(target=play_wave, args=(wave,)).start()
        
    def play_jump_sound(self, perfect=False):
        """Play jump sound with melody note"""
        if perfect:
            # Play current melody note
            freq = self.melody_notes[self.melody_index]
            duration = 0.4
            t = np.linspace(0, duration, int(44100 * duration), False)
            wave = np.sin(2 * np.pi * freq * t)
            wave += 0.3 * np.sin(2 * np.pi * freq * 2 * t)  # Harmonic
            envelope = np.exp(-2 * t)
            wave = wave * envelope
            self.melody_index = (self.melody_index + 1) % len(self.melody_notes)
        else:
            # Whoosh sound for jump
            duration = 0.3
            t = np.linspace(0, duration, int(44100 * duration), False)
            # Rising pitch
            freq_sweep = 100 * (1 + 3 * t / duration)
            wave = np.sin(2 * np.pi * freq_sweep * t)
            # Add wind noise
            noise = np.random.normal(0, 0.1, len(t))
            wave = 0.5 * wave + 0.5 * noise
            envelope = 1 - t / duration  # Fade out
            wave = wave * envelope * 0.3
            
        wave = (wave * 32767).astype(np.int16)
        threading.Thread(target=play_wave, args=(wave,)).start()
        
    def play_star_sound(self):
        """Play magical sound when collecting star"""
        # Ascending arpeggio
        notes = [523.25, 659.25, 783.99, 1046.50]  # C E G C
        for i, freq in enumerate(notes):
            t = np.linspace(0, 0.1, int(44100 * 0.1), False)
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-3 * t)
            wave = wave * envelope * 0.3
            wave = (wave * 32767).astype(np.int16)
            threading.Thread(target=play_wave, args=(wave,), daemon=True).start()
            time.sleep(0.05)
            
    def jump(self):
        """Make the runner jump (with double jump!)"""
        if not self.jumping:
            self.jumping = True
            self.double_jump_available = True
            
            # Check if we're jumping over an obstacle
            perfect_jump = False
            with self.lock:
                for x, _ in self.obstacles:
                    if abs(x - self.runner_pos) < 1:
                        perfect_jump = True
                        self.perfect_jumps += 1
                        self.combo += 1
                        self.score += 20
                        break
                        
            self.play_jump_sound(perfect=perfect_jump)
            threading.Thread(target=self.jump_animation).start()
        elif self.double_jump_available and self.jump_height > 1:
            # Double jump!
            self.double_jump_available = False
            self.combo += 1
            self.play_jump_sound(perfect=True)  # Double jumps always sound good
            threading.Thread(target=self.double_jump_animation).start()
            
    def jump_animation(self):
        """Smooth jump animation"""
        jump_steps = 8
        max_height = 3
        
        for i in range(jump_steps):
            self.jump_height = (i / jump_steps) * max_height
            time.sleep(0.05)
            
        time.sleep(0.1)
        
        for i in range(jump_steps):
            self.jump_height = max_height - (i / jump_steps) * max_height
            time.sleep(0.05)
            
        self.jump_height = 0
        self.jumping = False
        
    def double_jump_animation(self):
        """Double jump goes higher!"""
        current = self.jump_height
        jump_steps = 6
        extra_height = 2
        
        for i in range(jump_steps):
            self.jump_height = current + (i / jump_steps) * extra_height
            time.sleep(0.04)
            
        time.sleep(0.1)
        
        total_height = current + extra_height
        for i in range(jump_steps * 2):
            self.jump_height = total_height - (i / (jump_steps * 2)) * total_height
            time.sleep(0.04)
            
        self.jump_height = 0
        self.jumping = False
        
    def check_collision(self):
        """Check if runner hits an obstacle"""
        if self.jumping and self.jump_height > 1:
            return False, None  # Can't hit while jumping high enough
            
        with self.lock:
            for x, obstacle_type in self.obstacles:
                if abs(x - self.runner_pos) < 0.5:
                    # Check height for birds
                    if obstacle_type == 'bird' and self.jump_height < 1:
                        return True, obstacle_type
                    elif obstacle_type != 'bird' and self.jump_height == 0:
                        return True, obstacle_type
        return False, None
        
    def check_star_collection(self):
        """Check if we collected a star"""
        with self.lock:
            collected = []
            for star in self.collectibles:
                x, y, item_type = star
                if abs(x - self.runner_pos) < 0.5 and abs(y - (self.runner_y - self.jump_height)) < 1:
                    collected.append(star)
                    self.stars_collected += 1
                    self.score += 50
                    threading.Thread(target=self.play_star_sound).start()
                    
            for star in collected:
                self.collectibles.remove(star)
                
    def handle_button_press(self, button):
        """Handle any button press to jump"""
        self.jump()
        
    def spawn_items(self):
        """Spawn obstacles and collectibles"""
        while self.running:
            with self.lock:
                # Clean up off-screen items
                self.obstacles = [(x, t) for x, t in self.obstacles if x > -2]
                self.collectibles = [(x, y, t) for x, y, t in self.collectibles if x > -2]
                
                # Spawn new items
                spawn_type = random.choices(
                    ['obstacle', 'star', 'nothing'],
                    weights=[40, 30, 30]
                )[0]
                
                if spawn_type == 'obstacle' and len(self.obstacles) < 3:
                    obstacle_type = random.choice(['cactus', 'cactus', 'mountain', 'bird'])
                    # Make sure there's space
                    can_spawn = True
                    for x, _ in self.obstacles:
                        if x > 6:
                            can_spawn = False
                            break
                    if can_spawn:
                        self.obstacles.append((8.0, obstacle_type))
                        
                elif spawn_type == 'star' and len(self.collectibles) < 2:
                    # Random height for stars
                    star_y = random.randint(3, 5)
                    self.collectibles.append((8.0, star_y, 'star'))
                    
            time.sleep(random.uniform(1.5, 2.5))
            
    def scroll_world(self):
        """Scroll everything left"""
        while self.running:
            with self.lock:
                # Move obstacles
                new_obstacles = []
                for x, obstacle_type in self.obstacles:
                    new_x = x - self.scroll_speed
                    if new_x >= -1:
                        new_obstacles.append((new_x, obstacle_type))
                    else:
                        self.obstacles_jumped += 1
                        self.score += 10
                self.obstacles = new_obstacles
                
                # Move collectibles
                new_collectibles = []
                for x, y, item_type in self.collectibles:
                    new_x = x - self.scroll_speed
                    if new_x >= -1:
                        new_collectibles.append((new_x, y, item_type))
                self.collectibles = new_collectibles
                
            # Check collisions
            hit, obstacle_type = self.check_collision()
            if hit:
                self.combo = 0  # Reset combo
                self.play_hit_sound(obstacle_type)
                threading.Thread(target=self.collision_effect, args=(obstacle_type,)).start()
                
            # Check star collection
            self.check_star_collection()
                
            time.sleep(0.1)
            
    def collision_effect(self, obstacle_type):
        """Different effects for different obstacles"""
        # Visual feedback
        original_color = self.runner_color
        
        if obstacle_type == 'cactus':
            # Green flash for cactus
            self.runner_color = (0, 255, 0)
        elif obstacle_type == 'mountain':
            # Brown flash for mountain
            self.runner_color = (139, 69, 19)
        elif obstacle_type == 'bird':
            # Pink flash for bird
            self.runner_color = (255, 100, 100)
            
        time.sleep(0.2)
        self.runner_color = original_color
        
        # Remove the obstacle (forgiving)
        with self.lock:
            self.obstacles = [(x, t) for x, t in self.obstacles 
                            if abs(x - self.runner_pos) >= 0.5]
                            
    def update_display(self):
        """Update only the changing parts of display"""
        # Draw static elements once
        self.draw_static_elements()
        
        while self.running:
            # Clear only the game area
            self.clear_game_area()
            
            # Draw game elements
            self.draw_obstacles()
            self.draw_collectibles()
            self.draw_runner()
            
            # Show score
            score_lights = min(8, self.score // 50)
            for i in range(9):
                if i < score_lights:
                    self.set_led(i, 0, (255, 215, 0))  # Gold
                else:
                    self.set_led(i, 0, self.sky_colors[0])  # Reset to sky
                    
            # Show combo with rainbow
            if self.combo > 5:
                rainbow_colors = [
                    (255, 0, 0), (255, 127, 0), (255, 255, 0),
                    (0, 255, 0), (0, 0, 255), (148, 0, 211)
                ]
                for x in range(5, 9):
                    if x - 5 < len(rainbow_colors):
                        color = rainbow_colors[(x - 5 + int(time.time() * 3)) % len(rainbow_colors)]
                        self.set_led(x, 1, color)
                        
            time.sleep(0.05)
            
    def play_background_music(self):
        """Adaptive background music that builds with combo"""
        while self.running:
            # Base rhythm
            bass_notes = [130.81, 130.81, 155.56, 130.81]  # C, C, Eb, C
            
            for i, note in enumerate(bass_notes):
                if not self.running:
                    break
                    
                duration = 0.2
                t = np.linspace(0, duration, int(44100 * duration), False)
                
                # Bass line
                wave = np.sin(2 * np.pi * note * t) * 0.1
                
                # Add harmony when combo is high
                if self.combo > 5:
                    wave += np.sin(2 * np.pi * note * 2 * t) * 0.05
                if self.combo > 10:
                    wave += np.sin(2 * np.pi * note * 3 * t) * 0.03
                    
                wave = (wave * 32767).astype(np.int16)
                play_wave(wave)
                time.sleep(0.4)
                
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Musical Runner"""
        print("Starting Musical Runner!")
        print("🏃 Press any button to jump!")
        print("⭐ Collect stars for bonus points!")
        print("🦅 Birds fly high - jump under them!")
        print("🌵 Cactuses are prickly!")
        print("⛰️  Mountains are solid!")
        print("🎵 Perfect jumps play melody notes")
        print("Press again while jumping for DOUBLE JUMP!")
        print("Press Ctrl+C to exit.")
        
        # Start all game threads
        spawn_thread = threading.Thread(target=self.spawn_items)
        spawn_thread.daemon = True
        spawn_thread.start()
        
        scroll_thread = threading.Thread(target=self.scroll_world)
        scroll_thread.daemon = True
        scroll_thread.start()
        
        display_thread = threading.Thread(target=self.update_display)
        display_thread.daemon = True
        display_thread.start()
        
        music_thread = threading.Thread(target=self.play_background_music)
        music_thread.daemon = True
        music_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print(f"\nGreat job! Final Score: {self.score}")
            print(f"⭐ Stars collected: {self.stars_collected}")
            print(f"🎯 Perfect jumps: {self.perfect_jumps}")
            print(f"🔥 Best combo: {self.combo}")

if __name__ == "__main__":
    runner = MusicalRunner()
    runner.start()
