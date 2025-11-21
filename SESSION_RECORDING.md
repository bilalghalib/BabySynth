# Session Recording & Playback

> **✨ NEW!** BabySynth now remembers every moment of your musical journey.

## What is Session Recording?

Session recording captures **every button press, LED change, and sound** during your BabySynth sessions. This enables:

- **👶 For Parents:** Review your child's discovery moments and developmental progress
- **🎸 For Musicians:** Analyze embodied patterns and performance flow
- **🧑‍⚕️ For Therapists:** Document client engagement and therapeutic milestones

## Quick Start

### 1. Recording is Automatic

Just run BabySynth as usual:

```bash
python main.py
```

Your session is automatically recorded! When you stop (Ctrl+C), you'll see:

```
✨ Session saved! Run 'python replay.py --list' to see your sessions
   Replay this session with: python replay.py 1
```

### 2. View Your Sessions

```bash
python replay.py --list
```

Output:
```
================================================================================
  RECORDED SESSIONS
================================================================================

  ✨ Session #3 - Sarah_daughter
     Date: 2025-11-21 14:23
     Duration: 127.3s | Events: 89 | Patterns: 5

  🎵 Session #2 - Marcus
     Date: 2025-11-21 10:15
     Duration: 302.1s | Events: 234 | Patterns: 12
```

### 3. Replay a Session

```bash
python replay.py 3
```

Watch your session replay on the Launchpad with:
- All LED colors and animations
- Pattern highlights (white flashes)
- Event logging in real-time

## Features

### 📊 Session Summaries

Get insights about any session:

```bash
python replay.py 3 --summary
```

Shows:
- Duration and timestamp
- Most pressed buttons
- Average tempo
- Detected interesting patterns
- User profile and configuration

### ⚡ Pattern Detection

BabySynth automatically detects **interesting moments**:

| Pattern Type | Description | Example |
|--------------|-------------|---------|
| **Rapid Sequence** | Quick succession of notes (< 0.3s) | Child getting excited |
| **Long Pause** | Thinking time (> 3s) | Moment of concentration |
| **Repeated Sequence** | Same pattern played again | Discovery of a musical idea |
| **Happy Accidents** | Unexpected combinations | Serendipitous exploration |

These are highlighted during playback with visual cues.

### 🎬 Playback Controls

#### Variable Speed

```bash
python replay.py 5 --speed 0.5   # Slow motion (50% speed)
python replay.py 5 --speed 2.0   # Fast forward (2x speed)
```

Speed range: 0.25x to 4.0x

#### Visual-Only Mode

Coming soon: Replay without audio for silent review.

### 📤 Export & Share

#### Export to JSON

```bash
python replay.py 5 --export session_5.json
```

Creates a shareable file with:
- All events and timestamps
- LED state changes
- Detected patterns
- Session metadata

#### ASCII Animation

Generate a text-based "video":

```bash
python replay.py 5 --ascii animation.txt
```

Creates frame-by-frame ASCII art:
```
[2.3s]
·········
·█·█·····
·········
█···█····
·········
```

Great for:
- Sharing via text/email
- Documentation
- Analysis without hardware

## User Profiles

### Setting Your Profile

Edit `main.py` to customize your profile name:

```python
user_profile = "Sarah_daughter"  # Your custom profile name
```

Suggested naming:
- **Parents:** `"ParentName_childname"` (e.g., `"Sarah_Emma"`)
- **Musicians:** Your name or stage name (e.g., `"Marcus"`, `"DJ_Synth"`)
- **Therapists:** `"TherapistName_client_ID"` (e.g., `"James_client_Alex"`)

### Filtering by Profile

```bash
python replay.py --list --profile Sarah_daughter
```

Shows only sessions for that profile.

## Technical Details

### Database

Sessions are stored in `sessions.db` (SQLite) with four tables:

- **sessions** - Metadata (duration, profile, config, patterns)
- **events** - Button presses/releases with timestamps
- **led_changes** - All LED color changes
- **patterns** - Auto-detected interesting moments

### Storage Requirements

Approximate storage per minute:
- **Light usage** (occasional presses): ~50 KB/min
- **Active play** (frequent interaction): ~200 KB/min
- **Intense performance** (rapid sequences): ~500 KB/min

A typical 5-minute session: ~1 MB

### Privacy & Data

- All data stored **locally** on your computer
- No cloud sync or external transmission
- Delete `sessions.db` to clear all recordings
- Export/share only what you choose

## Use Cases

### 👶 Developmental Tracking (Parents)

**Goal:** Observe child's motor skill development and preference patterns

```bash
# Record daily play sessions with profile
user_profile = "Mom_Emma_age3"

# Weekly review
python replay.py --list --profile Mom_Emma_age3

# Compare sessions over time
python replay.py 10 --summary  # This week
python replay.py 5 --summary   # Last week
```

