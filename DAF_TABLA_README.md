# Daf & Tabla Percussion Demo

Transform your Launchpad Mini MK3 into a traditional Persian daf or Indian tabla!

## Overview

This demo turns the Launchpad's 8x8 grid into an interactive percussion soundboard featuring:

- **Tabla strokes**: Na, Tin, Te, Ge, Ka, Dha (traditional Indian hand drum)
- **Daf strokes**: Dum, Tak, Ka, Roll (traditional Persian frame drum)
- **Multiple layouts**: Optimized configurations for different playing styles
- **Pattern recording**: Record and playback your rhythms
- **Visual feedback**: Color-coded pads (red=bass, blue=treble, etc.)

## Quick Start

### 1. Run the setup script

```bash
./setup_daf_tabla.sh
```

This creates the directory structure and placeholder sound files to get you started immediately.

### 2. Run the demo

```bash
# Basic layout (4x4 daf + 4x4 tabla)
python demos/daf_tabla.py

# Full tabla layout
python demos/daf_tabla.py --layout TABLA_FULL

# Full daf layout
python demos/daf_tabla.py --layout DAF_FULL
```

### 3. Play!

- Press the pads to trigger percussion sounds
- Top-right corner button: Start/stop recording
- Record your rhythm, then it will auto-playback

## Installation

### Prerequisites

- Launchpad Mini MK3 connected via USB
- Python 3.7+
- Required packages (from requirements.txt):
  - lpminimk3
  - simpleaudio
  - pyyaml
  - numpy

### Setup Sound Files

**Option 1: Quick test with placeholders**
```bash
./setup_daf_tabla.sh
```

**Option 2: Use real percussion samples**

See the detailed guide: [`sounds/DAF_TABLA_SOUNDS.md`](sounds/DAF_TABLA_SOUNDS.md)

Free sample sources:
- Freesound.org (search: "tabla" or "daf")
- 99sounds.org
- YouTube Audio Library

Place files in:
```
sounds/
├── tabla/
│   ├── na.wav      # Open rim stroke
│   ├── tin.wav     # Closed rim stroke
│   ├── te.wav      # Middle stroke
│   ├── ge.wav      # Bass open
│   ├── ka.wav      # Bass slap
│   └── dha.wav     # Combined stroke
└── daf/
    ├── dum.wav     # Bass center
    ├── tak.wav     # Treble rim
    └── roll.wav    # Finger roll
```

## Layouts

### DAF_TABLA (Default)
Balanced layout with both instruments:
```
Top Half:
  Left 4 columns  → Bass strokes (tabla/daf)
  Right 4 columns → Treble strokes

Bottom Half:
  Left 4 columns  → Daf bass (Dum)
  Right 4 columns → Daf treble (Tak)
```

### TABLA_FULL
Complete tabla layout:
```
Top rows:    Na (left) | Tin (center) | Te (right)
Middle rows: Ge (left) | Ka (center)  | Dha (right)
Bottom rows: Rolls
```

### DAF_FULL
Complete daf layout:
```
Top:          Bass (Dum)
Upper middle: Treble (Tak)
Lower middle: Slaps (Ka)
Bottom:       Rolls
```

## Features

### Pattern Recording

1. Press the **top-right corner button** (8,0) to start recording
2. Play your rhythm on the pads
3. Press the corner button again to stop
4. Your pattern automatically plays back!

The corner button shows your recording status:
- **Blue**: Ready to record
- **Red**: Currently recording
- **Green**: Recording saved, ready to playback

### Color Coding

Pads are color-coded by stroke type:
- **Red tones**: Bass/low sounds (Dum, Ge)
- **Blue tones**: Treble/high sounds (Na, Tin, Tak)
- **Orange/Yellow**: Daf strokes
- **Purple**: Combined strokes (Dha)
- **Green**: Rolls and special effects

### Web Interface

Run with the web UI for visual monitoring:

```bash
python main_web.py
```

Then open http://localhost:5001 and load the daf_tabla configuration.

## Usage Examples

### Basic Tabla Rhythm (Teental)

```bash
python demos/daf_tabla.py --layout TABLA_FULL
```

