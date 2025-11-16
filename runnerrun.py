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
        
        # Obstacles and terrain
        self.obstacles = []  # List of (x, type) where type is 'cactus' or 'mountain'
        self.ground_level = 6  # MUST BE SET BEFORE init_launchpad!
        
        # Music
        self.melody_notes = [
            261.63,  # C - Do
            293.66,  # D - Re
            329.63,  # E - Mi
            392.00,  # G - Sol
            329.63,  # E - Mi
            293.66,  # D - Re
            261.63,  # C - Do
        ]
        self.melody_index = 0
        self.beat_interval = 0.5  # Time between beats
        self.last_beat_time = time.time()
        
        # Timing windows
        self.perfect_window = 0.1  # ±0.1 seconds
        self.good_window = 0.2     # ±0.2 seconds
        
        # Visual elements
        self.runner_color = (255, 255, 0)  # Yellow
        self.ground_color = (139, 69, 19)   # Brown
        self.cactus_color = (0, 128, 0)     # Green
        self.mountain_color = (128, 128, 128) # Gray
        self.sky_colors = [
            (135, 206, 250),  # Light sky blue
            (255, 182, 193),  # Light pink (sunset)
        ]
        
        # Score and feedback
        self.score = 0
        self.combo = 0
        self.last_timing = None
        
        # NOW load config and init
        self.load_config(config_file)
        self.init_launchpad()
        
    # ... rest of the code remains the same as before ...
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
        self.draw_ground()
        print("Musical Runner initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def draw_ground(self):
        """Draw the ground"""
        for x in range(9):
            led = self.lp.panel.led(x, self.ground_level + 1)
            led.color = self.ground_color
            led = self.lp.panel.led(x, self.ground_level + 2)
            led.color = tuple(int(c * 0.5) for c in self.ground_color)
            
    def draw_runner(self):
        """Draw the runner character"""
        y = self.runner_y - self.jump_height
        if 0 <= y < 9:
            led = self.lp.panel.led(self.runner_pos, y)
            led.color = self.runner_color
            
            # Draw body
            if y + 1 < 9 and not self.jumping:
                led = self.lp.panel.led(self.runner_pos, y + 1)
                led.color = tuple(int(c * 0.7) for c in self.runner_color)
                
    def draw_obstacles(self):
        """Draw all obstacles"""
        with self.lock:
            for x, obstacle_type in self.obstacles:
                if obstacle_type == 'cactus':
                    # Small cactus (1 block high)
                    if 0 <= x < 9:
                        led = self.lp.panel.led(x, self.ground_level)
                        led.color = self.cactus_color
                elif obstacle_type == 'mountain':
                    # Mountain (2 blocks high)
                    if 0 <= x < 9:
                        led = self.lp.panel.led(x, self.ground_level)
                        led.color = self.mountain_color
                        led = self.lp.panel.led(x, self.ground_level - 1)
                        led.color = tuple(int(c * 0.7) for c in self.mountain_color)
                        
    def create_timing_indicator(self):
        """Show timing window on the ground"""
        # Perfect timing zone
        led = self.lp.panel.led(self.runner_pos, self.ground_level + 2)
        led.color = (0, 255, 0)  # Green for perfect
        
        # Good timing zones
        if self.runner_pos - 1 >= 0:
            led = self.lp.panel.led(self.runner_pos - 1, self.ground_level + 2)
            led.color = (255, 255, 0)  # Yellow for good
        if self.runner_pos + 1 < 9:
            led = self.lp.panel.led(self.runner_pos + 1, self.ground_level + 2)
            led.color = (255, 255, 0)  # Yellow for good
            
    def play_melody_note(self, perfect=True):
        """Play the current melody note"""
        freq = self.melody_notes[self.melody_index]
        
        if not perfect:
            # Off-key for bad timing
            freq *= random.choice([0.9, 1.1])  # Slightly sharp or flat
            
        duration = 0.3
        t = np.linspace(0, duration, int(44100 * duration), False)
        
        # Different timbre for perfect vs off
        if perfect:
            # Clear tone
            wave = np.sin(2 * np.pi * freq * t)
            wave += 0.3 * np.sin(2 * np.pi * freq * 2 * t)  # Harmonic
        else:
            # Muddy tone
            wave = np.sin(2 * np.pi * freq * t)
            noise = np.random.normal(0, 0.05, len(t))
            wave = 0.8 * wave + 0.2 * noise
            
        envelope = np.exp(-3 * t)
        wave = wave * envelope
        wave = (wave * 32767 * 0.5).astype(np.int16)
        
        threading.Thread(target=play_wave, args=(wave,)).start()
        
        # Advance melody
        self.melody_index = (self.melody_index + 1) % len(self.melody_notes)
        
    def jump(self):
        """Make the runner jump"""
        if not self.jumping:
            self.jumping = True
            threading.Thread(target=self.jump_animation).start()
            
    def jump_animation(self):
        """Animate the jump"""
        # Jump up
        for i in range(3):
            self.jump_height = i + 1
            time.sleep(0.08)
            
        # Fall down
        for i in range(3):
            self.jump_height = 2 - i
            time.sleep(0.08)
            
        self.jump_height = 0
        self.jumping = False
        
    def check_collision(self):
        """Check if runner hits an obstacle"""
        with self.lock:
            for x, obstacle_type in self.obstacles:
                if x == self.runner_pos and not self.jumping:
                    return True, obstacle_type
        return False, None
        
    def calculate_timing(self):
        """Calculate timing accuracy for button press"""
        with self.lock:
            # Find nearest obstacle
            nearest_distance = 999
            for x, _ in self.obstacles:
                distance = abs(x - self.runner_pos)
                if distance < nearest_distance:
                    nearest_distance = distance
                    
        if nearest_distance == 0:
            return 'perfect'
        elif nearest_distance == 1:
            return 'good'
        else:
            return 'miss'
            
    def handle_button_press(self, button):
        """Handle any button press to jump"""
        timing = self.calculate_timing()
        self.last_timing = timing
        
        # Jump regardless of timing (forgiving for babies)
        self.jump()
        
        # Play note based on timing
        if timing == 'perfect':
            self.play_melody_note(perfect=True)
            self.score += 10
            self.combo += 1
            self.create_perfect_effect()
        elif timing == 'good':
            self.play_melody_note(perfect=True)  # Still play correct note
            self.score += 5
            self.combo += 1
        else:
            self.play_melody_note(perfect=False)  # Off note
            self.combo = 0
            
    def create_perfect_effect(self):
        """Visual effect for perfect timing"""
        # Flash the runner
        original_color = self.runner_color
        for _ in range(2):
            self.runner_color = (255, 255, 255)  # White flash
            time.sleep(0.05)
            self.runner_color = original_color
            time.sleep(0.05)
            
    def spawn_obstacles(self):
        """Spawn new obstacles"""
        while self.running:
            # Wait between obstacles
            time.sleep(random.uniform(1.5, 2.5))
            
            with self.lock:
                # Remove off-screen obstacles
                self.obstacles = [(x, t) for x, t in self.obstacles if x >= -1]
                
                # Spawn new obstacle
                obstacle_type = random.choice(['cactus', 'cactus', 'mountain'])
                self.obstacles.append((8, obstacle_type))
                
    def move_obstacles(self):
        """Move obstacles from right to left"""
        while self.running:
            with self.lock:
                # Move all obstacles left
                self.obstacles = [(x - 1, t) for x, t in self.obstacles]
                
                # Check for collisions
                hit, obstacle_type = self.check_collision()
                if hit and not self.jumping:
                    # Gentle collision - just visual feedback
                    self.collision_effect()
                    
            time.sleep(0.3)  # Speed of scrolling
            
    def collision_effect(self):
        """Gentle collision effect"""
        # Flash red briefly
        led = self.lp.panel.led(self.runner_pos, self.runner_y)
        for _ in range(3):
            led.color = (255, 0, 0)
            time.sleep(0.1)
            led.color = self.runner_color
            time.sleep(0.1)
            
    def update_display(self):
        """Update the display"""
        while self.running:
            # Clear upper area
            for x in range(9):
                for y in range(self.ground_level):
                    led = self.lp.panel.led(x, y)
                    led.color = (0, 0, 0)
                    
            # Draw sky gradient
            for y in range(3):
                color = self.sky_colors[0] if y < 2 else self.sky_colors[1]
                fade = 0.1 + (y * 0.1)
                for x in range(9):
                    led = self.lp.panel.led(x, y)
                    led.color = tuple(int(c * fade) for c in color)
                    
            # Draw game elements
            self.draw_ground()
            self.create_timing_indicator()
            self.draw_obstacles()
            self.draw_runner()
            
            # Show score/combo in top row
            if self.combo >= 3:
                # Light up top row for combo
                combo_color = (
                    min(255, self.combo * 20),
                    max(0, 255 - self.combo * 20),
                    128
                )
                for x in range(min(self.combo, 9)):
                    led = self.lp.panel.led(x, 0)
                    led.color = combo_color
                    
            time.sleep(0.05)
            
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
        print("🎵 Time your jumps to play the melody")
        print("⭐ Perfect timing = correct note + bonus points")
        print("Press Ctrl+C to exit.")
        
        # Start game threads
        spawn_thread = threading.Thread(target=self.spawn_obstacles)
        spawn_thread.daemon = True
        spawn_thread.start()
        
        move_thread = threading.Thread(target=self.move_obstacles)
        move_thread.daemon = True
        move_thread.start()
        
        display_thread = threading.Thread(target=self.update_display)
        display_thread.daemon = True
        display_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print(f"\nGame Over! Score: {self.score}")
            print("Musical Runner stopped.")

if __name__ == "__main__":
    runner = MusicalRunner()
    runner.start()
