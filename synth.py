"""
BabySynth - LaunchpadSynth Controller
Main controller that manages the Launchpad interface, note mapping, and sound playback.
"""
import yaml
import logging
import threading
import simpleaudio as sa
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import Note, Button, Chord

class LaunchpadSynth:
    def __init__(self, config_file, web_broadcaster=None):
        self.load_config(config_file)
        self.init_launchpad()
        self.notes = {}
        self.audio_files = {}
        self.active_chords = []
        self.button_events = []
        self.current_audio_play_obj = None  # To keep track of the current playing WAV file
        self.DEBOUNCE_WINDOW = 0.005  # Reduced debounce window
        self.debounce_timer = None
        self.lock = threading.Lock()  # Lock for thread-safe operations
        self.web_broadcaster = web_broadcaster  # Optional web UI broadcaster

    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        self.model_name = config['name']
        self.models = config['models']
        self.scales = config['scales']
        self.colors = config['colors']
        self.file_char_and_locations = config.get('file_char_and_locations', {})
        self.file_colors = config.get('file_colors', {})
        self.debounce = config.get('debounce', True)  # Read debounce setting, default to True if not specified
        self.DEBOUNCE_WINDOW = 0.005 if self.debounce else 0  # Set debounce window based on setting

    def init_launchpad(self):
        self.lp = find_launchpads()[0]
        if self.lp is None:
            print("No Launchpad found. Exiting.")
            exit()
        self.lp.open()
        self.lp.mode = Mode.PROG
        self.clear_grid()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def clear_grid(self):
        for x in range(9):
            for y in range(9):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)
                if self.web_broadcaster:
                    self.web_broadcaster.update_led(x, y, (0, 0, 0))

    def assign_notes_and_files(self, scale, model_name):
        layout = self.models[model_name]['layout'].strip().split('\n')
        scale_notes = self.scales[scale]

        # Create mappings for notes and audio files
        unique_chars = sorted(set(''.join(layout)))
        note_mapping = {char: scale_notes[i % len(scale_notes)] for i, char in enumerate(unique_chars) if char in scale_notes}
        file_mapping = {char: self.file_char_and_locations[char] for char in unique_chars if char in self.file_char_and_locations}

        self.notes = {}
        self.audio_files = {}

        for y, row in enumerate(layout):
            for x, char in enumerate(row):
                if char == '.':
                    continue
                button = Button(x, y)
                if char in note_mapping:
                    note_name = note_mapping[char]
                    frequency = self.get_frequency_for_note(note_name)
                    color = self.colors[note_name]
                    if note_name not in self.notes:
                        self.notes[note_name] = Note(note_name, frequency, [button], color, self.lp, self.web_broadcaster)
                    else:
                        self.notes[note_name].buttons.append(button)
                elif char in file_mapping:
                    file_path = file_mapping[char]
                    color = self.file_colors.get(char, [255, 255, 255])  # Default to white if no color specified
                    if char not in self.audio_files:
                        self.audio_files[char] = {"file": file_path, "buttons": [button], "color": color}
                    else:
                        self.audio_files[char]["buttons"].append(button)

        self.initialize_grid()
        logging.info(f"Grid partitioned: \n{self.get_ascii_grid()}")

    def initialize_grid(self):
        for note in self.notes.values():
            note.light_up_buttons(note.color)
            # Broadcast to web UI
            if self.web_broadcaster:
                for button in note.buttons:
                    self.web_broadcaster.update_led(button.x, button.y, note.color)
        for char, audio in self.audio_files.items():
            for button in audio["buttons"]:
                led = self.lp.panel.led(button.x, button.y)
                led.color = audio["color"]  # Set the color for audio file buttons
                # Broadcast to web UI
                if self.web_broadcaster:
                    self.web_broadcaster.update_led(button.x, button.y, audio["color"])

    def get_frequency_for_note(self, note):
        note_frequencies = {
            'C': 261.63,
            'D': 293.66,
            'E': 329.63,
            'F': 349.23,
            'G': 392.00,
            'A': 440.00,
            'B': 493.88
        }
        return note_frequencies[note]

    def get_ascii_grid(self):
        grid = [['.' for _ in range(9)] for _ in range(9)]
        for note_name, note in self.notes.items():
            for button in note.buttons:
                x, y = button.get_position()
                grid[y][x] = note_name.lower()
        for char, audio in self.audio_files.items():
            for button in audio["buttons"]:
                x, y = button.get_position()
                grid[y][x] = char.lower()
        return '\n'.join([''.join(row) for row in grid])

    def start(self, scale, model_name):
        self.assign_notes_and_files(scale, model_name)
        print("Listening for button presses. Press Ctrl+C to exit.")
        event_thread = threading.Thread(target=self.event_loop)
        event_thread.start()

    def event_loop(self):
        while True:
            button_event = self.lp.panel.buttons().poll_for_event()
            if button_event:
                with self.lock:
                    self.handle_event(button_event)

    def handle_event(self, button_event):
        if button_event.type == ButtonEvent.PRESS:
            self.handle_button_press(button_event.button)
        elif button_event.type == ButtonEvent.RELEASE:
            self.handle_button_release(button_event.button)

    def handle_button_press(self, button):
        logging.info(f"Button press detected at {button.x}, {button.y}")
        self.button_events.append(button)
        if self.debounce:
            if not self.debounce_timer:
                self.debounce_timer = threading.Timer(self.DEBOUNCE_WINDOW, self.process_button_events)
                self.debounce_timer.start()
        else:
            self.process_button_events()

    def process_button_events(self):
        with self.lock:
            if not self.button_events:
                return

            for button in self.button_events:
                x, y = button.x, button.y
                logging.info(f"Processing button event at {x}, {y}")

                for note in self.notes.values():
                    for btn in note.buttons:
                        if (x, y) == btn.get_position():
                            note.play()
                            break

                for char, audio in self.audio_files.items():
                    for btn in audio["buttons"]:
                        if (x, y) == btn.get_position():
                            self.play_sound(audio["file"])
                            break

            logging.info(f"Current grid: \n{self.get_ascii_grid()}")
            self.button_events.clear()
            self.debounce_timer = None

    def handle_button_release(self, button):
        x, y = button.x, button.y
        logging.info(f"Button release detected at {x}, {y}")
        for note in self.notes.values():
            for btn in note.buttons:
                if (x, y) == btn.get_position():
                    note.stop()
                    logging.info(f"Stopping note: {note.name}")
                    break

    def play_sound(self, sound_file):
        # Stop the current audio if playing
        if self.current_audio_play_obj and self.current_audio_play_obj.is_playing():
            self.current_audio_play_obj.stop()
        
        wave_obj = sa.WaveObject.from_wave_file(sound_file)
        self.current_audio_play_obj = wave_obj.play()
