# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BabySynth** (Synth.baby) is a Python-based baby synthesizer and interactive soundboard built for the **Launchpad Mini MK3** MIDI controller. It transforms the controller's 8x8 grid into:
1. A customizable musical instrument (synthesized notes via sine waves)
2. A soundboard (pre-recorded .wav files)
3. A game platform (30+ interactive demos: Simon Says, Snake, Bubble Pop, etc.)
4. A web-monitored device with real-time LED visualization

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main synthesizer
python main.py

# Run with web UI monitoring (http://localhost:5001)
python main_web.py

# Run a demo/game
python demos/simon.py

# Run plugin-based games
python game_plugin.py
```

## Entry Points

- **`main.py`** - Standard synthesizer mode (console only)
- **`main_web.py`** - Synthesizer with web UI on http://localhost:5001
- **`game_plugin.py`** - Plugin-based game launcher (auto-discovers games in `plugins/`)
- **`demos/*.py`** - Standalone game scripts (30+ files)

## Core Architecture

### Event Processing Pipeline

```
Hardware Button Press
  → Logged with (x, y) coordinates
  → Added to button_events queue
  → [Optional] Batched by debounce timer (5ms window)
  → process_button_events() executes
  → Note.play() or play_sound() called
  → LED color updated on hardware
  → Broadcasted to web UI (if enabled)
```

### Threading Model

The project uses extensive threading for non-blocking operations:

1. **Main Thread**: Polls Launchpad hardware for button events (blocking API)
2. **ThreadPoolExecutor** (10 workers): Processes button events concurrently
3. **Note Playback Threads**: Each Note instance has independent `playing_thread` for continuous sine wave generation
4. **Debounce Timer**: `threading.Timer` batches events within 5ms window to prevent double-triggers
5. **ConfigManager Watch Thread**: File monitoring for hot-reload (if using config_manager.py)
6. **Web Server Thread**: Flask-SocketIO runs on separate thread (in main_web.py)

**Synchronization**: Lock-based for shared state, Event flags for Note stop signals.

### Key Classes

**LaunchpadSynth (synth.py)** - Core controller bridging hardware, config, and audio
- `load_config()` - Parses YAML, supports models/scales/colors/file mappings
- `assign_notes_and_files()` - Maps ASCII grid characters to Note objects or .wav files
- `handle_event()` - Routes PRESS/RELEASE events to appropriate handlers
- `get_frequency_for_note()` - Converts note names to Hz (A4=440Hz standard)
- Optional `web_broadcaster` parameter for LED visualization

**Note (note.py)** - Synthesized musical tone
- `play()` - Spawns thread, sets buttons white, starts continuous playback
- `play_note()` - Loop generating 1-second sine wave buffers (16-bit PCM, 44.1kHz)
- `stop()` - Sets stop flag, joins thread, restores button colors
- Thread-safe with stop_flag (threading.Event)

**Button (note.py)** - Simple (x, y) position + color storage

**Chord (note.py)** - Multiple simultaneous notes (defined but minimally used)

**WebUIBroadcaster (web_ui.py)** - Singleton for real-time LED sync
- `update_led(x, y, color)` - Emits SocketIO event to all web clients
- `update_grid(grid_data)` - Bulk grid updates
- Flask routes: `/` (live view), `/editor` (audio editor), `/config` (visual config editor)

### Configuration System

**Basic Structure (config.yaml)**:
```yaml
models:
  LAYOUT_NAME:
    layout: |          # 9x9 ASCII grid
      xxxxxxxxx         # 'x' = inactive button
      ABCDEFGAx        # Each char = note or sound
      ...

scales:
  C_major: [C, D, E, F, G, A, B]

colors:
  C: [255, 0, 0]      # RGB tuples

file_char_and_locations:
  Z: "./sounds/file.wav"

file_colors:
  Z: [128, 0, 0]

debounce: true        # 5ms batching window
```

**Advanced Features** (see configs/ directory):
- Themes, animations (frame-based LED patterns)
- Chord progressions, macros
- ADSR envelopes (drum_kit.yaml example)

**ConfigManager (config_manager.py)**: Hot-reload support with file watching and callback system.

## Game Development

### Two Approaches

**1. Standalone Demos (demos/ directory)**
- 30+ existing examples (simon.py, snake.py, bubble.py, etc.)
- Direct imports: `from lpminimk3 import LaunchpadMiniMk3, Mode`
- Full control, no framework constraints
- Run directly: `python demos/game_name.py`

**2. Plugin System (plugins/ directory)**
- Inherit from `Game` base class (game_plugin.py)
- Required methods: `start()`, `handle_button_press(x, y)`, `stop()`
- Optional: `handle_button_release(x, y)`
- Auto-discovered by GameLoader
- Run: `python game_plugin.py` (presents menu of available games)

**Game Base Class Helpers**:
- `init_launchpad()` - Hardware connection
- `clear_grid()` - Turn off all LEDs
- `set_led(x, y, color)` - Update single button
- Metadata: name, description, difficulty, min_age

### Example Plugin
```python
from game_plugin import Game

class MyGame(Game):
    def __init__(self):
        super().__init__(name="My Game", description="Fun!",
                         difficulty="Easy", min_age=1)

    def start(self):
        self.clear_grid()
        # Initialize game state

    def handle_button_press(self, x, y):
        # Game logic
        pass

    def stop(self):
        self.clear_grid()
```

## Development Workflows

### Adding a New Configuration
1. Create `configs/my_config.yaml`
2. Define models (ASCII grid layouts), scales, colors
3. Add sound file mappings if needed
4. Load in code: `LaunchpadSynth('configs/my_config.yaml')`
5. Or use hot-reload with ConfigManager

### Adding Sound Files
1. Place .wav files in `sounds/` directory
2. Add to `file_char_and_locations` in YAML
3. Set color in `file_colors`
4. Use character in model layout grid

### Creating a New Game
**Standalone**: Create `demos/my_game.py`, import lpminimk3 directly
**Plugin**: Create `plugins/my_game.py`, inherit from Game class

### Web UI Development
- Flask routes in web_ui.py
- SocketIO events for real-time LED sync
- Templates in `templates/`, static assets in `static/`
- WebUIBroadcaster singleton provides state management

### Debugging
- Logging enabled by default (INFO level)
- Button events logged with (x, y) coordinates
- Grid state: `synth.get_ascii_grid()` shows current mappings
- Web UI provides visual debugging at http://localhost:5001

## Technical Conventions

- **Button coordinates**: (x, y) where both range 0-8
- **Colors**: RGB tuples like (255, 0, 0) for red
- **Frequencies**: Standard tuning (A4 = 440Hz, C4 = 261.63Hz)
- **Audio**: 16-bit PCM, 44.1kHz sample rate, sine waves via NumPy
- **Grid layout**: 9x9 grid, top row (y=0) often reserved for controls
- **Character mapping**: 'x' in layout = inactive button

## Important Architecture Notes

### Dependency Injection Pattern
- `web_broadcaster` parameter passed through LaunchpadSynth → Note → light_up_buttons()
- Allows running without web UI (parameter is optional)
- Enables console-only mode (main.py) and web-enabled mode (main_web.py) with same codebase

### Audio Playback Differences
- **Synthesized notes** (Note class): Polyphonic, multiple can play simultaneously (separate threads)
- **Sound files** (play_sound()): Monophonic, only one .wav at a time (stops previous before playing new)

### Web UI Communication
- Flask-SocketIO uses `threading` async mode (macOS compatible)
- No eventlet/gevent required
- Real-time LED updates via `update_led` SocketIO events
- New clients receive full grid state on connect

### Configuration Parsing
- Models must be valid 9x9 ASCII grids
- Characters in layout map to scales or file_char_and_locations
- No validation for character consistency (manual verification needed)
- Multiple models can share same scales/colors

## Known Limitations

1. **Chord Infrastructure**: Chord class defined but minimally used; multiple notes per button play sequentially, not simultaneously
2. **Debouncing Trade-off**: 5ms window reduces accidental double-triggers but may affect rapid play patterns
3. **Plugin Game Scope**: Games run independently, can't layer over synth soundboard (separate Launchpad init)
4. **No Formal Tests**: Testing relies on manual hardware verification and demo scripts

## Common Issues

- **No Launchpad detected**: Check USB connection, ensure no other app is using device
- **ModuleNotFoundError**: Run demos from project root or use `python -m demos.game_name`
- **Audio issues (Linux)**: Install ALSA: `sudo apt-get install libasound2-dev`
- **Multiple triggers**: Enable `debounce: true` in YAML config
- **Sound file not found**: Check paths in `file_char_and_locations` are relative to execution directory
