import yaml
import logging
from lpminimk3 import ButtonEvent, Mode, find_launchpads
from note import Note, Button
import threading

class LaunchpadSynth:
    def __init__(self, config_file):
        self.load_config(config_file)
        self.init_launchpad()
        self.notes = {}
        self.button_events = []
        self.DEBOUNCE_WINDOW = 0.01  # Debounce window in seconds
        self.debounce_timer = None
        self.lock = threading.Lock()  # Lock for thread-safe operations

    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        self.scales = config['scales']
        self.colors = config['colors']

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
        for x in range(8):
            for y in range(8):
                led = self.lp.panel.led(x, y)
                led.color = (0, 0, 0)

    def partition_grid(self, partition_type):
        partitions = []
        if partition_type == 'full':
            partitions.append([(x, y + 1) for y in range(7) for x in range(8)])
        elif partition_type == 'half':
            partitions = [
                [(x, y + 1) for x in range(8) for y in range(3)],
                [(x, y + 1) for x in range(8) for y in range(3, 7)]
            ]
        elif partition_type == 'quarter':
            partitions = [
                [(x, y + 1) for x in range(4) for y in range(3)],
                [(x, y + 1) for x in range(4, 8) for y in range(3)],
                [(x, y + 1) for x in range(4) for y in range(3, 7)],
                [(x, y + 1) for x in range(4, 8) for y in range(3, 7)]
            ]
        elif partition_type == 'eighth':
            partitions = [
                [(x, y + 1) for x in range(4) for y in range(1)],
                [(x, y + 1) for x in range(4) for y in range(1, 3)],
                [(x, y + 1) for x in range(4) for y in range(3, 5)],
                [(x, y + 1) for x in range(4) for y in range(5, 7)],
                [(x, y + 1) for x in range(4, 8) for y in range(1)],
                [(x, y + 1) for x in range(4, 8) for y in range(1, 3)],
                [(x, y + 1) for x in range(4, 8) for y in range(3, 5)],
                [(x, y + 1) for x in range(4, 8) for y in range(5, 7)]
            ]
        return partitions

    def assign_notes(self, scale, partition_type):
        partitions = self.partition_grid(partition_type)
        notes = self.scales[scale]
        self.notes = {}

        for note_name, grid_section in zip(notes, partitions):
            frequency = self.get_frequency_for_note(note_name)
            buttons = [Button(x, y) for x, y in grid_section if y < 8]  # Ensure buttons stay within the grid
            color = self.colors[note_name]
            note = Note(note_name, frequency, buttons, color, self.lp)
            self.notes[note_name] = note
        self.initialize_grid()
        logging.info(f"Grid partitioned: \n{self.get_ascii_grid()}")

    def initialize_grid(self):
        for note in self.notes.values():
            note.light_up_buttons(note.color)

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
        grid = [['.' for _ in range(8)] for _ in range(8)]
        for note_name, note in self.notes.items():
            for button in note.buttons:
                x, y = button.get_position()
                grid[y][x] = note_name.lower()
        return '\n'.join([''.join(row) for row in grid])

    def start(self, scale, partition_type):
        self.assign_notes(scale, partition_type)
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
        if not self.debounce_timer:
            self.debounce_timer = threading.Timer(self.DEBOUNCE_WINDOW, self.process_button_events)
            self.debounce_timer.start()

    def process_button_events(self):
        with self.lock:
            if not self.button_events:
                return

            notes_to_play = []
            for button in self.button_events:
                x, y = button.x, button.y
                logging.info(f"Processing button event at {x}, {y}")
                for note in self.notes.values():
                    for btn in note.buttons:
                        if (x, y) == btn.get_position():
                            notes_to_play.append(note)
                            logging.info(f"Found note {note.name} for button at {x}, {y}")
                            break

            for note in notes_to_play:
                note.play()
                logging.info(f"Playing note: {note.name}")

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
