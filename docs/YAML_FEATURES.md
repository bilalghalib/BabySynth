# 🎨 BabySynth YAML Configuration Guide

Welcome to the complete guide for BabySynth's powerful YAML configuration system! This document covers everything from basic setup to advanced features like animations, themes, and macros.

## Table of Contents

1. [Basic Configuration](#basic-configuration)
2. [LED Animations](#led-animations)
3. [Chord Progressions](#chord-progressions)
4. [Color Themes](#color-themes)
5. [Macros](#macros)
6. [Light Shows](#light-shows)
7. [Advanced Audio](#advanced-audio)
8. [Complete Examples](#complete-examples)

---

## Basic Configuration

Every BabySynth config needs these core elements:

```yaml
name: "My Config"

models:
  my_layout:
    layout: |
      xxxxxxxxx
      ABCDEFGAx
      BCDEFGABx
      ...

scales:
  C_major: [C, D, E, F, G, A, B]

colors:
  C: [255, 0, 0]    # Red
  D: [0, 255, 0]    # Green
  # ... more colors

debounce: true  # Prevent double-presses
```

### Layout Grid

The layout is a 9x9 ASCII grid where:
- Letters (A-G) = musical notes
- Numbers (0-9) = sound file references
- `x` = empty (no function)
- `.` = inactive

---

## 🎭 LED Animations

**NEW!** Define looping LED animations that play on the Launchpad.

### Simple Animation

```yaml
animations:
  rainbow_wave:
    duration: 2.0    # Total animation length
    loop: true       # Repeat forever
    frames:
      - delay: 0.1   # Show this frame for 0.1 seconds
        pattern:     # 9x9 grid of RGB colors
          - [[255,0,0], [255,0,0], ...]  # Row 1
          - [[255,127,0], [255,127,0], ...]  # Row 2
```

### Brightness Animation

```yaml
animations:
  breathing:
    duration: 3.0
    loop: true
    frames:
      - delay: 0.5
        brightness: 0.3
      - delay: 0.5
        brightness: 1.0
      - delay: 0.5
        brightness: 0.3
```

### Full-Grid Flash

```yaml
animations:
  disco_flash:
    duration: 0.5
    loop: true
    frames:
      - delay: 0.1
        all_buttons: [255, 0, 255]  # All magenta
      - delay: 0.1
        all_buttons: [0, 255, 255]  # All cyan
```

### How to Use

```python
# In Python code:
from config_manager import ConfigManager, AnimationPlayer

manager = ConfigManager()
config = manager.load('configs/party_mode.yaml')

player = AnimationPlayer(launchpad, web_broadcaster)
animation = manager.get_animation('disco_flash')
player.play(animation)
```

---

## 🎵 Chord Progressions

**NEW!** Define sequences of notes that play together.

### Basic Progression

```yaml
chord_progressions:
  happy: [C, F, G, C]
  sad: [A, D, E, A]
  lullaby: [C, G, A, F, C]
```

### Actual Chords (Multiple Notes)

```yaml
chords:
  C_major: [C, E, G]
  F_major: [F, A, C]
  G_major: [G, B, D]
  A_minor: [A, C, E]
```

### Progression with Timing

```yaml
chord_progressions:
  complex_song:
    - note: C
      duration: 1.0
    - note: F
      duration: 0.5
    - note: G
      duration: 0.5
    - chord: C_major
      duration: 2.0
```

### How to Use

Assign to a button or macro:

```yaml
macros:
  play_happy_song:
    trigger: [[4,4]]  # Center button
    action: play_progression('happy')
```

---

## 🌈 Color Themes

**NEW!** Create color palettes and switch between them on-the-fly!

### Define Themes

```yaml
themes:
  ocean:
    C: [0, 100, 200]
    D: [0, 150, 255]
    E: [50, 200, 255]
    F: [100, 220, 255]
    G: [0, 180, 230]
    A: [0, 160, 210]
    B: [0, 140, 190]

  sunset:
    C: [255, 50, 0]
    D: [255, 100, 0]
    E: [255, 150, 50]
    F: [255, 200, 100]
    G: [255, 150, 150]
    A: [200, 100, 150]
    B: [150, 50, 100]

  candy:
    C: [255, 20, 147]   # Pink
    D: [255, 105, 180]  # Hot pink
    E: [255, 192, 203]  # Light pink
    F: [255, 0, 255]    # Magenta
    G: [238, 130, 238]  # Violet
    A: [221, 160, 221]  # Plum
    B: [255, 182, 193]  # Light pink
```

### Switch Themes with Macros

```yaml
macros:
  theme_ocean:
    trigger: [[0,1]]  # Top row, second button
    action: apply_theme('ocean')

  theme_sunset:
    trigger: [[1,1]]
    action: apply_theme('sunset')
```

### How to Use

```python
manager.apply_theme('candy')
# All buttons instantly update to candy colors!
```

---

## ⚡ Macros

**NEW!** Button combinations that trigger special actions.

### Single Button Macro

```yaml
macros:
  disco_mode:
    trigger: [[4,4]]  # Press center button
    action: play_animation('disco_flash')
```

### Multi-Button Combo

```yaml
macros:
  secret_mode:
    trigger: [[0,0], [8,0]]  # Press top-left AND top-right together
    action: play_animation('rainbow_wave')
```

### Sequential Actions

```yaml
macros:
  party_starter:
    trigger: [[4,4]]
    actions:
      - apply_theme('neon')
      - play_animation('strobe')
      - play_progression('party_time')
```

### Available Actions

- `play_animation('name')` - Start an animation
- `apply_theme('name')` - Switch color theme
- `play_progression('name')` - Play chord progression
- `play_sound('file.wav')` - Play audio file
- `play_light_show('name')` - Start a light show

---

## 💫 Light Shows

**NEW!** Choreographed sequences perfect for performances!

### Basic Light Show

```yaml
light_shows:
  baby_birthday:
    duration: 10.0   # Total show length
    sequence:
      - time: 0.0
        action: play_animation('rainbow_wave')
      - time: 3.0
        action: play_progression('happy')
      - time: 6.0
        action: apply_theme('candy')
      - time: 8.0
        action: play_animation('sparkle')
```

### Bedtime Routine

```yaml
light_shows:
  goodnight:
    duration: 10.0
    sequence:
      - time: 0.0
        action: apply_theme('moonlight')
      - time: 1.0
        action: play_animation('gentle_wave')
      - time: 3.0
        action: play_progression('lullaby')
      - time: 7.0
        action: play_animation('soft_breathing')
      - time: 9.0
        action: fade_to_black(duration=2.0)
```

---

## 🎼 Advanced Audio

### Waveform Selection

```yaml
waveforms:
  default: sine
  notes:
    C: sine      # Smooth
    D: square    # Sharp
    E: triangle  # Mellow
    F: sawtooth  # Bright
```

### ADSR Envelopes

Control how notes fade in/out:

```yaml
envelopes:
  default:
    attack: 0.1   # Fade in time
    decay: 0.2    # Drop to sustain
    sustain: 0.7  # Held volume (0-1)
    release: 0.3  # Fade out time

  punchy:  # Fast attack for percussion
    attack: 0.01
    decay: 0.1
    sustain: 0.5
    release: 0.1

  soft:  # Gentle for melody
    attack: 0.5
    decay: 0.8
    sustain: 0.8
    release: 1.0
```

### Audio Effects

```yaml
audio_effects:
  reverb:
    enabled: true
    mix: 30        # 0-100
    room_size: 50  # 0-100

  delay:
    enabled: true
    mix: 20
    time: 0.5  # Seconds

  filter:
    enabled: true
    cutoff: 1000  # Hz
    resonance: 20  # 0-100
```

---

## 📝 Complete Examples

### Party Mode

Perfect for celebrations!

```yaml
name: "Party Mode"

animations:
  disco_flash:
    duration: 0.5
    loop: true
    frames:
      - { delay: 0.1, all_buttons: [255,0,255] }
      - { delay: 0.1, all_buttons: [0,255,255] }

chord_progressions:
  party_time: [C, G, A, F]

themes:
  neon:
    C: [255, 20, 147]
    D: [0, 255, 127]
    E: [255, 215, 0]

macros:
  start_party:
    trigger: [[4,4]]
    actions:
      - apply_theme('neon')
      - play_animation('disco_flash')
      - play_progression('party_time')
```

### Bedtime Mode

Soothing and calm!

```yaml
name: "Bedtime"

animations:
  soft_breathing:
    duration: 4.0
    loop: true
    frames:
      - { delay: 1.0, brightness: 0.2 }
      - { delay: 1.0, brightness: 0.5 }
      - { delay: 1.0, brightness: 0.2 }

themes:
  moonlight:
    C: [30, 30, 80]
    D: [40, 40, 90]
    E: [50, 50, 100]

chord_progressions:
  lullaby: [C, G, F, C]

envelopes:
  default:
    attack: 0.5
    decay: 1.0
    sustain: 0.8
    release: 1.5
```

---

## 🎨 Using the Visual Editor

Don't want to edit YAML by hand? Use the web editor!

1. Run `python main_web.py`
2. Open http://localhost:5000/config
3. Visual editing for:
   - Grid layout (click to paint)
   - Color picking
   - Animation definitions
   - Theme creation
4. Save and hot-reload!

---

## 🔥 Hot Reload

Change configs without restarting:

```python
manager = ConfigManager()
manager.start_watching(callback=my_reload_function)

# Edit YAML file...
# Automatically reloads when saved!
```

Or use the web UI "Apply & Hot Reload" button!

---

## 💡 Tips & Tricks

1. **Start Simple** - Begin with basic colors and layouts
2. **Test Incrementally** - Add one animation at a time
3. **Use Themes** - Create different moods (party, bedtime, learning)
4. **Combine Features** - Macros can trigger light shows!
5. **Save Presets** - Keep favorite configs in `configs/` folder
6. **Share** - Export configs as JSON to share with others

---

## 🎯 What's Possible?

With these YAML features, you can create:

- **🎵 Interactive Songs** - Chord progressions triggered by buttons
- **🎨 Art Shows** - Animated LED patterns
- **🎮 Custom Games** - Combine with the plugin system!
- **🌙 Routines** - Morning/bedtime light shows
- **🎪 Performances** - Choreographed sequences
- **🎨 Themes** - Seasonal color palettes
- **⚡ Power-User Shortcuts** - Macro buttons for quick actions

---

## 📚 More Resources

- See `configs/advanced_features.yaml` for ALL features demonstrated
- See `configs/party_mode.yaml` for party configuration
- See `configs/bedtime.yaml` for calming configuration
- Visit http://localhost:5000/config for visual editing

**Happy configuring!** 🎹✨
