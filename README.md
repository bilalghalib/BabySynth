# 🎹 BabySynth - Synth.baby

**A baby-friendly synthesizer and interactive soundboard built with Python and the Launchpad Mini MK3**

Transform your Launchpad into a colorful, tactile musical instrument perfect for babies and young children! Each button can play musical notes or trigger fun sounds, with beautiful LED feedback.

https://github.com/bilalghalib/BabySynth/assets/3254792/a62da9f3-094c-42cb-885c-bde33f1aae00

## Features

- **🎵 Synthesizer Mode**: Play musical notes with different scales and layouts
- **🔊 Soundboard Mode**: Trigger .wav sound files with button presses
- **🌈 Visual Feedback**: Colorful LED lighting for each note/sound
- **📱 Web UI Monitor**: Real-time visual display of the Launchpad grid in your browser!
- **🎛️ Audio Engine Editor**: Web-based editor for waveforms, ADSR envelopes, and effects
- **⚙️ Visual Config Editor**: Drag-and-drop YAML editor with live preview!
- **🎭 LED Animations**: Define looping animations in YAML (rainbow waves, sparkles, breathing)
- **🌈 Color Themes**: Switch between color palettes on-the-fly (ocean, sunset, candy, etc.)
- **🎵 Chord Progressions**: Define musical sequences (lullabies, happy tunes, jazz)
- **⚡ Macros**: Button combos that trigger animations, themes, or light shows
- **💫 Light Shows**: Choreographed sequences perfect for birthdays and bedtime
- **🔥 Hot Reload**: Change configs without restarting!
- **🎮 30+ Games & Demos**: Simon Says, Snake, Bubble Pop, and many more!
- **🔌 Plugin System**: Easy framework for creating custom games - no advanced coding required!
- **👶 Baby-Friendly**: Designed for little hands with debouncing and simple interactions

## Hardware Required

