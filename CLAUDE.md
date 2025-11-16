# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BabySynth** (Synth.baby) is a Python-based baby synthesizer and soundboard that uses the **Launchpad Mini MK3** MIDI controller. It transforms the Launchpad's 8x8 grid of LED buttons into a customizable musical instrument where each button can:
1. Play a synthesized musical note (sine wave at specific frequency)
2. Play a pre-recorded .wav sound file

The project also includes 30+ interactive games and demos built on the same framework (Simon Says, Snake, Bubble Pop, Color Catch, etc.).

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main synthesizer
python main.py

# Run a demo/game
python demos/simon.py
```

## Project Structure

```
BabySynth/
├── main.py              # Entry point - initializes synth and event loop
├── synth.py             # LaunchpadSynth class - core controller
├── note.py              # Button, Note, and Chord classes
├── config.yaml          # Main configuration file
├── requirements.txt     # Python dependencies
├── sounds/              # WAV files for sound playback
├── configs/             # Additional YAML configurations
│   ├── baby_config.yaml
│   ├── drum_kit.yaml
│   ├── baby_grunge.yaml
│   └── ...
└── demos/               # Games and interactive demos
    ├── simon.py
    ├── snake.py
    ├── bubble.py
    └── ...
```

## Core Architecture

### 1. LaunchpadSynth (synth.py)
Main controller that:
- Loads YAML configuration
- Initializes Launchpad hardware connection
- Maps grid buttons to notes or sound files based on layout
- Handles button press/release events with optional debouncing
- Manages threading for non-blocking audio playback

**Key Methods:**
- `load_config()` - Parses YAML configuration
- `init_launchpad()` - Connects to Launchpad hardware
- `assign_notes_and_files()` - Maps buttons to notes/sounds
- `handle_event()` - Processes button press/release events
- `play_sound()` - Plays WAV files

### 2. Button, Note, and Chord Classes (note.py)
- **Button**: Represents a physical button with (x, y) position and color
- **Note**: Synthesized musical note with frequency, generates sine waves, handles play/stop with threading
- **Chord**: Collection of notes played simultaneously (currently defined but not heavily used)

### 3. Event Handling (main.py)
- ThreadPoolExecutor manages concurrent button event processing
- Main loop polls for button events and submits them to thread pool
- Small sleep (0.01s) prevents high CPU usage

### 4. Configuration System (config.yaml)
YAML-based configuration defines:
- **models**: ASCII grid layouts mapping characters to button positions
- **scales**: Musical scales (e.g., C_major: [C, D, E, F, G, A, B])
- **colors**: RGB colors for each note
- **file_char_and_locations**: Maps characters to .wav file paths
- **file_colors**: RGB colors for sound file buttons
- **debounce**: Boolean to enable/disable button debouncing

### Example Config Layout
```yaml
models:
  ADGC:
    layout: |
      xxxxxxxxx
      ABCDEFGAx
      BCDEFGABx
      ...
```
Each character represents which note/sound that button plays. The `x` character means no mapping (button inactive).

## Technical Details

### Audio Generation
- Notes are generated as sine waves using NumPy
- Formula: `amplitude * sin(2π * frequency * t)`
- 16-bit PCM audio at 44.1kHz sample rate
- Continuous playback via threading with stop flags

### Debouncing
- Configurable debounce window (default 5ms)
- Prevents multiple triggers from single button press
- Uses threading.Timer to batch events within window

### Thread Safety
- Lock-based synchronization for event handling
- ThreadPoolExecutor manages concurrent audio playback
- Each Note has its own playing_thread

## Dependencies

- **lpminimk3** (>=0.4.1) - Launchpad Mini MK3 Python library
- **simpleaudio** (>=1.0.4) - Cross-platform audio playback
- **numpy** (>=1.24.0) - Numerical operations for wave generation
- **pyyaml** (>=6.0) - YAML configuration parsing
- **mingus** (>=0.6.1) - Music theory utilities (currently minimal usage)

## Common Development Tasks

### Adding a New Note Layout
1. Edit `config.yaml` (or create new YAML in `configs/`)
2. Define a new model with ASCII grid layout
3. Map characters to notes in scales section
4. Optionally customize colors
5. Update `main.py` to use new model name in `synth.start()`

### Adding Sound Files
1. Place .wav files in `sounds/` directory
2. Add character mapping in `file_char_and_locations`
3. Set colors in `file_colors`
4. Use that character in a layout grid

### Creating a New Game/Demo
1. See examples in `demos/` directory
2. Import necessary classes from lpminimk3 and note.py
3. Initialize Launchpad connection
4. Implement game loop with button event handling
5. Use LED colors for visual feedback

### Debugging
- Logging is enabled by default (INFO level)
- Button presses/releases are logged with coordinates
- Grid state is logged after events in synth.py:167
- Check `self.get_ascii_grid()` for current button mapping

## Hardware Requirements

- **Launchpad Mini MK3** by Novation
- USB connection to computer
- The lpminimk3 library handles device detection automatically

## Known Patterns and Conventions

- **Button coordinates**: (x, y) where both range 0-8
- **Colors**: RGB tuples like (255, 0, 0) for red
- **Frequencies**: Standard note frequencies (A4 = 440Hz, C4 = 261.63Hz)
- **Threading**: Used extensively for non-blocking audio
- **Event-driven**: All interactions are button press/release events
- **Grid layout**: 9x9 grid where top row (y=0) is typically reserved for controls

## Potential Issues

- **No Launchpad detected**: Ensure device is connected and powered
- **Import errors**: Run `pip install -r requirements.txt`
- **Audio issues**: simpleaudio requires platform-specific dependencies (ALSA on Linux)
- **File not found**: Check relative paths for sound files in config.yaml
- **Multiple triggers**: Enable debouncing in config.yaml

## Code Quality Notes

- All core files now have proper docstrings
- Project is organized with demos/ and configs/ subdirectories
- requirements.txt provides clear dependency management
- Thread-safe operations use locks appropriately
- Debouncing is configurable for different use cases

## Additional Notes

- The project was developed iteratively (many demo variations exist)
- Some demos may reference sound files that don't exist
- The Chord class is defined but not extensively used in main synth
- Archive.zip contains old versions (can likely be removed)
- .DS_Store files indicate macOS development

## Future Enhancement Ideas

See the main README.md for detailed improvement suggestions.
