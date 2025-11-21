# LED Animations 🎨

> **✨ NEW IN PHASE 3!** BabySynth buttons now breathe, pulse, and flow with expressive LED animations.

## What Are LED Animations?

LED animations make your Launchpad come **alive**. Instead of simple on/off LED states, buttons now:

- **Breathe** gently while notes play (like they're "singing")
- **Pulse** when you press them (satisfying feedback)
- **Fade** smoothly when you release (graceful transitions)
- **Ripple** outward from pressed buttons (spatial awareness)
- **Sparkle** with random variations (organic feel)

## Why Animations Matter

From our values assessment, animations serve **Marcus's attention policy**:

> *"VISUAL language created by the lit buttons during performance"*

But they also help:
- **👶 Sarah:** More engaging for children - buttons feel responsive and alive
- **🧑‍⚕️ James:** Visual feedback supports engagement tracking
- **🎸 Marcus:** Performance becomes a visual-auditory synthesis

## Quick Start

### Animations Are Enabled by Default!

Just run BabySynth normally - animations work automatically:

```bash
python main.py
```

You'll see:
- ✨ Quick white **pulse** when you press a button
- 🫁 Gentle **breathing** animation while the note plays
- 🌊 Smooth **fade** back to color when you release

### Try the Showcase

See all animation types:

```bash
python demos/animation_showcase.py
```

This demonstrates:
1. Breathing (sustained notes)
2. Pulse (button feedback)
3. Fade (color transitions)
4. Ripple (spatial effects)
5. Sparkle (twinkling)
6. Wave (synchronized patterns)
7. Rainbow cycle (color wheel)
8. Strobe (high-energy flashing)

---

## Animation Types

### 1. 🫁 Breathing Animation

**What it does:** Smooth sine-wave brightness modulation

**When it's used:** While a note is held down

**Effect:** Button "breathes" like it's alive - gets brighter and dimmer in a smooth cycle

**Parameters:**
- `period`: Time for one breath cycle (default: 2.0s)
- `min_brightness`: Minimum brightness 0-1 (default: 0.5)

**Example:**
```python
animator.breathe(x=4, y=4, base_color=(255, 0, 0), period=2.0, min_brightness=0.3)
```

**Values served:** Creates a sense of **sustained presence** - the button isn't static, it's "playing"

---

### 2. 💥 Pulse Animation

**What it does:** Quick burst of brightness then return to base

**When it's used:** Immediately when you press a button

**Effect:** White flash that says "I heard you!"

**Parameters:**
- `duration`: Pulse length (default: 0.1s)
- `max_brightness`: Peak brightness multiplier (default: 1.5x)

**Example:**
```python
animator.pulse(x=4, y=4, base_color=(255, 0, 0), duration=0.15, max_brightness=1.8)
```

**Values served:** **Immediate tactile feedback** - satisfying confirmation of action

---

### 3. 🌈 Fade Animation

**What it does:** Smooth color transition

**When it's used:** When releasing a button (white → base color)

**Effect:** Graceful transition, not jarring

**Parameters:**
- `from_color`: Starting color
- `to_color`: Ending color
- `duration`: Fade time (default: 0.3s)
- `curve`: Easing function (linear, ease_in, ease_out, etc.)

**Example:**
```python
animator.fade(x=4, y=4, from_color=(255, 255, 255), to_color=(255, 0, 0), duration=0.3)
```

**Values served:** **Smooth transitions** preserve flow state

---

### 4. 🌊 Ripple Animation

**What it does:** Expanding wave from center point

**When it's used:** (Currently in showcase only - could be added for special events)

**Effect:** Beautiful radial spread, like dropping a stone in water

**Parameters:**
- `center_x, center_y`: Origin point
- `radius`: How far the ripple spreads
- `duration`: Time to reach max radius
- `fade_out`: Whether colors fade as ripple expands

**Example:**
```python
animator.ripple(center_x=4, center_y=4, color=(0, 255, 255), radius=3, duration=0.8)
```

**Values served:** **Spatial awareness** - shows relationships between buttons

---

### 5. ✨ Sparkle Animation

**What it does:** Random brightness variations like twinkling stars

**When it's used:** (Showcase/special modes)

**Effect:** Organic, alive feeling - never quite the same twice

**Parameters:**
- `duration`: How long to sparkle (0 = forever)
- `intensity`: How much brightness varies (0-1)

**Example:**
```python
animator.sparkle(x=4, y=4, base_color=(255, 255, 255), duration=5.0, intensity=0.6)
```

**Values served:** **Organic responsiveness** - feels less mechanical

---

### 6. 🌀 Wave Animation

**What it does:** Synchronized breathing across multiple buttons with phase offset

**When it's used:** For chords or sequences

**Effect:** Buttons pulse in a traveling wave pattern

**Parameters:**
- `buttons`: List of (x, y) positions
- `period`: Wave cycle time
- `phase_offset`: Delay between adjacent buttons

**Example:**
```python
buttons = [(2, 4), (3, 4), (4, 4), (5, 4)]
animator.wave(buttons, color=(255, 100, 0), period=2.0, phase_offset=0.2)
```

**Values served:** **Pattern visualization** - see the sequence as a wave

---

### 7. 🌈 Rainbow Cycle

**What it does:** Continuous rotation through color wheel

**When it's used:** Special modes, effects

**Effect:** Psychedelic color transitions

**Parameters:**
- `period`: Time for one complete rainbow cycle

**Example:**
```python
animator.rainbow_cycle(x=4, y=4, period=3.0)
```

**Values served:** **Exploratory play** - pure visual delight

---

### 8. ⚡ Strobe Animation

**What it does:** Rapid on/off flashing

**When it's used:** High-energy moments

**Effect:** Attention-grabbing flash

**Parameters:**
- `frequency`: Flashes per second
- `duration`: Total strobe time

**Example:**
```python
animator.strobe(x=4, y=4, color=(255, 0, 255), frequency=8.0, duration=1.0)
```

**Values served:** **High-energy expression** - intensity visualization

---

## Configuration

### Enable/Disable Animations

In your config YAML:

```yaml
animations_enabled: true  # Set to false to disable
```

### Custom Animation Settings

```yaml
animations_enabled: true

animation_presets:
  breathe:
    period: 2.0         # Breathing cycle time (seconds)
    min_brightness: 0.4 # Minimum brightness (0.0 to 1.0)

  pulse:
    duration: 0.15      # Pulse duration (seconds)
    max_brightness: 1.8 # Peak brightness multiplier

  fade:
    duration: 0.3       # Fade duration (seconds)
    curve: "ease_out"   # Options: linear, ease_in, ease_out, ease_in_out, sine
```

### Disable Animations for Performance

If you're running on slower hardware or want minimal CPU usage:

```yaml
animations_enabled: false
```

This reverts to simple on/off LED behavior (like Phase 1/2).

---

## Technical Details

### Performance

- **CPU Usage:** Minimal - animations run in separate threads at 30 FPS
- **Thread Safety:** Each button can have independent animations
- **Responsiveness:** Zero impact on audio or input latency

### Implementation

Animations use a frame-based system:
- 30 FPS refresh rate (33ms per frame)
- Non-blocking threaded execution
- Automatic cleanup when stopped
- Multiple simultaneous animations supported

### Session Recording

LED animations are fully recorded! When you replay a session, you'll see:
- All LED color changes
- Timing of animations
- Visual state at each moment

This means you can **review the visual performance** later.

---

## Use Cases by User Type

### 👶 Parents (Sarah)

**Why animations help:**
- More engaging for children
- Clear cause-effect (press → flash → breathe)
- Holds attention longer
- Visual development stimulation

**Recommended settings:**
```yaml
animations_enabled: true
animation_presets:
  breathe:
    period: 1.5      # Faster breathing = more engaging for toddlers
    min_brightness: 0.5
  pulse:
    max_brightness: 2.0  # Brighter pulse = clearer feedback
```

---

### 🎸 Musicians (Marcus)

**Why animations help:**
- Visual language for performance
- Audience sees your process
- LED patterns become part of composition
- Spatial visualization of note relationships

**Recommended settings:**
```yaml
animations_enabled: true
animation_presets:
  breathe:
    period: 2.0      # Slower, more expressive
    min_brightness: 0.3  # Wider dynamic range
  fade:
    curve: "ease_in_out"  # Smooth, musical transitions
```

**Pro tip:** Record your performance sessions - the LED animations are captured too!

---

### 🧑‍⚕️ Therapists (James)

**Why animations help:**
- Visual engagement indicators
- Breathing animation shows sustained attention
- Pulse feedback confirms client awareness
- Gentler than harsh on/off

**Recommended settings:**
```yaml
animations_enabled: true
animation_presets:
  breathe:
    period: 2.5      # Slower, calming
    min_brightness: 0.5
  pulse:
    duration: 0.2    # Slightly longer for processing
    max_brightness: 1.5  # Subtle, not overwhelming
```

---

## Advanced: Custom Animations

### Creating Your Own

Want to add custom animation effects? The API is straightforward:

```python
from led_animator import LEDAnimator

animator = LEDAnimator(launchpad)

# Your custom animation logic
def my_custom_animation(x, y):
    # Run in a thread
    while not stopped:
        # Calculate color based on time, position, etc.
        color = calculate_color()
        animator._set_led_color(x, y, color)
        time.sleep(1/30)  # 30 FPS

# Start it
threading.Thread(target=lambda: my_custom_animation(4, 4)).start()
```

See `led_animator.py` for examples of all built-in animations.

---

## Troubleshooting

### "Animations are flickering"

This might happen on older systems. Try:
1. Reduce FPS in `led_animator.py`: `self.fps = 20`
2. Disable session recording during playback
3. Use simpler animations (disable sparkle/rainbow)

### "No animations appearing"

Check:
1. Is `animations_enabled: true` in your config?
2. Are you running the latest code?
3. Try the showcase: `python demos/animation_showcase.py`

### "Performance issues"

Animations use minimal CPU, but if needed:
1. Set `animations_enabled: false` in config
2. Reduce animation complexity (fewer simultaneous animations)
3. Increase frame time: `self.frame_time = 1/20` (20 FPS instead of 30)

---

## Comparison: Before vs. After

### Before (Phase 1-2):
- Button press → LED white (instant)
- Button release → LED returns to color (instant)
- Static, binary states
- Functional but mechanical

### After (Phase 3):
- Button press → White **pulse** (0.1s satisfying flash)
- While holding → **Breathing** animation (alive, sustained)
- Button release → Smooth **fade** back (graceful)
- Dynamic, expressive states
- Feels organic and responsive

---

## Philosophy

From the values assessment:

> "Marcus pays attention to the **VISUAL language created by lit buttons** during performance"

Animations serve this by:
1. **Richer vocabulary** - More than just on/off
2. **Temporal expression** - Timing and rhythm visible
3. **Spatial relationships** - Ripples show connections
4. **Organic feel** - Less mechanical, more alive
5. **Performance art** - LEDs become part of the show

But we also serve other values:
- **Engagement** (Sarah's child stays interested longer)
- **Feedback** (James's clients get clear confirmation)
- **Flow state** (Smooth transitions don't break concentration)

---

## What's Next?

Future animation ideas (Phase 4+):
- **Adaptive brightness** based on ambient light
- **Sync to tempo** - animations match playing speed
- **Collaborative waves** - multiple users create combined effects
- **Pattern memory** - LEDs "remember" recent notes
- **Audio-reactive** - brightness responds to volume

---

## Credits

Animations built on principles from:
- **Music visualization theory** - Color and motion express sound
- **Game design** - Satisfying feedback loops
- **Performance art** - LEDs as expressive medium

Inspired by:
- Novation Launchpad performance videos
- Monome grid aesthetics
- Reaktor Blocks visual feedback

---

**Try it now:**

```bash
# See the showcase
python demos/animation_showcase.py

# Use in regular play
python main.py

# Or with a profile
python profiles/launch_musician.py
```

**Every press now has personality. Every hold breathes life. Every release flows gracefully.** 🎨✨