**What to look for:**
- Increasing tempo (faster presses)
- Emergence of repeated patterns (intentional play)
- Longer engagement periods
- Spatial preferences (favorite buttons)

---

### 🎸 Performance Analysis (Musicians)

**Goal:** Discover unconscious patterns and refine performance

```bash
# Record practice sessions
user_profile = "Marcus"

# Analyze a session
python replay.py 15 --summary

# Slow-motion review of rapid sequences
python replay.py 15 --speed 0.25

# Export for documentation
python replay.py 15 --export performance_2025-11-21.json
```

**What to look for:**
- Embodied patterns (muscle memory sequences)
- Rhythmic variations
- Spatial navigation on grid
- Moments of hesitation vs. flow

---

### 🧑‍⚕️ Therapeutic Documentation (Therapists)

**Goal:** Track client progress and engagement markers

```bash
# Record with client identifier
user_profile = "James_client_007"

# Review session for progress notes
python replay.py 8 --summary

# Look for milestones:
# - Long pauses (processing time)
# - Repeated sequences (learning)
# - Increasing tempo (confidence)

# Export for case documentation
python replay.py 8 --export client_007_session_2025-11-21.json
```

**What to look for:**
- Changes in response timing
- Emergence of turn-taking patterns
- Self-initiated interactions
- Sustained engagement periods

---

## Advanced Usage

### Multiple Users

Track multiple people by changing profile:

```python
# In main.py, prompt for profile:
user_profile = input("Who's playing? ")
```

Or create separate launch scripts:

```bash
# launch_sarah.sh
python main.py  # with user_profile = "Sarah_daughter"

# launch_marcus.sh
python main.py  # with user_profile = "Marcus"
```

### Batch Analysis

List all sessions and pipe to analysis tools:

```bash
python replay.py --list --limit 100 > sessions_log.txt
```

### Custom Database Location

```bash
python replay.py --list --db /path/to/custom/sessions.db
```

## Coming Soon (Phase 2+)

- **Adaptive timing** based on user skill level
- **Dynamic LED animations** during playback
- **Turn-taking mode** for collaborative sessions
- **Web-based viewer** (no Launchpad required)
- **Progress visualizations** (charts, heatmaps)
- **Pattern search** ("Find all sessions with rapid sequences")

## Troubleshooting

### "No sessions found"

- Make sure you've run `python main.py` at least once
- Check that `sessions.db` exists in the project directory
- Verify database path with `--db` flag

### "No Launchpad found for playback"

- Playback requires Launchpad hardware
- Use `--summary` or `--ascii` for visualization without hardware
- Ensure Launchpad is connected and recognized

### "Session X not found"

- Run `python replay.py --list` to see available sessions
- Session IDs are sequential (1, 2, 3, ...)

### Database errors

If you encounter database corruption:

```bash
# Backup first
cp sessions.db sessions.db.backup

# Delete and recreate (WARNING: loses all data)
rm sessions.db
python main.py  # Creates new empty database
```

## API Reference

### SessionManager

```python
from session_manager import SessionManager

sm = SessionManager("sessions.db")

# Start recording
session_id = sm.start_session(user_profile="Sarah",
                              config_name="config.yaml",
                              scale="C_major",
                              model_name="ADGC")

# Record events
sm.record_button_press(x=3, y=4, note_name="C", frequency=261.63)
sm.record_button_release(x=3, y=4, note_name="C")
sm.record_led_change(x=3, y=4, color=(255, 0, 0))

# End recording
sm.end_session()

# Query
sessions = sm.list_sessions(user_profile="Sarah", limit=10)
events = sm.get_session_events(session_id)
patterns = sm.get_session_patterns(session_id)
summary = sm.get_session_summary(session_id)
```

### PlaybackEngine

```python
from playback_engine import PlaybackEngine

pe = PlaybackEngine(session_manager)
pe.init_launchpad()

# Replay
pe.play_session(session_id=5, speed=1.0, show_patterns=True)

# Display
pe.display_session_summary(session_id=5)
pe.generate_session_video_ascii(session_id=5, "output.txt")
```

## Philosophy

Session recording embodies the **values-first design** principles from the BabySynth Values Assessment:

> *"We're not building features - we're supporting ways of being."*

- **Memory** over novelty - Preserve meaningful moments
- **Reflection** over consumption - Review and learn from experience
- **Connection** over isolation - Share discoveries with others
- **Agency** over automation - User controls what to record/share
- **Attention** over metrics - Focus on what creates meaning

---

**Questions?** See `VALUES_ASSESSMENT.md` for the full design philosophy.

**Contribute:** Open an issue or PR at github.com/bilalghalib/BabySynth
