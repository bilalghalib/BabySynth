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

class ColorCatcher:
    def __init__(self, config_file='config.yaml'):
        # Initialize all attributes first
        self.running = True
        self.lock = threading.Lock()
        
        # Game elements
        self.paddle_y = 7  # Bottom row
        self.paddle_width = 3  # Start with 3-wide paddle
        self.paddle_center = 4
        
        # Falling gems
        self.gems = []  # List of gems
        self.gem_speed = 0.15  # Much slower base speed
        self.spawn_timer = 0
        self.spawn_delay = 30  # Frames between spawns
        
        # Gem types - simplified and more forgiving
        self.gem_types = {
            'red': {
                'color': (255, 0, 0),
                'note': 261.63,  # C
                'points': 10
            },
            'yellow': {
                'color': (255, 255, 0),
                'note': 329.63,  # E
                'points': 10
            },
            'green': {
                'color': (0, 255, 0),
                'note': 392.00,  # G
                'points': 10
            },
            'blue': {
                'color': (0, 0, 255),
                'note': 523.25,  # C (octave)
                'points': 10
            },
            'rainbow': {
                'color': (255, 255, 255),
                'note': 0,
                'points': 50
            },
            'heart': {  # New healing gem!
                'color': (255, 100, 150),
                'note': 440.00,
                'points': 0  # Gives life instead
            }
        }
        
        # Game state
        self.score = 0
        self.combo = 0
        self.lives = 5
        self.max_lives = 7
        self.missed_gems = 0
        self.catch_streak = 0
        
        # Power-ups
        self.power_up_active = None
        self.power_up_timer = 0
        self.magnet_mode = False
        
        # Visual effects
        self.background_pulse = 0
        self.catch_effects = []
        self.grid_state = {}  # Track LED states
        
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
        print("Color Catcher initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                self.set_led(x, y, (0, 0, 0))
                
    def set_led(self, x, y, color):
        """Only update if changed"""
        if 0 <= x < 9 and 0 <= y < 9:
            if self.grid_state.get((x, y)) != color:
                led = self.lp.panel.led(x, y)
                led.color = color
                self.grid_state[(x, y)] = color
                
    def get_paddle_positions(self):
        """Get all paddle positions based on width"""
        positions = []
        half_width = self.paddle_width // 2
        for i in range(self.paddle_width):
            x = self.paddle_center - half_width + i
            if 0 <= x < 9:
                positions.append(x)
        return positions
        
    def draw_paddle(self):
        """Draw the paddle"""
        # Clear paddle row
        for x in range(9):
            self.set_led(x, self.paddle_y, (0, 0, 0))
            
        # Draw paddle
        positions = self.get_paddle_positions()
        
        if self.power_up_active == 'wide_paddle':
            # Extra wide paddle
            color = (100, 255, 100)  # Green glow
        elif self.magnet_mode:
            # Magnetic paddle
            color = (200, 200, 255)  # Blue glow
        else:
            color = (255, 255, 255)  # Normal white
            
        for x in positions:
            self.set_led(x, self.paddle_y, color)
            
    def draw_lives(self):
        """Show lives as hearts at bottom"""
        for i in range(9):
            if i < self.lives:
                heart_color = (255, 50, 100) if self.lives <= 2 else (255, 100, 150)
                self.set_led(i, 8, heart_color)
            else:
                self.set_led(i, 8, (20, 20, 20))  # Dim outline for lost lives
                
    def play_catch_sound(self, gem_type):
        """Play musical sound for catches"""
        gem_info = self.gem_types[gem_type]
        
        if gem_type == 'rainbow':
            # Magical ascending arpeggio
            notes = [261.63, 329.63, 392.00, 523.25, 659.25]
            for freq in notes:
                t = np.linspace(0, 0.1, int(44100 * 0.1), False)
                wave = np.sin(2 * np.pi * freq * t)
                envelope = np.exp(-2 * t)
                wave = wave * envelope * 0.3
                wave = (wave * 32767).astype(np.int16)
                threading.Thread(target=play_wave, args=(wave,), daemon=True).start()
                time.sleep(0.05)
        elif gem_type == 'heart':
            # Healing sound - two rising notes
            for freq in [392.00, 523.25]:
                t = np.linspace(0, 0.2, int(44100 * 0.2), False)
                wave = np.sin(2 * np.pi * freq * t)
                envelope = np.sin(np.pi * t / 0.2)  # Smooth envelope
                wave = wave * envelope * 0.4
                wave = (wave * 32767).astype(np.int16)
                play_wave(wave)
                time.sleep(0.1)
        else:
            # Normal gem - play its note
            freq = gem_info['note']
            
            # Higher combo = richer sound
            harmonics = 1 + min(3, self.combo // 5)
            
            duration = 0.3
            t = np.linspace(0, duration, int(44100 * duration), False)
            wave = np.zeros_like(t)
            
            for h in range(harmonics):
                wave += np.sin(2 * np.pi * freq * (h + 1) * t) / (h + 1)
                
            envelope = np.exp(-3 * t)
            wave = wave * envelope * 0.5 / harmonics
            wave = (wave * 32767).astype(np.int16)
            play_wave(wave)
            
    def play_miss_sound(self):
        """Gentle miss sound"""
        # Descending slide
        duration = 0.3
        t = np.linspace(0, duration, int(44100 * duration), False)
        freq_start = 300
        freq_end = 150
        freq = freq_start * (freq_end / freq_start) ** (t / duration)
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-3 * t)
        wave = wave * envelope * 0.3
        wave = (wave * 32767).astype(np.int16)
        play_wave(wave)
        
    def spawn_gem(self):
        """Spawn a new gem with better variety"""
        # Weighted spawning based on game state
        if self.lives < 3:
            # More hearts when low on lives
            weights = {
                'red': 20, 'yellow': 20, 'green': 20, 'blue': 20,
                'rainbow': 5, 'heart': 15
            }
        else:
            weights = {
                'red': 22, 'yellow': 22, 'green': 22, 'blue': 22,
                'rainbow': 7, 'heart': 5
            }
            
        gem_type = random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]
        
        # Spawn in columns to make catching easier
        x = random.randint(0, 8)
        
        self.gems.append({
            'x': x,
            'y': 0.0,
            'type': gem_type,
            'color': self.gem_types[gem_type]['color'],
            'rainbow_phase': 0
        })
        
    def move_gems(self):
        """Move gems with magnetism effect"""
        gems_to_remove = []
        
        for gem in self.gems:
            # Apply magnetism if active
            if self.magnet_mode and gem['y'] > 4:
                # Pull gems toward paddle
                paddle_x = self.paddle_center
                diff = paddle_x - gem['x']
                if abs(diff) > 0:
                    gem['x'] += 0.1 * np.sign(diff)
                    
            # Move down
            speed = self.gem_speed * (1 + self.score / 2000)  # Very gradual speed increase
            gem['y'] += speed
            
            # Update rainbow animation
            if gem['type'] == 'rainbow':
                gem['rainbow_phase'] = (gem['rainbow_phase'] + 0.1) % 7
                
            # Check if caught
            if self.paddle_y - 0.5 <= gem['y'] <= self.paddle_y + 0.5:
                gem_x = int(round(gem['x']))
                if gem_x in self.get_paddle_positions():
                    gems_to_remove.append(gem)
                    self.catch_gem(gem)
            elif gem['y'] > 8:
                # Missed
                gems_to_remove.append(gem)
                if gem['type'] not in ['heart']:  # Don't punish for missing hearts
                    self.miss_gem()
                    
        # Remove processed gems
        for gem in gems_to_remove:
            if gem in self.gems:
                self.gems.remove(gem)
                
    def catch_gem(self, gem):
        """Handle catching with more rewards"""
        gem_info = self.gem_types[gem['type']]
        
        # Score and effects
        if gem['type'] == 'heart':
            # Heal!
            self.lives = min(self.max_lives, self.lives + 1)
            self.create_heart_effect()
        else:
            # Points
            points = gem_info['points'] * (1 + self.combo // 10)
            self.score += points
            self.combo += 1
            self.catch_streak += 1
            
        # Play sound
        self.play_catch_sound(gem['type'])
        
        # Visual effect
        self.create_catch_effect(int(gem['x']), gem['color'])
        
        # Power-ups
        if gem['type'] == 'rainbow':
            self.activate_power_up('wide_paddle')
        elif self.catch_streak >= 10:
            self.magnet_mode = True
            self.catch_streak = 0
            
    def miss_gem(self):
        """More forgiving miss handling"""
        self.missed_gems += 1
        
        # Only lose life every 3 misses
        if self.missed_gems >= 3:
            self.lives = max(0, self.lives - 1)
            self.missed_gems = 0
            self.play_miss_sound()
            threading.Thread(target=self.flash_screen, args=((100, 0, 0),)).start()
        else:
            # Just a warning flash
            threading.Thread(target=self.flash_paddle, args=((255, 100, 0),)).start()
            
        self.combo = 0
        self.catch_streak = 0
        self.magnet_mode = False
        
    def create_catch_effect(self, x, color):
        """Sparkle effect for catches"""
        self.catch_effects.append({
            'x': x,
            'y': self.paddle_y,
            'color': color,
            'life': 10
        })
        
    def create_heart_effect(self):
        """Heart healing effect"""
        # Pink pulse from bottom
        for y in range(8, 5, -1):
            for x in range(9):
                self.set_led(x, y, (255, 100, 150))
            time.sleep(0.05)
        time.sleep(0.1)
        # Clear
        for y in range(5, 9):
            for x in range(9):
                self.set_led(x, y, (0, 0, 0))
                
    def flash_paddle(self, color):
        """Flash paddle for warning"""
        for _ in range(2):
            for x in self.get_paddle_positions():
                self.set_led(x, self.paddle_y, color)
            time.sleep(0.1)
            self.draw_paddle()
            time.sleep(0.1)
            
    def flash_screen(self, color):
        """Flash edges for miss"""
        # Flash border
        for _ in range(2):
            for i in range(9):
                self.set_led(0, i, color)
                self.set_led(8, i, color)
                self.set_led(i, 0, color)
            time.sleep(0.1)
            # Clear
            for i in range(9):
                self.set_led(0, i, (0, 0, 0))
                self.set_led(8, i, (0, 0, 0))
                self.set_led(i, 0, (0, 0, 0))
            time.sleep(0.1)
            
    def activate_power_up(self, power_type):
        """Activate power-ups"""
        self.power_up_active = power_type
        if power_type == 'wide_paddle':
            self.paddle_width = 5
            self.power_up_timer = 100
            
    def handle_button_press(self, button):
        """Move paddle smoothly"""
        target_x = button.x
        
        # Smooth movement
        if target_x < self.paddle_center:
            self.paddle_center = max(2, self.paddle_center - 1)
        elif target_x > self.paddle_center:
            self.paddle_center = min(6, self.paddle_center + 1)
            
    def update_display(self):
        """Main display update"""
        while self.running:
            # Clear play area
            for x in range(9):
                for y in range(self.paddle_y):
                    self.set_led(x, y, (0, 0, 0))
                    
            # Background effects
            if self.combo > 20:
                # Starfield for high combo
                if random.random() < 0.1:
                    star_x = random.randint(0, 8)
                    star_y = random.randint(0, 5)
                    self.set_led(star_x, star_y, (100, 100, 100))
                    
            # Draw gems
            for gem in self.gems[:]:  # Copy to avoid threading issues
                y = int(gem['y'])
                x = int(round(gem['x']))
                
                if 0 <= x < 9 and 0 <= y < self.paddle_y:
                    if gem['type'] == 'rainbow':
                        # Animated rainbow
                        colors = [
                            (255, 0, 0), (255, 127, 0), (255, 255, 0),
                            (0, 255, 0), (0, 0, 255), (148, 0, 211)
                        ]
                        color = colors[int(gem['rainbow_phase'])]
                    else:
                        color = gem['color']
                        
                    self.set_led(x, y, color)
                    
                    # Gem trails
                    if y > 0:
                        trail_color = tuple(c // 3 for c in color)
                        self.set_led(x, y - 1, trail_color)
                        
            # Draw effects
            effects_to_remove = []
            for effect in self.catch_effects:
                effect['life'] -= 1
                if effect['life'] > 0:
                    # Sparkle effect
                    for dx, dy in [(0, -1), (1, 0), (-1, 0)]:
                        ex = effect['x'] + dx
                        ey = effect['y'] + dy
                        if 0 <= ex < 9 and 0 <= ey < self.paddle_y:
                            brightness = effect['life'] / 10.0
                            color = tuple(int(c * brightness) for c in effect['color'])
                            self.set_led(ex, ey, color)
                else:
                    effects_to_remove.append(effect)
                    
            for effect in effects_to_remove:
                self.catch_effects.remove(effect)
                
            # Update paddle
            self.draw_paddle()
            
            # Update power-up timer
            if self.power_up_timer > 0:
                self.power_up_timer -= 1
                if self.power_up_timer == 0:
                    self.power_up_active = None
                    self.paddle_width = 3
                    
            # Draw lives
            self.draw_lives()
            
            # Show score/combo on top
            score_lights = min(8, self.score // 100)
            for i in range(9):
                if i <= score_lights:
                    # Golden score indicator
                    self.set_led(i, 0, (255, 215, 0))
                    
            time.sleep(0.05)
            
    def game_loop(self):
        """Main game loop"""
        while self.running and self.lives > 0:
            # Spawn gems
            self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_gem()
                self.spawn_timer = 0
                # Speed up spawning as game progresses
                self.spawn_delay = max(15, 30 - self.score // 200)
                
            # Move gems
            self.move_gems()
            
            time.sleep(0.05)
            
        if self.lives <= 0:
            self.game_over()
            
    def game_over(self):
        """Gentle game over"""
        print(f"\nGreat job! Final Score: {self.score}")
        print(f"Best Combo: {self.combo}")
        
        # Pretty game over animation
        colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255)]
        for color in colors:
            for y in range(9):
                for x in range(9):
                    self.set_led(x, y, color)
                time.sleep(0.1)
                
        time.sleep(1)
        self.clear_grid()
        self.running = False
        
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Color Catcher"""
        print("Starting Color Catcher - Baby Edition!")
        print("💎 Catch the colorful gems!")
        print("🎵 Each gem plays a musical note")
        print("❤️  Pink hearts heal you!")
        print("🌈 Rainbow gems = wide paddle!")
        print("⚡ Catch 10 in a row for MAGNET MODE!")
        print("You can miss 2 gems before losing a life")
        print("Press Ctrl+C to exit.")
        
        # Start game threads
        game_thread = threading.Thread(target=self.game_loop)
        game_thread.daemon = True
        game_thread.start()
        
        display_thread = threading.Thread(target=self.update_display)
        display_thread.daemon = True
        display_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nThanks for playing!")

if __name__ == "__main__":
    catcher = ColorCatcher()
    catcher.start()
