# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BabySynth (Synth.baby) is a baby synthesizer and soundboard built with Python. It uses the Launchpad Mini MK3 MIDI controller to create a customizable synthesizer and sound player where each button on the Launchpad can either:
1. Play a musical note (with customizable frequency)
2. Play a .wav sound file

## Setup and Dependencies

This project requires the following Python packages:
- lpminimk3 - for Launchpad Mini MK3 integration
- simpleaudio - for audio playback
- numpy - for generating sine waves
- pyyaml - for reading configuration
- mingus - for music theory functionality
- concurrent.futures - for threading support

To run the project:
```bash
python main.py
```

## Project Structure

- **main.py** - Entry point that initializes the LaunchpadSynth and handles events
- **synth.py** - Contains the LaunchpadSynth class, which manages the Launchpad interface, note mapping, and sound playback
- **note.py** - Defines Button, Note, and Chord classes for synthesizer functionality
- **config.yaml** - Configuration file that defines:
  - Models/layouts for button mapping
  - Scales for musical notes
  - Colors for visual feedback
  - File locations for sound playback
  - Debounce settings

## Core Architecture

1. **LaunchpadSynth** is the main controller that:
   - Loads configuration from YAML
   - Initializes the Launchpad controller
   - Maps buttons to notes or sound files based on the layout
   - Handles button press/release events

2. **Button Events**:
   - Button presses trigger either note playing or sound file playback
   - Button releases stop note playing
   - Debounce mechanism prevents multiple triggers from a single press

3. **Synthesizer Implementation**:
   - Notes are generated as sine waves with specific frequencies
   - Sound files are loaded and played using simpleaudio
   - Threading is used to ensure continuous playback without blocking

4. **Configuration System**:
   - Layouts define the arrangement of notes/sounds on the Launchpad grid
   - Multiple models can be defined in the config (FILES, ADGC, etc.)
   - Colors provide visual feedback for different notes

## Customization

The system is highly customizable through the config.yaml file:
- Define new layouts using ASCII grids
- Map different characters to different notes or sound files
- Customize colors for visual feedback
- Enable/disable debounce for button presses