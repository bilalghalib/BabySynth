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
        
        # Obstacles and terrain
        self.obstacles = []  # List of (x, type) where type is 'cactus' or 'mountain'
        self.ground_level = 6  # MUST BE SET BEFORE init_launchpad!
        self.scroll_speed = 0.5  # Slower for babies
        
        # Music - simplified melody
        self.melody_notes = [
            261.63,  # C
            293.66,  # D
            329.63,  # E
            261.63,  # C
        ]
        self.melody_index = 0
        
        # Visual elements
        self.runner_color = (255, 255, 0)  # Yellow
        self.ground_color = (0, 100, 0)     # Dark green (grass)
        self.cactus_color = (0, 255, 0)     # Bright green
        self.mountain_color = (139, 69, 19)  # Brown
        self.sky_colors = [
            (135, 206, 250),  # Light sky blue
            (255, 182, 193),  # Light pink (sunset)
        ]
        
        # Score and feedback
        self.score = 0
        self.obstacles_jumped = 0
        self.perfect_jumps = 0
        
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
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def draw_sky(self):
        """Draw pretty sky background"""
        for y in range(4):
            color = self.sky_colors[0] if y < 2 else self.sky_colors[1]
            brightness = 0.2 + (y * 0.1)
            for x in range(9):
                led = self.lp.panel.led(x, y)
                led.color = tuple(int(c * brightness) for c in color)
                
    def draw_ground(self):
        """Draw the ground with grass"""
        # Main ground
        for x in range(9):
            led = self.lp.panel.led(x, self.ground_level + 1)
            led.color = self.ground_color
            
        # Darker ground below
        for x in range(9):
            if self.ground_level + 2 < 9:
                led = self.lp.panel.led(x, self.ground_level + 2)
                led.color = tuple(int(c * 0.5) for c in self.ground_color)
                
    def draw_runner(self):
        """Draw the runner character (2 pixels tall)"""
        y = self.runner_y - int(self.jump_height)
        
        # Head
        if 0 <= y < 9:
            led = self.lp.panel.led(self.runner_pos, y)
            led.color = self.runner_color
            
        # Body (only when not jumping high)
        if 0 <= y + 1 < 9 and self.jump_height < 2:
            led = self.lp.panel.led(self.runner_pos, y + 1)
            led.color = tuple(int(c * 0.7) for c in self.runner_color)
            
        # Show star above runner for perfect jumps
        if self.perfect_jumps > 0 and y - 1 >= 0:
            star_brightness = min(1.0, self.perfect_jumps * 0.2)
            led = self.lp.panel.led(self.runner_pos, y - 1)
            led.color = tuple(int(255 * star_brightness) for _ in range(3))
            
    def draw_obstacles(self):
        """Draw all obstacles"""
        with self.lock:
            for x, obstacle_type in self.obstacles:
                x_pos = int(x)
                if 0 <= x_pos < 9:
                    if obstacle_type == 'cactus':
                        # Small cactus (1 block)
                        led = self.lp.panel.led(x_pos, self.ground_level)
                        led.color = self.cactus_color
                    elif obstacle_type == 'mountain':
                        # Mountain (2 blocks tall)
                        led = self.lp.panel.led(x_pos, self.ground_level)
                        led.color = self.mountain_color
                        if self.ground_level - 1 >= 0:
                            led = self.lp.panel.led(x_pos, self.ground_level - 1)
                            led.color = tuple(int(c * 0.7) for c in self.mountain_color)
                            
    def play_jump_sound(self, perfect=False):
        """Play jump sound with melody note"""
        freq = self.melody_notes[self.melody_index]
        
        if perfect:
            # Play current melody note clearly
            duration = 0.4
            t = np.linspace(0, duration, int(44100 * duration), False)
            wave = np.sin(2 * np.pi * freq * t)
            wave += 0.3 * np.sin(2 * np.pi * freq * 2 * t)  # Harmonic
            envelope = np.exp(-2 * t)
            wave = wave * envelope
            self.melody_index = (self.melody_index + 1) % len(self.melody_notes)
        else:
            # Just a simple jump sound
            duration = 0.2
            t = np.linspace(0, duration, int(44100 * duration), False)
            # Rising pitch for jump
            freq_sweep = freq * (1 + 0.5 * t / duration)
            wave = np.sin(2 * np.pi * freq_sweep * t)
            envelope = np.exp(-5 * t)
            wave = wave * envelope * 0.5
            
        wave = (wave * 32767 * 0.5).astype(np.int16)
        threading.Thread(target=play_wave, args=(wave,)).start()
        
    def jump(self):
        """Make the runner jump"""
        if not self.jumping:
            self.jumping = True
            
            # Check if we're jumping over an obstacle
            perfect_jump = False
            with self.lock:
                for x, _ in self.obstacles:
                    if abs(x - self.runner_pos) < 1:
                        perfect_jump = True
                        self.perfect_jumps += 1
                        self.score += 20
                        break
                        
            self.play_jump_sound(perfect=perfect_jump)
            threading.Thread(target=self.jump_animation).start()
            
    def jump_animation(self):
        """Smooth jump animation"""
        # Jump up
        jump_steps = 8
        max_height = 3
        
        for i in range(jump_steps):
            self.jump_height = (i / jump_steps) * max_height
            time.sleep(0.05)
            
        # Hover at peak
        time.sleep(0.1)
        
        # Fall down
        for i in range(jump_steps):
            self.jump_height = max_height - (i / jump_steps) * max_height
            time.sleep(0.05)
            
        self.jump_height = 0
        self.jumping = False
        
    def check_collision(self):
        """Check if runner hits an obstacle"""
        if self.jumping:
            return False  # Can't hit while jumping
            
        with self.lock:
            for x, obstacle_type in self.obstacles:
                if abs(x - self.runner_pos) < 0.5:
                    return True
        return False
        
    def handle_button_press(self, button):
        """Handle any button press to jump"""
        self.jump()
        
    def spawn_obstacles(self):
        """Spawn new obstacles"""
        while self.running:
            with self.lock:
                # Clean up off-screen obstacles
                self.obstacles = [(x, t) for x, t in self.obstacles if x > -2]
                
                # Spawn new obstacle
                if len(self.obstacles) < 3:  # Limit obstacles
                    obstacle_type = random.choice(['cactus', 'cactus', 'mountain'])
                    # Make sure there's space between obstacles
                    can_spawn = True
                    for x, _ in self.obstacles:
                        if x > 6:  # Too close to right edge
                            can_spawn = False
                            break
                            
                    if can_spawn:
                        self.obstacles.append((8.0, obstacle_type))
                        
            # Wait between spawns (easier spacing)
            time.sleep(random.uniform(2.0, 3.5))
            
    def scroll_world(self):
        """Scroll everything left"""
        while self.running:
            with self.lock:
                # Move obstacles left
                new_obstacles = []
                for x, obstacle_type in self.obstacles:
                    new_x = x - self.scroll_speed
                    if new_x >= -1:  # Keep if still visible
                        new_obstacles.append((new_x, obstacle_type))
                    else:
                        # Successfully passed an obstacle!
                        self.obstacles_jumped += 1
                        self.score += 10
                self.obstacles = new_obstacles
                
            # Check collisions
            if self.check_collision():
                # Very gentle collision - just a visual bump
                threading.Thread(target=self.collision_effect).start()
                
            time.sleep(0.1)
            
    def collision_effect(self):
        """Gentle collision effect - just stumble, don't punish"""
        # Small visual feedback
        original_color = self.runner_color
        self.runner_color = (255, 100, 100)  # Reddish
        time.sleep(0.2)
        self.runner_color = original_color
        
        # Remove the obstacle we hit (forgiving)
        with self.lock:
            self.obstacles = [(x, t) for x, t in self.obstacles 
                            if abs(x - self.runner_pos) >= 0.5]
                            
    def update_display(self):
        """Update the entire display"""
        while self.running:
            # Clear grid
            self.clear_grid()
            
            # Draw layers
            self.draw_sky()
            self.draw_ground()
            self.draw_obstacles()
            self.draw_runner()
            
            # Show score in top-left
            score_display = min(8, self.score // 10)  # One light per 10 points
            for i in range(score_display):
                led = self.lp.panel.led(i, 0)
                led.color = (255, 215, 0)  # Gold
                
            # Show perfect jump streak
            if self.perfect_jumps > 3:
                # Rainbow effect on top row
                for x in range(5, 9):
                    rainbow_colors = [
                        (255, 0, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255)
                    ]
                    color = rainbow_colors[(x + int(time.time() * 5)) % len(rainbow_colors)]
                    led = self.lp.panel.led(x, 0)
                    led.color = color
                    
            time.sleep(0.05)
            
    def play_background_music(self):
        """Play gentle background rhythm"""
        while self.running:
            # Simple bass line
            bass_notes = [130.81, 130.81, 155.56, 130.81]  # C, C, Eb, C
            for note in bass_notes:
                if not self.running:
                    break
                duration = 0.2
                t = np.linspace(0, duration, int(44100 * duration), False)
                wave = np.sin(2 * np.pi * note * t)
                envelope = np.ones_like(t) * 0.1  # Very quiet
                wave = wave * envelope
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
        print("🎵 Jump over obstacles to play a melody")
        print("⭐ Perfect timing = bonus points!")
        print("Very forgiving - just have fun!")
        print("Press Ctrl+C to exit.")
        
        # Start all game threads
        spawn_thread = threading.Thread(target=self.spawn_obstacles)
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
            print(f"\nGreat job! Score: {self.score}")
            print(f"Obstacles passed: {self.obstacles_jumped}")
            print(f"Perfect jumps: {self.perfect_jumps}")

if __name__ == "__main__":
    runner = MusicalRunner()
    runner.start()
