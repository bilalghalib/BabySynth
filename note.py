#note_m.py
from mingus.containers import Note as MingusNote, NoteContainer
import numpy as np
import simpleaudio as sa
import threading

def generate_sine_wave(frequency, duration, sample_rate=44100, amplitude=0.5):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = amplitude * np.sin(2 * np.pi * frequency * t)
    wave = (wave * 32767).astype(np.int16)
    return wave

def play_wave(wave):
    play_obj = sa.play_buffer(wave, 1, 2, 44100)
    return play_obj

class Button:
    def __init__(self, x, y, color=(0, 0, 0)):
        self.x = x
        self.y = y
        self.color = color

    def set_color(self, color):
        self.color = color

    def get_position(self):
        return (self.x, self.y)

class Note:
    def __init__(self, name, frequency, buttons, color, lp):
        self.name = name
        self.frequency = frequency
        self.buttons = buttons
        self.color = color
        self.lp = lp
        self.playing_thread = None
        self.stop_flag = threading.Event()
        self.play_obj = None

    def play(self):
        if not self.playing_thread or not self.playing_thread.is_alive():
            self.stop_flag.clear()
            self.playing_thread = threading.Thread(target=self.play_note)
            self.playing_thread.start()
        self.light_up_buttons((255, 255, 255))

    def play_note(self):
        wave = generate_sine_wave(self.frequency, 1)  # 1-second buffer to keep the note playing
        while not self.stop_flag.is_set():
            if not self.play_obj or not self.play_obj.is_playing():
                self.play_obj = play_wave(wave)
            self.stop_flag.wait(0.1)  # Check the flag every 0.1 seconds

    def stop(self):
        self.stop_flag.set()
        if self.playing_thread and self.playing_thread.is_alive():
            self.playing_thread.join()
        if self.play_obj:
            self.play_obj.stop()
        self.light_up_buttons(self.color)

    def light_up_buttons(self, color):
        for button in self.buttons:
            led = self.lp.panel.led(button.x, button.y)
            led.color = color

class Chord:
    def __init__(self, notes):
        self.notes = notes
        self.playing_thread = None
        self.stop_flag = threading.Event()
        self.play_objs = []

    def play(self):
        if not self.playing_thread or not self.playing_thread.is_alive():
            self.stop_flag.clear()
            self.playing_thread = threading.Thread(target=self.play_chord)
            self.playing_thread.start()
        for note in self.notes:
            note.light_up_buttons((255, 255, 255))

    def play_chord(self):
        waves = [generate_sine_wave(note.frequency, 1) for note in self.notes]  # 1-second buffer
        while not self.stop_flag.is_set():
            if not self.play_objs or not any(play_obj.is_playing() for play_obj in self.play_objs):
                self.play_objs = [play_wave(wave) for wave in waves]
            self.stop_flag.wait(0.1)  # Check the flag every 0.1 seconds
        for play_obj in self.play_objs:
            play_obj.stop()

    def stop(self):
        self.stop_flag.set()
        if self.playing_thread and self.playing_thread.is_alive():
            self.playing_thread.join()
        for note in self.notes:
            note.light_up_buttons(note.color)
