import yaml
import time
import random
import threading
import numpy as np
import simpleaudio as sa
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import generate_sine_wave, play_wave

class DanceParty:
    def __init__(self, config_file='config.yaml'):
        self.load_config(config_file)
        self.init_launchpad()
        self.running = True
        self.tempo = 120  # BPM
        self.beat_interval = 60.0 / self.tempo
        self.current_pattern = 0
        self.user_presses = []  # Store recent presses for interaction
        self.lock = threading.Lock()
        
        # Dance patterns
        self.patterns = [
            self.pattern_checkerboard,
            self.pattern_wave,
            self.pattern_spiral,
            self.pattern_pulse,
        ]
        
        # Disco colors
        self.disco_colors = [
            (255, 0, 0),     # Red
            (255, 127, 0),   # Orange  
            (255, 255, 0),   # Yellow
            (0, 255, 0),     # Green
            (0, 0, 255),     # Blue
            (255, 0, 255),   # Magenta
            (0, 255, 255),   # Cyan
        ]
        
        # Simple drum sounds (synthesized)
        self.beat_count = 0
        
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
        print("Dance Party initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def play_drum_sound(self):
        """Play a simple drum beat"""
        duration = 0.1
        t = np.linspace(0, duration, int(44100 * duration), False)
        
        if self.beat_count % 4 == 0:
            # Kick drum on beat 1
            freq = 60
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-35 * t)
        elif self.beat_count % 4 == 2:
            # Snare on beat 3
            noise = np.random.normal(0, 0.3, len(t))
            tone = np.sin(2 * np.pi * 200 * t)
            wave = 0.7 * noise + 0.3 * tone
            envelope = np.exp(-25 * t)
        else:
            # Hi-hat on off beats
            noise = np.random.normal(0, 0.2, len(t))
            wave = noise
            envelope = np.exp(-50 * t)
            
        wave = wave * envelope
        wave = (wave * 32767 * 0.3).astype(np.int16)
        threading.Thread(target=play_wave, args=(wave,)).start()
        
    def pattern_checkerboard(self):
        """Alternating checkerboard pattern"""
        offset = self.beat_count % 2
        for x in range(9):
            for y in range(9):
                if (x + y + offset) % 2 == 0:
                    led = self.lp.panel.led(x, y)
                    color = self.disco_colors[self.beat_count % len(self.disco_colors)]
                    led.color = color
                else:
                    led = self.lp.panel.led(x, y)
                    led.color = (0, 0, 0)
                    
    def pattern_wave(self):
        """Wave pattern across the grid"""
        wave_pos = self.beat_count % 18
        for x in range(9):
            for y in range(9):
                distance = abs(x + y - wave_pos)
                if distance < 3:
                    brightness = 1.0 - distance * 0.3
                    color = self.disco_colors[(self.beat_count + x) % len(self.disco_colors)]
                    led = self.lp.panel.led(x, y)
                    led.color = tuple(int(c * brightness) for c in color)
                else:
                    led = self.lp.panel.led(x, y)
                    led.color = (0, 0, 0)
                    
    def pattern_spiral(self):
        """Spiral pattern from center"""
        center_x, center_y = 4, 4
        angle_offset = self.beat_count * 0.5
        
        for x in range(9):
            for y in range(9):
                dx = x - center_x
                dy = y - center_y
                distance = (dx**2 + dy**2)**0.5
                angle = np.arctan2(dy, dx)
                
                # Create spiral arms
                spiral_value = (angle + angle_offset + distance * 0.5) % (2 * np.pi)
                if spiral_value < np.pi / 2:
                    brightness = 1.0 - distance * 0.1
                    color_index = int(distance) % len(self.disco_colors)
                    color = self.disco_colors[color_index]
                    led = self.lp.panel.led(x, y)
                    led.color = tuple(int(c * brightness) for c in color)
                else:
                    led = self.lp.panel.led(x, y)
                    led.color = (0, 0, 0)
                    
    def pattern_pulse(self):
        """Pulsing circles from recent button presses"""
        # Add center if no recent presses
        if not self.user_presses:
            self.user_presses.append((4, 4, 0))
            
        with self.lock:
            # Age and clean old presses
            self.user_presses = [(x, y, age + 1) for x, y, age in self.user_presses if age < 10]
            
            # Clear grid first
            self.clear_grid()
            
            # Draw pulses from each press point
            for press_x, press_y, age in self.user_presses:
                radius = age * 0.5
                color = self.disco_colors[age % len(self.disco_colors)]
                brightness = max(0, 1.0 - age * 0.1)
                
                for x in range(9):
                    for y in range(9):
                        distance = ((x - press_x)**2 + (y - press_y)**2)**0.5
                        if abs(distance - radius) < 1.0:
                            led = self.lp.panel.led(x, y)
                            led.color = tuple(int(c * brightness) for c in color)
                            
    def handle_button_press(self, button):
        """Handle button press - adds to pulse pattern and changes tempo"""
        x, y = button.x, button.y
        
        with self.lock:
            # Add to user presses for pulse pattern
            self.user_presses.append((x, y, 0))
            
        # Play a fun note
        note_freqs = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
        freq = note_freqs[(x + y) % len(note_freqs)]
        
        t = np.linspace(0, 0.2, int(44100 * 0.2), False)
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-5 * t)
        wave = wave * envelope * 0.5
        wave = (wave * 32767).astype(np.int16)
        threading.Thread(target=play_wave, args=(wave,)).start()
        
        # Change pattern on press
        self.current_pattern = (self.current_pattern + 1) % len(self.patterns)
        
        # Flash effect
        for i in range(3):
            led = self.lp.panel.led(x, y)
            led.color = (255, 255, 255)
            time.sleep(0.05)
            led.color = (0, 0, 0)
            time.sleep(0.05)
            
    def beat_loop(self):
        """Main beat loop"""
        while self.running:
            # Play drum sound
            self.play_drum_sound()
            
            # Update pattern
            self.patterns[self.current_pattern]()
            
            # Increment beat
            self.beat_count += 1
            
            # Wait for next beat
            time.sleep(self.beat_interval)
            
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                threading.Thread(
                    target=self.handle_button_press,
                    args=(button_event.button,)
                ).start()
            time.sleep(0.01)
            
    def start(self):
        """Start Dance Party"""
        print("Starting Dance Party!")
        print("Press buttons to change patterns and add effects!")
        print("Press Ctrl+C to exit.")
        
        # Start beat loop
        beat_thread = threading.Thread(target=self.beat_loop)
        beat_thread.daemon = True
        beat_thread.start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nDance Party stopped.")

if __name__ == "__main__":
    party = DanceParty()
    party.start()
