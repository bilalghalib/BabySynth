import yaml
import time
import random
import threading
import numpy as np
import simpleaudio as sa
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import generate_sine_wave, play_wave

class MusicalTetris:
    def __init__(self, config_file='config.yaml'):
        self.load_config(config_file)
        self.init_launchpad()
        self.running = True
        self.lock = threading.Lock()
        
        # Game state
        self.grid = [[0 for _ in range(9)] for _ in range(9)]
        self.current_piece = None
        self.piece_x = 4
        self.piece_y = 0
        self.fall_timer = 0
        self.fall_speed = 20  # Frames per drop
        self.score = 0
        self.lines_cleared = 0
        
        # Simplified pieces (2x2 and 3x2 only for 9x9 grid)
        self.pieces = {
            'square': {
                'shape': [[1, 1], [1, 1]],
                'color': (255, 255, 0),  # Yellow
                'note': 329.63  # E
            },
            'line': {
                'shape': [[1, 1, 1]],
                'color': (0, 255, 255),  # Cyan
                'note': 440.00  # A
            },
            'L': {
                'shape': [[1, 0], [1, 0], [1, 1]],
                'color': (255, 127, 0),  # Orange
                'note': 349.23  # F
            },
            'T': {
                'shape': [[0, 1, 0], [1, 1, 1]],
                'color': (255, 0, 255),  # Purple
                'note': 392.00  # G
            }
        }
        
        # Tetris theme notes (simplified Korobeiniki)
        self.tetris_melody = [
            (659.25, 0.25),  # E
            (493.88, 0.125), # B
            (523.25, 0.125), # C
            (587.33, 0.25),  # D
            (523.25, 0.125), # C
            (493.88, 0.125), # B
            (440.00, 0.25),  # A
            (440.00, 0.125), # A
            (523.25, 0.125), # C
            (659.25, 0.25),  # E
            (587.33, 0.125), # D
            (523.25, 0.125), # C
            (493.88, 0.5),   # B
        ]
        self.melody_index = 0
        
        # Colors for filled blocks
        self.level_colors = [
            (100, 100, 255),  # Blue
            (100, 255, 100),  # Green
            (255, 100, 100),  # Red
            (255, 255, 100),  # Yellow
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
        print("Musical Tetris initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def spawn_piece(self):
        """Spawn a new tetris piece"""
        piece_type = random.choice(list(self.pieces.keys()))
        self.current_piece = self.pieces[piece_type].copy()
        self.piece_x = 3
        self.piece_y = 0
        
        # Play spawn sound
        freq = self.current_piece['note']
        self.play_note(freq, 0.1)
        
        # Check if game over
        if self.check_collision():
            self.game_over()
            
    def play_note(self, freq, duration):
        """Play a single note"""
        t = np.linspace(0, duration, int(44100 * duration), False)
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-3 * t)
        wave = wave * envelope * 0.4
        wave = (wave * 32767).astype(np.int16)
        threading.Thread(target=play_wave, args=(wave,)).start()
        
    def play_tetris_theme(self):
        """Play the Tetris theme continuously"""
        while self.running:
            freq, duration = self.tetris_melody[self.melody_index]
            self.play_note(freq, duration)
            time.sleep(duration)
            self.melody_index = (self.melody_index + 1) % len(self.tetris_melody)
            
    def check_collision(self, dx=0, dy=0, piece=None):
        """Check if piece collides"""
        if piece is None:
            piece = self.current_piece
            
        shape = piece['shape']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.piece_x + x + dx
                    new_y = self.piece_y + y + dy
                    
                    # Check boundaries
                    if new_x < 0 or new_x >= 9 or new_y >= 9:
                        return True
                        
                    # Check collision with placed pieces
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return True
                        
        return False
        
    def rotate_piece(self):
        """Rotate current piece 90 degrees"""
        if not self.current_piece:
            return
            
        # Simple rotation for small pieces
        shape = self.current_piece['shape']
        rows = len(shape)
        cols = len(shape[0]) if rows > 0 else 0
        
        # Create rotated shape
        rotated = [[0 for _ in range(rows)] for _ in range(cols)]
        for i in range(rows):
            for j in range(cols):
                rotated[j][rows-1-i] = shape[i][j]
                
        # Test if rotation is valid
        old_shape = self.current_piece['shape']
        self.current_piece['shape'] = rotated
        
        if self.check_collision():
            # Try wall kicks
            if not self.check_collision(dx=-1):
                self.piece_x -= 1
            elif not self.check_collision(dx=1):
                self.piece_x += 1
            else:
                # Can't rotate
                self.current_piece['shape'] = old_shape
                return
                
        # Play rotation sound
        self.play_note(523.25, 0.05)  # Quick C note
        
    def place_piece(self):
        """Place piece on grid"""
        shape = self.current_piece['shape']
        color = self.current_piece['color']
        
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = self.piece_x + x
                    grid_y = self.piece_y + y
                    if 0 <= grid_x < 9 and 0 <= grid_y < 9:
                        self.grid[grid_y][grid_x] = color
                        
        # Check for completed lines
        self.check_lines()
        
        # Spawn new piece
        self.spawn_piece()
        
    def check_lines(self):
        """Check and clear completed lines"""
        lines_to_clear = []
        
        for y in range(9):
            if all(self.grid[y][x] for x in range(9)):
                lines_to_clear.append(y)
                
        if lines_to_clear:
            # Play clearing sound
            for i, line in enumerate(lines_to_clear):
                freq = 523.25 * (1 + i * 0.25)  # Rising notes
                self.play_note(freq, 0.1)
                
            # Flash lines
            for _ in range(3):
                for y in lines_to_clear:
                    for x in range(9):
                        led = self.lp.panel.led(x, y)
                        led.color = (255, 255, 255)
                time.sleep(0.1)
                for y in lines_to_clear:
                    for x in range(9):
                        led = self.lp.panel.led(x, y)
                        led.color = self.grid[y][x]
                time.sleep(0.1)
                
            # Clear lines
            for y in sorted(lines_to_clear, reverse=True):
                del self.grid[y]
                self.grid.insert(0, [0 for _ in range(9)])
                
            self.lines_cleared += len(lines_to_clear)
            self.score += len(lines_to_clear) * 100
            
            # Speed up
            self.fall_speed = max(5, 20 - self.lines_cleared // 5)
            
    def handle_button_press(self, button):
        """Handle button input"""
        if not self.current_piece:
            return
            
        x = button.x
        
        if x < 3:
            # Left
            if not self.check_collision(dx=-1):
                self.piece_x -= 1
                self.play_note(200, 0.05)
        elif x > 5:
            # Right
            if not self.check_collision(dx=1):
                self.piece_x += 1
                self.play_note(250, 0.05)
        elif x == 4:
            # Rotate
            self.rotate_piece()
        else:
            # Drop
            while not self.check_collision(dy=1):
                self.piece_y += 1
                self.score += 1
            self.place_piece()
            self.play_note(100, 0.1)  # Thud
            
    def update_display(self):
        """Update the display"""
        while self.running:
            # Clear display
            self.clear_grid()
            
            # Draw placed pieces
            for y in range(9):
                for x in range(9):
                    if self.grid[y][x]:
                        led = self.lp.panel.led(x, y)
                        led.color = self.grid[y][x]
                        
            # Draw current piece
            if self.current_piece:
                shape = self.current_piece['shape']
                color = self.current_piece['color']
                
                for y, row in enumerate(shape):
                    for x, cell in enumerate(row):
                        if cell:
                            draw_x = self.piece_x + x
                            draw_y = self.piece_y + y
                            if 0 <= draw_x < 9 and 0 <= draw_y < 9:
                                led = self.lp.panel.led(draw_x, draw_y)
                                led.color = color
                                
            time.sleep(0.05)
            
    def game_loop(self):
        """Main game loop"""
        self.spawn_piece()
        
        while self.running:
            self.fall_timer += 1
            
            if self.fall_timer >= self.fall_speed:
                self.fall_timer = 0
                
                # Try to move piece down
                if not self.check_collision(dy=1):
                    self.piece_y += 1
                else:
                    # Place piece
                    self.place_piece()
                    
            time.sleep(0.05)
            
    def game_over(self):
        """Game over sequence"""
        self.running = False
        print(f"\nGame Over!")
        print(f"Score: {self.score}")
        print(f"Lines: {self.lines_cleared}")
        
        # Fill screen from bottom
        for y in range(8, -1, -1):
            for x in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (255, 0, 0)
            time.sleep(0.1)
            
    def event_loop(self):
        """Event handling"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start the game"""
        print("Starting Musical Tetris!")
        print("Controls:")
        print("  Left side (0-2): Move left")
        print("  Center (4): Rotate")
        print("  Right side (6-8): Move right")
        print("  Sides (3,5): Drop piece")
        print("Press Ctrl+C to exit.")
        
        # Start threads
        game_thread = threading.Thread(target=self.game_loop)
        game_thread.daemon = True
        game_thread.start()
        
        display_thread = threading.Thread(target=self.update_display)
        display_thread.daemon = True
        display_thread.start()
        
        music_thread = threading.Thread(target=self.play_tetris_theme)
        music_thread.daemon = True
        music_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nThanks for playing!")

if __name__ == "__main__":
    tetris = MusicalTetris()
    tetris.start()
