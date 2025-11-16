import yaml
import time
import random
import threading
import numpy as np
import simpleaudio as sa
import os
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import generate_sine_wave, play_wave

class SimonSaysBaby:
    def __init__(self, config_file='config.yaml'):
        self.load_config(config_file)
        self.init_launchpad()
        self.running = True
        
        # Game state
        self.pattern = []
        self.player_position = 0
        self.showing_pattern = False
        self.level = 1
        self.max_buttons = 4  # Only use 4 buttons for baby
        
        # Button positions (2x2 in center of grid)
        self.button_positions = [
            (3, 3),  # Top-left (Red)
            (5, 3),  # Top-right (Yellow)
            (3, 5),  # Bottom-left (Green)
            (5, 5),  # Bottom-right (Blue)
        ]
        
        self.button_colors = [
            (255, 0, 0),    # Red
            (255, 255, 0),  # Yellow
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
        ]
        
        # Animal sounds (you'll need to add these wav files)
        self.animal_sounds = [
            "./sounds/cow.wav",      # Red button
            "./sounds/duck.wav",     # Yellow button
            "./sounds/cat.wav",      # Green button
            "./sounds/dog.wav",      # Blue button
        ]
        
        # Use musical notes as fallback if wav files don't exist
        self.musical_notes = [
            261.63,  # C (Do)
            329.63,  # E (Mi)
            392.00,  # G (Sol)
            523.25,  # C (Do - higher)
        ]
        
        self.success_sounds = [
            "./sounds/yay.wav",
            "./sounds/giggle.wav",
            "./sounds/applause.wav"
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
        self.setup_buttons()
        print("Simon Says Baby initialized!")
        
    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                
    def setup_buttons(self):
        """Set up the 4 game buttons with dim colors"""
        for i, (x, y) in enumerate(self.button_positions):
            led = self.lp.panel.led(x, y)
            # Dim version of the color
            dim_color = tuple(int(c * 0.2) for c in self.button_colors[i])
            led.color = dim_color
            
    def play_button_sound(self, button_index):
        """Play animal sound or musical note for button"""
        # Try to play animal sound first
        if button_index < len(self.animal_sounds):
            sound_file = self.animal_sounds[button_index]
            if os.path.exists(sound_file):
                try:
                    wave_obj = sa.WaveObject.from_wave_file(sound_file)
                    play_obj = wave_obj.play()
                    return
                except:
                    pass
        
        # Fallback to musical note
        if button_index < len(self.musical_notes):
            frequency = self.musical_notes[button_index]
            # Create a pleasant bell-like tone
            duration = 0.5
            t = np.linspace(0, duration, int(44100 * duration), False)
            wave = np.sin(2 * np.pi * frequency * t)
            envelope = np.exp(-2 * t)
            wave = wave * envelope
            wave = (wave * 32767).astype(np.int16)
            play_wave(wave)
            
    def play_success_sound(self):
        """Play a success sound"""
        # Try success sounds
        for sound_file in self.success_sounds:
            if os.path.exists(sound_file):
                try:
                    wave_obj = sa.WaveObject.from_wave_file(sound_file)
                    play_obj = wave_obj.play()
                    return
                except:
                    pass
        
        # Fallback to happy chord
        frequencies = [261.63, 329.63, 392.00, 523.25]  # C major chord
        waves = []
        for freq in frequencies:
            t = np.linspace(0, 0.5, int(44100 * 0.5), False)
            wave = np.sin(2 * np.pi * freq * t) * 0.25
            waves.append(wave)
        combined = np.sum(waves, axis=0)
        combined = (combined * 32767).astype(np.int16)
        play_wave(combined)
        
    def light_button(self, button_index, bright=True):
        """Light up a button"""
        if button_index < len(self.button_positions):
            x, y = self.button_positions[button_index]
            led = self.lp.panel.led(x, y)
            if bright:
                led.color = self.button_colors[button_index]
            else:
                # Dim version
                dim_color = tuple(int(c * 0.2) for c in self.button_colors[button_index])
                led.color = dim_color
                
    def show_pattern(self):
        """Show the current pattern to the player"""
        self.showing_pattern = True
        time.sleep(0.5)  # Pause before starting
        
        for button_index in self.pattern:
            # Light up button
            self.light_button(button_index, bright=True)
            self.play_button_sound(button_index)
            
            time.sleep(0.6)  # Show for 600ms
            
            # Dim button
            self.light_button(button_index, bright=False)
            time.sleep(0.2)  # Gap between buttons
            
        self.showing_pattern = False
        self.player_position = 0
        
    def add_to_pattern(self):
        """Add a new random button to the pattern"""
        # For baby mode, keep patterns short
        if len(self.pattern) < 5:  # Max pattern length of 5
            new_button = random.randint(0, self.max_buttons - 1)
            self.pattern.append(new_button)
        else:
            # Reset with new pattern
            self.pattern = [random.randint(0, self.max_buttons - 1)]
            
    def handle_button_press(self, button):
        """Handle button press"""
        if self.showing_pattern:
            return  # Ignore presses during pattern display
            
        x, y = button.x, button.y
        
        # Check which game button was pressed
        button_index = None
        for i, (bx, by) in enumerate(self.button_positions):
            if x == bx and y == by:
                button_index = i
                break
                
        if button_index is not None:
            # Light up and play sound
            self.light_button(button_index, bright=True)
            self.play_button_sound(button_index)
            
            # Check if correct
            if button_index == self.pattern[self.player_position]:
                self.player_position += 1
                
                # Completed pattern!
                if self.player_position >= len(self.pattern):
                    time.sleep(0.3)
                    self.success_animation()
                    self.play_success_sound()
                    
                    # Add to pattern and show new sequence
                    self.add_to_pattern()
                    time.sleep(1.0)
                    self.setup_buttons()  # Reset button colors
                    threading.Thread(target=self.show_pattern).start()
            else:
                # Wrong button - be gentle with baby!
                time.sleep(0.5)
                # Just replay the pattern (no harsh failure)
                self.gentle_retry()
                
            # Dim button after press
            threading.Timer(0.3, lambda: self.light_button(button_index, bright=False)).start()
            
    def gentle_retry(self):
        """Gentle retry - just show pattern again"""
        # Flash all buttons gently
        for _ in range(2):
            for i in range(self.max_buttons):
                self.light_button(i, bright=True)
            time.sleep(0.2)
            for i in range(self.max_buttons):
                self.light_button(i, bright=False)
            time.sleep(0.2)
            
        # Show pattern again
        time.sleep(0.5)
        threading.Thread(target=self.show_pattern).start()
        
    def success_animation(self):
        """Fun success animation"""
        # Rainbow spiral
        colors = [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (148, 0, 211)
        ]
        
        # Light up buttons in sequence multiple times
        for _ in range(3):
            for i in range(self.max_buttons):
                self.light_button(i, bright=True)
                time.sleep(0.1)
            for i in range(self.max_buttons):
                self.light_button(i, bright=False)
                time.sleep(0.1)
                
    def event_loop(self):
        """Listen for button events"""
        while self.running:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event and button_event.type == ButtonEvent.PRESS:
                self.handle_button_press(button_event.button)
            time.sleep(0.01)
            
    def start(self):
        """Start Simon Says Baby"""
        print("Starting Simon Says Baby!")
        print("Watch the pattern and repeat it!")
        print("Using 4 buttons in the center of the pad")
        print("Press Ctrl+C to exit.")
        
        # Start with a single button pattern
        self.add_to_pattern()
        
        # Show first pattern after a delay
        threading.Timer(1.0, self.show_pattern).start()
        
        try:
            self.event_loop()
        except KeyboardInterrupt:
            self.running = False
            self.clear_grid()
            print("\nSimon Says Baby stopped.")

if __name__ == "__main__":
    simon = SimonSaysBaby()
    simon.start()
