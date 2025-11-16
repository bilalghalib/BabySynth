import yaml
import time
import random
import threading
import numpy as np
import simpleaudio as sa
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import generate_sine_wave

class LightChaser:
    def __init__(self, config_file='config.yaml'):
        self.load_config(config_file)
        self.init_launchpad()
        self.running = True
        self.chase_speed = 0.3  # seconds between moves
        self.current_position = (0, 0)
        self.chase_path = self.generate_chase_path()
        self.path_index = 0
        self.melody_notes = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00]  # C, D, E, F, G, A
        self.melody_index = 0
        self.light_caught = False
        self.score = 0
        self.lock = threading.Lock()
        
        # Audio management
        self.audio_lock = threading.Lock()
        self.active_play_objs = []
        self.max_concurrent_sounds = 2
        
    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        self.colors = config['colors']
        
    def init_launchpad(self):
        self.lp = find_launchpads()[0]
        if self.lp is None:
            print("No Launchpad found. Exiting.")
            exit()
        self.lp.open()
        self.lp.mode = Mode.PROG
        self.clear_grid()
        print("Launchpad initialized for Light Chaser")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def generate_chase_path(self):
        """Generate a random path for the light to follow"""
        # Create a spiral pattern
        path = []
        size = 8
        x, y = size // 2, size // 2  # Start in middle
        
        # Spiral outward
        for layer in range(1, size // 2 + 1):
            # Move right
            for i in range(2 * layer):
                if 0 <= x < size and 0 <= y < size:
                    path.append((x, y))
                x += 1
            x -= 1
            y += 1
            
            # Move down
            for i in range(2 * layer):
                if 0 <= x < size and 0 <= y < size:
                    path.append((x, y))
                y += 1
            y -= 1
            x -= 1
            
            # Move left
            for i in range(2 * layer + 1):
                if 0 <= x < size and 0 <= y < size:
                    path.append((x, y))
                x -= 1
            x += 1
            y -= 1
            
            # Move up
            for i in range(2 * layer + 1):
                if 0 <= x < size and 0 <= y < size:
                    path.append((x, y))
                y -= 1
            y += 1
            x += 1
            
        # Filter out any coordinates outside the grid
        path = [(x, y) for x, y in path if 0 <= x < 9 and 0 <= y < 9]
        return path
    
    def play_audio(self, wave_obj):
        """Manage audio playback to avoid overlapping sounds"""
        with self.audio_lock:
            # Clean up finished sounds
            self.active_play_objs = [obj for obj in self.active_play_objs if obj.is_playing()]
            
            # If we have too many sounds playing, stop the oldest one
            while len(self.active_play_objs) >= self.max_concurrent_sounds:
                oldest = self.active_play_objs.pop(0)
                oldest.stop()
            
            # Play the new sound
            play_obj = sa.play_buffer(wave_obj, 1, 2, 44100)
            self.active_play_objs.append(play_obj)
            return play_obj
    
    def play_melody_note(self):
        """Play the next note in the melody"""
        frequency = self.melody_notes[self.melody_index]
        wave = generate_sine_wave(frequency, 0.15, amplitude=0.4)
        self.play_audio(wave)
        self.melody_index = (self.melody_index + 1) % len(self.melody_notes)
        
    def play_catch_sound(self):
        """Play a fun sound when the light is caught"""
        # Create a fun glissando up - but combine into one buffer for smoother playback
        duration = 0.4
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create frequency sweep
        freqs = np.linspace(440, 880, len(t))
        wave = np.sin(2 * np.pi * np.cumsum(freqs) / sample_rate)
        wave = (wave * 0.4 * 32767).astype(np.int16)
        
        self.play_audio(wave)
            
    def play_bonus_sound(self):
        """Play a bonus sound"""
        # Create a chord
        freqs = [261.63, 329.63, 392.00]  # C major chord
        duration = 0.2
        sample_rate = 44100
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = np.zeros_like(t)
        
        # Add each frequency component
        for freq in freqs:
            wave += 0.3 * np.sin(2 * np.pi * freq * t)
            
        # Apply envelope to avoid clicks
        envelope = np.ones_like(t)
        attack = int(0.02 * sample_rate)
        release = int(0.05 * sample_rate)
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[-release:] = np.linspace(1, 0, release)
        
        wave = wave * envelope
        wave = (wave / len(freqs) * 32767).astype(np.int16)
        
        self.play_audio(wave)
            
    def create_ripple(self, center_x, center_y):
        """Create a ripple effect from the pressed button"""
        colors = [
            (255, 0, 0),    # Red
            (255, 165, 0),  # Orange
            (255, 255, 0),  # Yellow
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (75, 0, 130),   # Indigo
            (238, 130, 238) # Violet
        ]
        
        # Store current grid state
        grid_state = {}
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                grid_state[(x, y)] = led.color
        
        # Function to set LEDs in a circle
        def set_circle(radius, color):
            for x in range(9):
                for y in range(9):
                    distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    if radius - 0.5 <= distance < radius + 0.5:
                        led = self.lp.panel.led(x, y)
                        led.color = color
        
        # Create expanding ripple
        for radius in range(1, 5):
            set_circle(radius, random.choice(colors))
            time.sleep(0.08)
            
        # Restore original grid state
        time.sleep(0.1)
        with self.lock:  # Use lock to avoid conflicts with light movement
            for (x, y), color in grid_state.items():
                led = self.lp.panel.led(x, y)
                led.color = color
                
    def handle_button_press(self, button):
        """Handle button press events"""
        x, y = button.x, button.y
        
        with self.lock:
            # Check if the light was caught
            if (x, y) == self.current_position:
                self.light_caught = True
                self.score += 1
                print(f"Light caught! Score: {self.score}")
                
                # Play sound in a separate thread to avoid blocking
                threading.Thread(target=self.play_catch_sound, daemon=True).start()
                
                # Speed up the chase
                self.chase_speed = max(0.12, self.chase_speed * 0.95)
                
                # Jump to a random position in the path
                self.path_index = random.randint(0, len(self.chase_path) - 1)
            else:
                # Create a ripple effect from the pressed button in a separate thread
                threading.Thread(target=self.create_ripple, args=(x, y), daemon=True).start()
                
                # Play a fun sound in a separate thread
                threading.Thread(target=self.play_bonus_sound, daemon=True).start()
                
    def move_light(self):
        """Move the light along the chase path"""
        last_note_time = 0
        min_note_interval = 0.1  # Minimum time between melody notes
        
        while self.running:
            with self.lock:
                # Clear previous position
                if not self.light_caught:
                    old_x, old_y = self.current_position
                    old_led = self.lp.panel.led(old_x, old_y)
                    old_led.color = (0, 0, 0)
                
                # Get new position
                self.path_index = (self.path_index + 1) % len(self.chase_path)
                self.current_position = self.chase_path[self.path_index]
                x, y = self.current_position
                
                # Set new LED
                led = self.lp.panel.led(x, y)
                
                # Choose a color based on position
                color_key = list(self.colors.keys())[self.path_index % len(self.colors)]
                led.color = self.colors[color_key]
                
                # Play a note if enough time has passed
                current_time = time.time()
                if current_time - last_note_time >= min_note_interval:
                    threading.Thread(target=self.play_melody_note, daemon=True).start()
                    last_note_time = current_time
                
                # Reset caught flag
                self.light_caught = False
                
            # Wait before next move
            time.sleep(self.chase_speed)
    
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                # Create a new thread for handling button press
                t = threading.Thread(target=self.handle_button_press, args=(button_event.button,), daemon=True)
                t.start()
            time.sleep(0.01)
    
    def start(self):
        """Start the light chaser game"""
        print("Starting Light Chaser! Press buttons to catch the moving light.")
        print("Press Ctrl+C to exit.")
        
        # Start light movement thread
        light_thread = threading.Thread(target=self.move_light, daemon=True)
        light_thread.start()
        
        # Start event loop
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            print("\nLight Chaser stopped.")
        finally:
            # Clean up by stopping all sounds and clearing the grid
            with self.audio_lock:
                for obj in self.active_play_objs:
                    if obj.is_playing():
                        obj.stop()
            self.clear_grid()

if __name__ == "__main__":
    chaser = LightChaser()
    chaser.start()