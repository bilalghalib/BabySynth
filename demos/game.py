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

class MusicalBreakout:
    def __init__(self, config_file='config.yaml'):
        # Initialize grid_state FIRST
        self.grid_state = {}
        self.running = True
        self.lock = threading.Lock()
        
        # Game elements
        self.paddle_y = 7
        self.paddle_x = 4
        self.paddle_width = 3
        
        # Ball physics
        self.ball_x = 4.5
        self.ball_y = 6.0
        self.ball_vx = 0.2
        self.ball_vy = -0.2
        self.ball_speed = 0.2
        
        # Bricks
        self.bricks = {}  # {(x,y): brick_data}
        
        # Previous positions for anti-flicker
        self.prev_ball_pos = None
        self.prev_paddle_pos = None
        
        # Musical elements
        self.scale = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
        self.current_chord = []
        self.combo = 0
        self.rhythm_phase = 0
        
        # Power-ups
        self.power_ups = []  # Falling power-ups
        self.active_powers = {}
        self.multiball = []  # Extra balls
        
        # Score
        self.score = 0
        self.lives = 5
        
        # Brick types with musical properties
        self.brick_types = {
            'red': {
                'color': (255, 0, 0),
                'hits': 1,
                'points': 10,
                'instrument': 'piano',
                'note_offset': 0
            },
            'orange': {
                'color': (255, 127, 0),
                'hits': 1,
                'points': 20,
                'instrument': 'vibraphone',
                'note_offset': 2
            },
            'yellow': {
                'color': (255, 255, 0),
                'hits': 1,
                'points': 30,
                'instrument': 'marimba',
                'note_offset': 4
            },
            'green': {
                'color': (0, 255, 0),
                'hits': 2,
                'points': 40,
                'instrument': 'strings',
                'note_offset': 5
            },
            'blue': {
                'color': (0, 0, 255),
                'hits': 2,
                'points': 50,
                'instrument': 'bell',
                'note_offset': 7
            },
            'purple': {
                'color': (128, 0, 128),
                'hits': 3,
                'points': 100,
                'instrument': 'choir',
                'note_offset': 9
            }
        }
        
        # NOW initialize hardware
        self.load_config(config_file)
        self.init_launchpad()
        self.setup_bricks()
        
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
        print("Musical Breakout initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                self.set_led(x, y, (0, 0, 0))
        # Reset grid state after clearing
        self.grid_state = {}
        
    def set_led(self, x, y, color):
        """Only update LED if color changed"""
        if 0 <= x < 9 and 0 <= y < 9:
            current = self.grid_state.get((x, y))
            if current != color:
                led = self.lp.panel.led(x, y)
                led.color = color
                self.grid_state[(x, y)] = color
                
    def setup_bricks(self):
        """Create brick layout"""
        # Rainbow pattern
        brick_rows = [
            ('red', 1),
            ('orange', 1),
            ('yellow', 2),
            ('green', 2),
            ('blue', 3),
        ]
        
        for row, (brick_type, y) in enumerate(brick_rows):
            for x in range(1, 8):  # Leave borders empty
                self.bricks[(x, y)] = {
                    'type': brick_type,
                    'hits': self.brick_types[brick_type]['hits'],
                    'breaking': False
                }
                
    def play_brick_hit(self, brick_type, x, y):
        """Play musical note when brick is hit"""
        brick_info = self.brick_types[brick_type]
        
        # Note based on position and type
        base_note = self.scale[x % len(self.scale)]
        octave_mult = 1 + (y / 9)  # Higher bricks = higher octave
        freq = base_note * octave_mult
        
        # Different instruments
        duration = 0.3
        t = np.linspace(0, duration, int(44100 * duration), False)
        
        if brick_info['instrument'] == 'piano':
            wave = np.sin(2 * np.pi * freq * t)
            wave += 0.3 * np.sin(2 * np.pi * freq * 2 * t)
            envelope = np.exp(-3 * t)
        elif brick_info['instrument'] == 'vibraphone':
            wave = np.sin(2 * np.pi * freq * t)
            vibrato = 1 + 0.01 * np.sin(2 * np.pi * 6 * t)
            wave = wave * vibrato
            envelope = np.exp(-2 * t)
        elif brick_info['instrument'] == 'marimba':
            wave = np.sin(2 * np.pi * freq * t)
            wave += 0.5 * np.sin(2 * np.pi * freq * 0.5 * t)
            envelope = np.exp(-5 * t)
        elif brick_info['instrument'] == 'strings':
            # Multiple detuned oscillators
            wave = np.sin(2 * np.pi * freq * t)
            wave += np.sin(2 * np.pi * freq * 1.003 * t)
            wave += np.sin(2 * np.pi * freq * 0.997 * t)
            wave = wave / 3
            envelope = 0.8 * np.ones_like(t)
        elif brick_info['instrument'] == 'bell':
            wave = np.sin(2 * np.pi * freq * t)
            wave += 0.5 * np.sin(2 * np.pi * freq * 2.4 * t)
            wave += 0.3 * np.sin(2 * np.pi * freq * 3.6 * t)
            envelope = np.exp(-1 * t)
        elif brick_info['instrument'] == 'choir':
            # Formant synthesis (simplified)
            wave = np.sin(2 * np.pi * freq * t)
            wave += 0.7 * np.sin(2 * np.pi * freq * 3 * t)
            wave += 0.5 * np.sin(2 * np.pi * freq * 5 * t)
            wave = wave / 2.2
            envelope = np.ones_like(t) * 0.7
        else:
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-3 * t)
            
        wave = wave * envelope * 0.5
        wave = (wave * 32767).astype(np.int16)
        threading.Thread(target=play_wave, args=(wave,)).start()
        
        # Add to current chord
        self.current_chord.append(freq)
        if len(self.current_chord) > 3:
            self.current_chord.pop(0)
            
    def play_paddle_hit(self, hit_x):
        """Play sound when ball hits paddle"""
        # Pitch based on where ball hits paddle
        paddle_positions = self.get_paddle_positions()
        if paddle_positions:
            relative_pos = (hit_x - paddle_positions[0]) / len(paddle_positions)
            
            # Map position to note
            note_index = int(relative_pos * len(self.scale))
            freq = self.scale[note_index % len(self.scale)] * 0.5  # Lower octave
            
            # Quick percussion sound
            duration = 0.1
            t = np.linspace(0, duration, int(44100 * duration), False)
            wave = np.sin(2 * np.pi * freq * t)
            noise = np.random.normal(0, 0.1, len(t))
            wave = 0.7 * wave + 0.3 * noise
            envelope = np.exp(-20 * t)
            wave = wave * envelope * 0.4
            wave = (wave * 32767).astype(np.int16)
            play_wave(wave)
            
    def spawn_power_up(self, x, y, power_type=None):
        """Spawn a falling power-up"""
        if power_type is None:
            power_type = random.choice(['wide', 'multi', 'slow', 'laser'])
            
        power_up = {
            'x': x,
            'y': y,
            'type': power_type,
            'vy': 0.1
        }
        
        self.power_ups.append(power_up)
        
    def activate_power_up(self, power_type):
        """Activate a power-up"""
        if power_type == 'wide':
            self.paddle_width = 5
            self.active_powers['wide'] = 200  # Duration
        elif power_type == 'multi':
            # Add extra balls
            for i in range(2):
                self.multiball.append({
                    'x': self.ball_x + random.uniform(-1, 1),
                    'y': self.ball_y,
                    'vx': random.uniform(-0.3, 0.3),
                    'vy': -0.2
                })
        elif power_type == 'slow':
            self.ball_speed = 0.1
            self.active_powers['slow'] = 150
        elif power_type == 'laser':
            self.active_powers['laser'] = 100
            
        # Power-up sound
        self.play_power_up_sound(power_type)
        
    def play_power_up_sound(self, power_type):
        """Play power-up collection sound"""
        sounds = {
            'wide': [523.25, 659.25, 783.99],      # C E G ascending
            'multi': [261.63, 261.63, 523.25],     # C C C(octave)
            'slow': [392.00, 329.63, 261.63],      # G E C descending
            'laser': [1046.50, 1046.50, 1046.50]   # High C repeated
        }
        
        notes = sounds.get(power_type, [523.25])
        for freq in notes:
            t = np.linspace(0, 0.1, int(44100 * 0.1), False)
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-5 * t)
            wave = wave * envelope * 0.5
            wave = (wave * 32767).astype(np.int16)
            threading.Thread(target=play_wave, args=(wave,)).start()
            time.sleep(0.08)
            
    def get_paddle_positions(self):
        """Get all paddle x positions"""
        positions = []
        start = self.paddle_x - self.paddle_width // 2
        for i in range(self.paddle_width):
            x = start + i
            if 0 <= x < 9:
                positions.append(x)
        return positions
        
    def move_ball(self):
        """Move ball and handle collisions"""
        # Store previous position for clearing
        self.prev_ball_pos = (int(self.ball_x), int(self.ball_y))
        
        # Move ball
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy
        
        # Wall collisions
        if self.ball_x <= 0 or self.ball_x >= 8:
            self.ball_vx = -self.ball_vx
            self.ball_x = max(0.1, min(7.9, self.ball_x))
            # Wall hit sound
            self.play_wall_hit()
            
        if self.ball_y <= 0:
            self.ball_vy = -self.ball_vy
            self.ball_y = 0.1
            self.play_wall_hit()
            
        # Paddle collision
        if (self.paddle_y - 0.5 <= self.ball_y <= self.paddle_y + 0.5 and
            int(self.ball_x) in self.get_paddle_positions()):
            self.ball_vy = -abs(self.ball_vy)
            
            # Angle based on hit position
            paddle_center = self.paddle_x
            offset = (self.ball_x - paddle_center) / (self.paddle_width / 2)
            self.ball_vx = offset * 0.3
            
            # Play paddle sound
            self.play_paddle_hit(int(self.ball_x))
            self.combo += 1
            
        # Brick collisions
        ball_grid_x = int(self.ball_x)
        ball_grid_y = int(self.ball_y)
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check_x = ball_grid_x + dx
                check_y = ball_grid_y + dy
                
                if (check_x, check_y) in self.bricks:
                    brick = self.bricks[(check_x, check_y)]
                    if not brick['breaking']:
                        # Hit brick
                        brick['hits'] -= 1
                        
                        # Play sound
                        self.play_brick_hit(brick['type'], check_x, check_y)
                        
                        if brick['hits'] <= 0:
                            # Destroy brick
                            brick['breaking'] = True
                            self.score += self.brick_types[brick['type']]['points']
                            
                            # Chance for power-up
                            if random.random() < 0.2:
                                self.spawn_power_up(check_x, check_y)
                                
                            # Remove brick after animation
                            threading.Thread(
                                target=self.destroy_brick_animation,
                                args=(check_x, check_y)
                            ).start()
                            
                        # Bounce ball
                        if dx != 0:
                            self.ball_vx = -self.ball_vx
                        if dy != 0:
                            self.ball_vy = -self.ball_vy
                            
        # Bottom boundary (lose ball)
        if self.ball_y > 8:
            self.lives -= 1
            self.reset_ball()
            if self.lives <= 0:
                self.game_over()
                
    def play_wall_hit(self):
        """Quick wall bounce sound"""
        freq = 200
        duration = 0.05
        t = np.linspace(0, duration, int(44100 * duration), False)
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-50 * t)
        wave = wave * envelope * 0.3
        wave = (wave * 32767).astype(np.int16)
        play_wave(wave)
        
    def destroy_brick_animation(self, x, y):
        """Animate brick destruction"""
        # Flash white
        for _ in range(3):
            self.set_led(x, y, (255, 255, 255))
            time.sleep(0.05)
            self.set_led(x, y, (0, 0, 0))
            time.sleep(0.05)
            
        # Remove from dict
        with self.lock:
            if (x, y) in self.bricks:
                del self.bricks[(x, y)]
                
    def reset_ball(self):
        """Reset ball position"""
        self.ball_x = 4.5
        self.ball_y = 6.0
        self.ball_vx = random.uniform(-0.2, 0.2)
        self.ball_vy = -0.2
        self.combo = 0
        
        # Clear multiball
        self.multiball = []
        
        # Loss sound
        for freq in [440, 220, 110]:
            t = np.linspace(0, 0.2, int(44100 * 0.2), False)
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-5 * t)
            wave = wave * envelope * 0.3
            wave = (wave * 32767).astype(np.int16)
            play_wave(wave)
            time.sleep(0.15)
            
    def handle_button_press(self, button):
        """Move paddle based on button press"""
        target_x = button.x
        
        # Smooth movement toward target
        if target_x < self.paddle_x:
            self.paddle_x = max(self.paddle_width // 2, self.paddle_x - 1)
        elif target_x > self.paddle_x:
            self.paddle_x = min(8 - self.paddle_width // 2, self.paddle_x + 1)
            
        # Laser power-up
        if 'laser' in self.active_powers:
            # Shoot laser from paddle
            self.shoot_laser(button.x)
            
    def shoot_laser(self, x):
        """Shoot laser up from paddle position"""
        # Laser sound
        freq = 2000
        duration = 0.1
        t = np.linspace(0, duration, int(44100 * duration), False)
        freq_sweep = freq * (1 + t)  # Rising pitch
        wave = np.sin(2 * np.pi * freq_sweep * t)
        envelope = 1 - t / duration
        wave = wave * envelope * 0.3
        wave = (wave * 32767).astype(np.int16)
        play_wave(wave)
        
        # Visual effect and destroy bricks
        for y in range(self.paddle_y - 1, -1, -1):
            self.set_led(x, y, (255, 255, 0))
            if (x, y) in self.bricks:
                brick = self.bricks[(x, y)]
                brick['breaking'] = True
                self.score += self.brick_types[brick['type']]['points']
                self.destroy_brick_animation(x, y)
            time.sleep(0.02)
            
        # Clear laser trail
        time.sleep(0.1)
        for y in range(self.paddle_y):
            self.set_led(x, y, (0, 0, 0))
            
    def update_display(self):
        """Update display with minimal flicker"""
        while self.running:
            # Clear only moving elements
            if self.prev_ball_pos:
                self.set_led(self.prev_ball_pos[0], self.prev_ball_pos[1], (0, 0, 0))
                
            if self.prev_paddle_pos:
                for x in self.prev_paddle_pos:
                    self.set_led(x, self.paddle_y, (0, 0, 0))
                    
            # Draw bricks
            for (x, y), brick in list(self.bricks.items()):
                if not brick['breaking']:
                    brick_type = brick['type']
                    color = self.brick_types[brick_type]['color']
                    
                    # Dim damaged bricks
                    if brick['hits'] < self.brick_types[brick_type]['hits']:
                        dim_factor = brick['hits'] / self.brick_types[brick_type]['hits']
                        color = tuple(int(c * dim_factor) for c in color)
                        
                    self.set_led(x, y, color)
                    
            # Draw power-ups
            for power in self.power_ups[:]:
                x = int(power['x'])
                y = int(power['y'])
                if 0 <= x < 9 and 0 <= y < 9:
                    # Power-up colors
                    colors = {
                        'wide': (0, 255, 0),
                        'multi': (255, 255, 0),
                        'slow': (0, 0, 255),
                        'laser': (255, 0, 255)
                    }
                    self.set_led(x, y, colors.get(power['type'], (255, 255, 255)))
                    
            # Draw paddle
            paddle_positions = self.get_paddle_positions()
            self.prev_paddle_pos = paddle_positions
            
            paddle_color = (255, 255, 255)
            if 'wide' in self.active_powers:
                paddle_color = (100, 255, 100)
            elif 'laser' in self.active_powers:
                paddle_color = (255, 100, 255)
                
            for x in paddle_positions:
                self.set_led(x, self.paddle_y, paddle_color)
                
            # Draw ball
            ball_x = int(self.ball_x)
            ball_y = int(self.ball_y)
            if 0 <= ball_x < 9 and 0 <= ball_y < 9:
                # Ball color changes with combo
                if self.combo > 10:
                    ball_color = (255, 255, 0)  # Yellow
                elif self.combo > 5:
                    ball_color = (255, 127, 0)  # Orange
                else:
                    ball_color = (255, 255, 255)  # White
                    
                self.set_led(ball_x, ball_y, ball_color)
                
            # Draw multiball
            for ball in self.multiball:
                bx = int(ball['x'])
                by = int(ball['y'])
                if 0 <= bx < 9 and 0 <= by < 9:
                    self.set_led(bx, by, (100, 100, 255))
                    
            # Lives indicator on bottom row
            for i in range(9):
                if i < self.lives:
                    self.set_led(i, 8, (255, 0, 0))
                else:
                    self.set_led(i, 8, (50, 0, 0))
                    
            time.sleep(0.05)
            
    def game_loop(self):
        """Main game loop"""
        while self.running:
            # Move main ball
            self.move_ball()
            
            # Move extra balls
            for ball in self.multiball[:]:
                # Simple physics for extra balls
                ball['x'] += ball['vx']
                ball['y'] += ball['vy']
                
                # Bounce off walls
                if ball['x'] <= 0 or ball['x'] >= 8:
                    ball['vx'] = -ball['vx']
                if ball['y'] <= 0:
                    ball['vy'] = -ball['vy']
                    
                # Remove if falls off bottom
                if ball['y'] > 8:
                    self.multiball.remove(ball)
                    
            # Move power-ups
            for power in self.power_ups[:]:
                power['y'] += power['vy']
                
                # Check collection
                if (abs(power['x'] - self.paddle_x) < self.paddle_width / 2 and
                    abs(power['y'] - self.paddle_y) < 1):
                    self.activate_power_up(power['type'])
                    self.power_ups.remove(power)
                elif power['y'] > 8:
                    self.power_ups.remove(power)
                    
            # Update power-up timers
            for power, timer in list(self.active_powers.items()):
                self.active_powers[power] = timer - 1
                if timer <= 0:
                    del self.active_powers[power]
                    # Reset
                    if power == 'wide':
                        self.paddle_width = 3
                    elif power == 'slow':
                        self.ball_speed = 0.2
                        
            # Check win condition
            if not self.bricks:
                self.level_complete()
                
            time.sleep(0.05)
            
    def level_complete(self):
        """Handle level completion"""
        print("Level Complete!")
        
        # Victory fanfare
        victory_notes = [523.25, 659.25, 783.99, 1046.50]
        for freq in victory_notes:
            t = np.linspace(0, 0.2, int(44100 * 0.2), False)
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-2 * t)
            wave = wave * envelope * 0.5
            wave = (wave * 32767).astype(np.int16)
            play_wave(wave)
            time.sleep(0.15)
            
        # Reset with new bricks
        self.setup_bricks()
        self.reset_ball()
        
    def game_over(self):
        """Game over sequence"""
        self.running = False
        print(f"\nGame Over!")
        print(f"Final Score: {self.score}")
        
        # Sad music
        for freq in [440, 415, 392, 369, 349, 329]:
            t = np.linspace(0, 0.3, int(44100 * 0.3), False)
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-2 * t)
            wave = wave * envelope * 0.3
            wave = (wave * 32767).astype(np.int16)
            play_wave(wave)
            time.sleep(0.2)
            
    def play_background_beat(self):
        """Rhythmic background"""
        while self.running:
            # Simple beat
            self.rhythm_phase = (self.rhythm_phase + 1) % 8
            
            if self.rhythm_phase % 4 == 0:
                # Kick
                freq = 60
            elif self.rhythm_phase % 4 == 2:
                # Snare
                freq = 200
            else:
                time.sleep(0.125)
                continue
                
            duration = 0.1
            t = np.linspace(0, duration, int(44100 * duration), False)
            wave = np.sin(2 * np.pi * freq * t)
            if freq == 200:
                noise = np.random.normal(0, 0.1, len(t))
                wave = 0.5 * wave + 0.5 * noise
            envelope = np.exp(-20 * t)
            wave = wave * envelope * 0.1
            wave = (wave * 32767).astype(np.int16)
            play_wave(wave)
            
            time.sleep(0.125)  # Eighth note timing
            
    def event_loop(self):
        """Handle button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Musical Breakout"""
        print("Starting Musical Breakout!")
        print("🎯 Break the colorful bricks")
        print("🎵 Each brick plays a different note")
        print("🎹 Different rows = different instruments")
        print("⚡ Collect power-ups:")
        print("   💚 Green = Wide paddle")
        print("   💛 Yellow = Multiball")
        print("   💙 Blue = Slow motion")
        print("   💜 Purple = Laser paddle")
        print("Press buttons to move paddle")
        print("Press Ctrl+C to exit.")
        
        # Start threads
        game_thread = threading.Thread(target=self.game_loop)
        game_thread.daemon = True
        game_thread.start()
        
        display_thread = threading.Thread(target=self.update_display)
        display_thread.daemon = True
        display_thread.start()
        
        beat_thread = threading.Thread(target=self.play_background_beat)
        beat_thread.daemon = True
        beat_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nThanks for playing!")

if __name__ == "__main__":
    breakout = MusicalBreakout()
    breakout.start()