Play this pattern (16 beat cycle):
```
Dha Dhin Dhin Dha | Dha Dhin Dhin Dha |
Dha Tin Tin Ta    | Ta Dhin Dhin Dha
```

### Daf Rhythm (6/8 Persian)

```bash
python demos/daf_tabla.py --layout DAF_FULL
```

Play:
```
Dum Tak Ka Tak Dum Tak
```

### Freestyle Jam

```bash
python demos/daf_tabla.py
```

Use the default balanced layout to mix both instruments!

## Traditional Strokes

### Tabla Strokes

**Right Hand (Dayan - treble drum):**
- **Na/Ta**: Open resonant stroke on the edge
- **Tin**: Closed stroke, dampened with fingertips
- **Te/Ti**: Stroke on the center area
- **Tun**: Bass stroke on the center

**Left Hand (Bayan - bass drum):**
- **Ge/Ga**: Open bass, palm lifted for resonance
- **Ke**: High-pitched stroke, palm pressed
- **Ka**: Sharp slap with palm

**Combined:**
- **Dha**: Na + Ge played simultaneously
- **Dhin**: Tin + Ge played simultaneously

### Daf Strokes

- **Dum/Doom**: Deep bass stroke in center with fingertips
- **Tak**: Sharp high stroke on rim/edge
- **Ka**: Slap stroke
- **Roll**: Rapid finger roll around the rim
- **Sak**: Muted stroke

## Configuration

Edit [`configs/daf_tabla.yaml`](configs/daf_tabla.yaml) to:
- Change layouts
- Adjust colors
- Map different sound files
- Add new stroke types
- Create custom rhythm patterns

Example:
```yaml
file_char_and_locations:
  N: "./sounds/tabla/na.wav"
  T: "./sounds/tabla/tin.wav"
  # Add your own samples...

file_colors:
  N: [100, 150, 255]  # Light blue
  T: [50, 100, 200]   # Medium blue
```

## Troubleshooting

### "No Launchpad detected"
- Check USB connection
- Ensure no other app is using the Launchpad
- Try unplugging and reconnecting

### "File not found" errors
- Run `./setup_daf_tabla.sh` to create directories
- Check that sound files exist in `sounds/tabla/` and `sounds/daf/`
- Verify file names match the config (case-sensitive!)

### No sound playing
- Test sound files in a media player first
- Ensure files are WAV format (16-bit, 44.1kHz)
- Check volume levels in your OS

### Sounds are distorted
- Normalize audio files (see DAF_TABLA_SOUNDS.md)
- Reduce volume in audio editor
- Use 16-bit or 24-bit WAV files

## Advanced Usage

### Use with Main App

```bash
# Console mode
python main.py
# Load daf_tabla config when prompted

# Web mode
python main_web.py
# Open http://localhost:5001
# Use config editor to load configs/daf_tabla.yaml
```

### Custom Layouts

Create your own layout in `configs/daf_tabla.yaml`:

```yaml
models:
  MY_CUSTOM:
    layout: |
      xxxxxxxxx
      NNNNNNNNx
      TTTTTTTTx
      # ... 9x9 grid
```

Each character maps to a sound file or synthesized note.

### Integration with Other Configs

Mix percussion with melodic instruments by combining configurations!

## Resources

- **Sound Samples Guide**: [`sounds/DAF_TABLA_SOUNDS.md`](sounds/DAF_TABLA_SOUNDS.md)
- **Main Project**: [`README.md`](README.md)
- **Configuration Reference**: [`CLAUDE.md`](CLAUDE.md)

### Learn More

- **Tabla Tutorial**: https://www.taalmala.com
- **Daf Tutorial**: Search YouTube for "daf tutorial basic strokes"
- **Free Samples**: https://freesound.org
- **Audio Editing**: https://www.audacityteam.org

## Contributing

Found a great rhythm pattern? Created a custom layout?

Feel free to share your configurations and sound packs!

## License

Part of the BabySynth project. See main project license.

---

**Happy drumming! 🥁🎵**

For questions or issues, see the main BabySynth documentation.
