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
        self.paddle_positions = [3, 4, 5]  # 3-wide paddle
        self.paddle_center = 4
        
        # Falling gems
        self.gems = []  # List of {'x': int, 'y': float, 'color': tuple, 'type': str}
        self.gem_speed = 0.3  # Base falling speed
        
        # Gem types and properties
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
                'color': (255, 255, 255),  # Will cycle
                'note': 0,  # Will play chord
                'points': 50
            },
            'bomb': {
                'color': (128, 0, 128),  # Purple
                'note': 100,  # Low rumble
                'points': -20
            }
        }
        
        # Musical elements
        self.scale_position = 0
        self.harmony_notes = []
        self.music_pattern = []
        
        # Score and combo
        self.score = 0
        self.combo = 0
        self.multiplier = 1
        self.lives = 5
        
        # Visual effects
        self.background_pulse = 0
        self.catch_effects = []
        
        # Power-ups
        self.power_up_active = None
        self.power_up_timer = 0
        
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
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def draw_paddle(self):
        """Draw the catching paddle"""
        self.paddle_positions = [
            self.paddle_center - 1,
            self.paddle_center,
            self.paddle_center + 1
        ]
        
        # Clear paddle row first
        for x in range(9):
            led = self.lp.panel.led(x, self.paddle_y)
            led.color = (0, 0, 0)
            
        # Draw paddle with gradient
        paddle_colors = [
            (200, 200, 200),  # Light gray edges
            (255, 255, 255),  # White center
            (200, 200, 200),  # Light gray edges
        ]
        
        for i, x in enumerate(self.paddle_positions):
            if 0 <= x < 9:
                led = self.lp.panel.led(x, self.paddle_y)
                led.color = paddle_colors[i]
                
    def draw_lives(self):
        """Show remaining lives at bottom"""
        for i in range(self.lives):
            if i < 9:
                led = self.lp.panel.led(i, 8)
                led.color = (255, 0, 0) if self.lives <= 2 else (0, 255, 0)
                
    def play_catch_sound(self, gem_type):
        """Play sound when catching a gem"""
        gem_info = self.gem_types[gem_type]
        
        if gem_type == 'rainbow':
            # Play magical chord
            frequencies = [261.63, 329.63, 392.00, 523.25]
            waves = []
            for freq in frequencies:
                t = np.linspace(0, 0.5, int(44100 * 0.5), False)
                wave = np.sin(2 * np.pi * freq * t)
                waves.append(wave)
            combined = np.sum(waves, axis=0) / len(waves)
            envelope = np.exp(-2 * t)
            combined = combined * envelope
            combined = (combined * 32767 * 0.5).astype(np.int16)
            play_wave(combined)
        elif gem_type == 'bomb':
            # Play explosion sound
            duration = 0.3
            t = np.linspace(0, duration, int(44100 * duration), False)
            # Low frequency rumble with noise
            wave = np.sin(2 * np.pi * 60 * t)
            noise = np.random.normal(0, 0.3, len(t))
            wave = 0.3 * wave + 0.7 * noise
            envelope = np.exp(-10 * t)
            wave = wave * envelope
            wave = (wave * 32767 * 0.5).astype(np.int16)
            play_wave(wave)
        else:
            # Play gem's note
            freq = gem_info['note']
            duration = 0.3
            t = np.linspace(0, duration, int(44100 * duration), False)
            wave = np.sin(2 * np.pi * freq * t)
            # Add harmonics for richness
            wave += 0.3 * np.sin(2 * np.pi * freq * 2 * t)
            envelope = np.exp(-3 * t)
            wave = wave * envelope
            wave = (wave * 32767 * 0.5).astype(np.int16)
            play_wave(wave)
            
            # Add to music pattern
            self.music_pattern.append(freq)
            if len(self.music_pattern) > 8:
                self.music_pattern.pop(0)
                
    def spawn_gem(self):
        """Spawn a new falling gem"""
        # Weighted random selection
        gem_weights = {
            'red': 25,
            'yellow': 25,
            'green': 25,
            'blue': 25,
            'rainbow': 5,   # Rare
            'bomb': 10,     # Occasional challenge
        }
        
        gem_type = random.choices(
            list(gem_weights.keys()),
            weights=list(gem_weights.values())
        )[0]
        
        x = random.randint(0, 8)
        
        with self.lock:
            self.gems.append({
                'x': x,
                'y': 0.0,
                'type': gem_type,
                'color': self.gem_types[gem_type]['color'],
                'rainbow_phase': 0 if gem_type == 'rainbow' else None
            })
            
    def move_gems(self):
        """Move all gems down"""
        with self.lock:
            gems_to_remove = []
            
            for gem in self.gems:
                # Move gem down
                speed = self.gem_speed * (1 + self.score / 1000)  # Speed up over time
                gem['y'] += speed
                
                # Update rainbow color
                if gem['type'] == 'rainbow':
                    gem['rainbow_phase'] = (gem['rainbow_phase'] + 0.2) % 7
                    rainbow_colors = [
                        (255, 0, 0), (255, 127, 0), (255, 255, 0),
                        (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)
                    ]
                    gem['color'] = rainbow_colors[int(gem['rainbow_phase'])]
                
                # Check if caught
                if int(gem['y']) == self.paddle_y:
                    if gem['x'] in self.paddle_positions:
                        # Caught!
                        gems_to_remove.append(gem)
                        self.catch_gem(gem)
                    elif int(gem['y']) > self.paddle_y:
                        # Missed
                        gems_to_remove.append(gem)
                        if gem['type'] not in ['bomb']:  # Don't lose life for missing bombs
                            self.miss_gem(gem)
                elif gem['y'] > 8:
                    # Off screen
                    gems_to_remove.append(gem)
                    if gem['type'] not in ['bomb']:
                        self.miss_gem(gem)
                        
            # Remove caught/missed gems
            for gem in gems_to_remove:
                if gem in self.gems:
                    self.gems.remove(gem)
                    
    def catch_gem(self, gem):
        """Handle catching a gem"""
        gem_info = self.gem_types[gem['type']]
        
        # Update score
        points = gem_info['points'] * self.multiplier
        self.score += points
        
        # Update combo
        if gem['type'] != 'bomb':
            self.combo += 1
            self.multiplier = 1 + (self.combo // 5)  # Multiplier increases every 5
        else:
            self.combo = 0
            self.multiplier = 1
            self.lives = max(0, self.lives - 1)
            
        # Play sound
        threading.Thread(target=self.play_catch_sound, args=(gem['type'],)).start()
        
        # Visual effect
        self.create_catch_effect(gem['x'], gem['color'])
        
        # Special effects
        if gem['type'] == 'rainbow':
            self.activate_power_up('rainbow_paddle')
            
    def miss_gem(self, gem):
        """Handle missing a gem"""
        self.lives = max(0, self.lives - 1)
        self.combo = 0
        self.multiplier = 1
        
        # Flash paddle red
        threading.Thread(target=self.miss_effect).start()
        
    def miss_effect(self):
        """Visual effect for missing"""
        for _ in range(3):
            for x in self.paddle_positions:
                if 0 <= x < 9:
                    led = self.lp.panel.led(x, self.paddle_y)
                    led.color = (255, 0, 0)
            time.sleep(0.1)
            self.draw_paddle()
            time.sleep(0.1)
            
    def create_catch_effect(self, x, color):
        """Create visual effect when catching"""
        with self.lock:
            self.catch_effects.append({
                'x': x,
                'y': self.paddle_y,
                'color': color,
                'radius': 0,
                'max_radius': 3
            })
            
    def activate_power_up(self, power_type):
        """Activate a power-up"""
        self.power_up_active = power_type
        self.power_up_timer = 100  # About 5 seconds
        
    def handle_button_press(self, button):
        """Handle button press to move paddle"""
        x = button.x
        
        # Move paddle to pressed position
        if 1 <= x <= 7:  # Keep paddle on screen
            self.paddle_center = x
        elif x == 0:
            self.paddle_center = 1
        elif x == 8:
            self.paddle_center = 7
            
    def update_display(self):
        """Update the game display"""
        while self.running:
            # Clear grid except paddle and lives
            for x in range(9):
                for y in range(self.paddle_y):
                    led = self.lp.panel.led(x, y)
                    led.color = (0, 0, 0)
                    
            # Background pulse effect based on combo
            if self.combo > 10:
                self.background_pulse = (self.background_pulse + 0.1) % (2 * np.pi)
                bg_brightness = int((np.sin(self.background_pulse) + 1) * 10)
                bg_color = (bg_brightness, 0, bg_brightness)
                for x in range(9):
                    for y in range(self.paddle_y):
                        led = self.lp.panel.led(x, y)
                        led.color = bg_color
                        
            # Draw gems
            with self.lock:
                for gem in self.gems:
                    y = int(gem['y'])
                    if 0 <= y < self.paddle_y:
                        led = self.lp.panel.led(gem['x'], y)
                        led.color = gem['color']
                        
                        # Gem glow
                        if gem['type'] == 'rainbow':
                            # Adjacent cells glow
                            for dx in [-1, 1]:
                                if 0 <= gem['x'] + dx < 9:
                                    led = self.lp.panel.led(gem['x'] + dx, y)
                                    led.color = tuple(c // 3 for c in gem['color'])
                                    
            # Draw catch effects
            with self.lock:
                effects_to_remove = []
                for effect in self.catch_effects:
                    effect['radius'] += 0.5
                    if effect['radius'] <= effect['max_radius']:
                        # Draw expanding circle
                        radius = int(effect['radius'])
                        for dx in range(-radius, radius + 1):
                            for dy in range(-radius, radius + 1):
                                if abs(dx) == radius or abs(dy) == radius:
                                    ex = effect['x'] + dx
                                    ey = effect['y'] + dy
                                    if 0 <= ex < 9 and 0 <= ey < self.paddle_y:
                                        led = self.lp.panel.led(ex, ey)
                                        brightness = 1.0 - (effect['radius'] / effect['max_radius'])
                                        led.color = tuple(int(c * brightness) for c in effect['color'])
                    else:
                        effects_to_remove.append(effect)
                        
                for effect in effects_to_remove:
                    self.catch_effects.remove(effect)
                    
            # Draw paddle (with power-up effects)
            if self.power_up_active == 'rainbow_paddle':
                # Rainbow paddle
                rainbow_colors = [
                    (255, 0, 0), (255, 255, 0), (0, 255, 0)
                ]
                for i, x in enumerate(self.paddle_positions):
                    if 0 <= x < 9:
                        led = self.lp.panel.led(x, self.paddle_y)
                        led.color = rainbow_colors[i % len(rainbow_colors)]
                self.power_up_timer -= 1
                if self.power_up_timer <= 0:
                    self.power_up_active = None
            else:
                self.draw_paddle()
                
            # Draw lives
            self.draw_lives()
            
            # Show score/multiplier in top row
            if self.multiplier > 1:
                for i in range(min(self.multiplier, 9)):
                    led = self.lp.panel.led(i, 0)
                    led.color = (255, 215, 0)  # Gold
                    
            time.sleep(0.05)
            
    def spawn_loop(self):
        """Spawn gems periodically"""
        while self.running:
            self.spawn_gem()
            # Spawn faster as score increases
            spawn_delay = max(0.5, 2.0 - self.score / 500)
            time.sleep(spawn_delay)
            
    def game_loop(self):
        """Main game loop"""
        while self.running and self.lives > 0:
            self.move_gems()
            time.sleep(0.05)
            
        if self.lives == 0:
            self.game_over()
            
    def game_over(self):
        """Game over sequence"""
        print(f"\nGame Over! Final Score: {self.score}")
        
        # Clear gems
        with self.lock:
            self.gems = []
            
        # Game over animation
        for y in range(9):
            for x in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (255, 0, 0)
            time.sleep(0.1)
            
        time.sleep(1)
        self.clear_grid()
        
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Color Catcher"""
        print("Starting Color Catcher!")
        print("💎 Catch the falling gems!")
        print("🎵 Each gem plays a musical note")
        print("🌈 Rainbow gems = 50 points + power-up!")
        print("💣 Avoid purple bombs!")
        print("Press any button to move the paddle")
        print("Press Ctrl+C to exit.")
        
        # Start game threads
        spawn_thread = threading.Thread(target=self.spawn_loop)
        spawn_thread.daemon = True
        spawn_thread.start()
        
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
            print("\nColor Catcher stopped.")

if __name__ == "__main__":
    catcher = ColorCatcher()
    catcher.start()