- **Launchpad Mini MK3** by Novation ([Product Page](https://novationmusic.com/products/launchpad-mini-mk3))
- Computer with USB port (works on Windows, macOS, Linux)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/bilalghalib/BabySynth.git
cd BabySynth

# Install dependencies
pip install -r requirements.txt

# Connect your Launchpad Mini MK3 via USB

# Run the synthesizer
python main.py
```

### First Run

When you run `main.py`, the Launchpad will light up with colorful buttons:
- Each color represents a different musical note
- Press any button to play that note
- Release the button to stop the note
- The layout is fully customizable via `config.yaml`

### 🌐 Web UI Mode (NEW!)

For a visual monitor of what your baby is playing:

```bash
python main_web.py
```

Then open your browser to **http://localhost:5000**

You'll see:
- **Live View** (/) - Real-time visualization of the Launchpad grid
- **Audio Editor** (/editor) - Configure waveforms, ADSR envelopes, and effects
- **Config Editor** (/config) - Visually edit YAML configurations!
- Perfect for monitoring from another room or recording sessions!

### ⚙️ Config Editor

Edit YAML configurations visually in your browser!

- 🎨 **Visual Grid Layout** - Click to paint notes on the grid
- 🌈 **Color Picker** - Choose colors for each note
- 🎭 **Animation Editor** - Define LED animations
- 🎵 **Chord Creator** - Build chord progressions
- 💾 **Save & Hot Reload** - Apply changes instantly!

**Access:** http://localhost:5000/config

## Configuration

The main configuration file is `config.yaml`. Here's what you can customize:

### Define Custom Layouts

```yaml
models:
  ADGC:
    layout: |
      xxxxxxxxx
      ABCDEFGAx
      BCDEFGABx
      CDEFGABCx
      ...
```

Each character represents a different note or sound. The `x` means that button is inactive.

### Choose Musical Scales

```yaml
scales:
  C_major: [C, D, E, F, G, A, B]
  # Add your own scales!
```

### Customize Colors

```yaml
colors:
  C: [255, 0, 0]    # Red
  D: [0, 255, 0]    # Green
  E: [0, 0, 255]    # Blue
  # RGB values for each note
```

### Add Sound Files

```yaml
file_char_and_locations:
  Z: "./sounds/beezoo.wav"
  Y: "./sounds/upla.wav"

file_colors:
  Z: [128, 0, 0]    # Dark red
  Y: [0, 128, 0]    # Dark green
```

See `configs/` directory for more example configurations including:
- `drum_kit.yaml` - Drum machine layout
- `baby_grunge.yaml` - Alternative sound arrangements
- `baby_toxic.yaml` - Custom button mappings
- And more!

## Project Structure

```
BabySynth/
├── main.py              # Main entry point
├── main_web.py          # Web UI enabled version
├── synth.py             # Core synthesizer logic
├── note.py              # Note and button classes
├── game_plugin.py       # Game plugin system
├── web_ui.py            # Web server for live view
├── config.yaml          # Main configuration
├── requirements.txt     # Python dependencies
├── sounds/              # Sound files (.wav)
├── configs/             # Additional configurations
│   ├── drum_kit.yaml
│   ├── baby_config.yaml
│   └── ...
├── demos/               # Games and demos
│   ├── simon.py         # Simon Says game
│   ├── snake.py         # Snake game
│   ├── bubble.py        # Bubble popping
│   └── ... (30+ more!)
├── plugins/             # Custom game plugins
│   ├── whack_a_light.py
│   ├── rainbow_chase.py
│   └── README.md        # Plugin development guide
├── templates/           # Web UI HTML templates
│   ├── index.html       # Live view
│   └── editor.html      # Audio engine editor
└── static/              # Web UI assets
    ├── css/
    └── js/
```

## Games & Demos

BabySynth includes 30+ interactive games and demonstrations! Each is a standalone Python file in the `demos/` directory.

### Popular Demos

- **Simon Says** (`simon.py`) - Classic memory game with lights and sounds
- **Snake** (`snake.py`) - Navigate the snake around the grid
- **Bubble Pop** (`bubble.py`) - Pop colorful bubbles as they appear
- **Color Catch** (`colorcatch.py`) - Catch matching colors
- **Rainbow Effects** (`rainbow.py`) - Beautiful visual displays
- **Dance Party** (`dance.py`) - Rhythm and movement game

### Running Demos

```bash
python demos/simon.py
python demos/snake.py
# etc.
```

> Tip: Run demo scripts from the project root (or use `python -m demos.simon`) so Python can find `note.py` and the YAML configs. The `babyplayer` demo automatically looks in `configs/baby_config.yaml`, but you can pass a different path if you have your own layout.

See `demos/README.md` for a complete list and descriptions.

## 🔌 Creating Your Own Games (Plugin System)

**NEW!** BabySynth now includes an easy-to-use plugin system for creating custom games!

### Quick Start

1. Create a new Python file in the `plugins/` directory
2. Inherit from the `Game` base class
3. Implement three simple methods: `start()`, `handle_button_press()`, and `stop()`

### Example - Complete Game in ~30 Lines!

```python
from game_plugin import Game
import random

class MyFirstGame(Game):
    def __init__(self):
        super().__init__(
            name="Color Pop",
            description="Pop the colors as they appear!",
            difficulty="Easy",
            min_age=1
        )
        self.score = 0

    def start(self):
        self.clear_grid()
        self.show_random_light()

    def show_random_light(self):
        x = random.randint(0, 8)
        y = random.randint(1, 8)
        color = (255, 0, 0)  # Red
        self.set_led(x, y, color)
        self.current = (x, y)

    def handle_button_press(self, x, y):
        if (x, y) == self.current:
            self.score += 1
            print(f"Score: {self.score}")
            self.clear_grid()
            self.show_random_light()

    def stop(self):
        self.clear_grid()
        print(f"Final score: {self.score}")
```

### Running Plugin Games

```bash
python game_plugin.py
```

The system automatically discovers all games in `plugins/` and lets you choose which to play!

### For Parents and Educators

The plugin system is designed to be accessible to:
- Parents with basic Python knowledge
- Educators teaching programming
- Older children learning to code
- Anyone wanting to create custom interactive experiences

See `plugins/README.md` for a complete guide with examples!

## How It Works

### Core Components

1. **LaunchpadSynth** (`synth.py`) - Main controller
   - Connects to Launchpad hardware
   - Maps buttons to notes/sounds
   - Handles button events
   - Manages LED colors

2. **Note Classes** (`note.py`)
   - **Button**: Represents a physical button (x, y position, color)
   - **Note**: Synthesizes musical tones using sine waves
   - **Chord**: Plays multiple notes simultaneously

3. **Configuration** (`config.yaml`)
   - Define grid layouts with ASCII art
   - Map notes to frequencies and colors
   - Specify sound file locations
   - Configure debouncing and other settings

### Audio Generation

- Musical notes are generated as **sine waves** using NumPy
- Standard musical frequencies (A4 = 440Hz, C4 = 261.63Hz, etc.)
- 16-bit PCM audio at 44.1kHz sample rate
- Threading ensures smooth, non-blocking playback

## Use Cases

- **Baby Development**: Tactile and visual stimulation, cause-and-effect learning
- **Music Education**: Learn scales, note relationships, rhythm
- **Creative Play**: Freeform musical exploration
- **Soundboard**: Sound effects for performances or presentations
- **Game Platform**: Foundation for Launchpad-based games
- **Prototyping**: Base for other MIDI controller projects

## Dependencies

All dependencies are listed in `requirements.txt`:

- `lpminimk3` - Launchpad Mini MK3 Python interface
- `simpleaudio` - Cross-platform audio playback
- `numpy` - Numerical operations for wave generation
- `pyyaml` - YAML configuration parsing
- `mingus` - Music theory utilities

## Troubleshooting

### "No Launchpad found"
- Ensure your Launchpad Mini MK3 is connected via USB
- Try unplugging and reconnecting the device
- Check that no other application is using the Launchpad

### Audio Not Playing
- **Linux**: Install ALSA dependencies: `sudo apt-get install libasound2-dev`
- **macOS**: Should work out of the box
- **Windows**: May require Visual C++ redistributables

### Import Errors
```bash
pip install -r requirements.txt
```

### "ModuleNotFoundError: No module named 'note'"
- Run the script from the project root or invoke it as a module (e.g. `python -m demos.britney`) so the repository stays on `PYTHONPATH`.
- If you're launching a demo that expects a YAML like `baby_config.yaml`, the script now searches the `/configs` directory automatically. You can also pass the full path explicitly.

### "unsupported platform" when starting `main_web.py`
- Flask-SocketIO now forces the lightweight `threading` async mode, so you no longer need `eventlet`/`trio` on macOS. Reinstall dependencies if you still see the error: `pip install --force-reinstall -r requirements.txt`.

### Buttons Triggering Multiple Times
- Enable debouncing in `config.yaml`: `debounce: true`

## Contributing

Contributions are welcome! Here are some ideas:
- Add new game demos
- Create new configuration layouts
- Add support for more complex waveforms (sawtooth, square waves)
- Improve documentation
- Add MIDI file playback support
- Create a GUI configuration editor

## Future Enhancement Ideas

1. **Advanced Audio Engine**
   - Support for multiple waveforms (sawtooth, square, triangle)
   - ADSR envelope control (Attack, Decay, Sustain, Release)
   - Effects processing (reverb, delay, filters)
   - Polyphonic synthesis improvements
   - Real-time audio visualization

2. **Web Interface & Remote Control**
   - Web-based configuration editor
   - Remote control via smartphone/tablet
   - Real-time status monitoring
   - Record and playback sessions
   - Share configurations online

3. **Educational Features**
   - Guided tutorials for learning scales
   - Music theory lessons built-in
   - Interactive games that teach musical concepts
   - Progress tracking for skill development
   - Pre-made lesson plans for parents/educators

4. **Multi-Device & Collaboration**
   - Support for multiple Launchpads simultaneously
   - Network synchronization for collaborative playing
   - MIDI output to external synthesizers/DAWs
   - OSC (Open Sound Control) integration
   - Record MIDI sequences for later playback

5. **Expanded Game Library**
   - More sophisticated rhythm games
   - Melody composition games
   - Pattern recognition challenges
   - Multi-player competitive modes
   - Adaptive difficulty based on age/skill level
   - Sound-based storytelling games

## License

This project is intended for educational and personal use. Please ensure you have the appropriate Launchpad hardware.

## Credits

Created by [@bilalghalib](https://github.com/bilalghalib)

Built with love for babies and music enthusiasts everywhere! 🎵👶

## Links

- [GitHub Repository](https://github.com/bilalghalib/BabySynth)
- [Launchpad Mini MK3](https://novationmusic.com/products/launchpad-mini-mk3)
- [Video Walkthrough](https://github.com/bilalghalib/BabySynth/assets/3254792/a62da9f3-094c-42cb-885c-bde33f1aae00)

---

**Made with ❤️ for tiny musicians**
