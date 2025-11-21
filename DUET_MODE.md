## Duet Mode & Turn-Taking 🎵🎵

> **✨ NEW IN PHASE 4!** Play music together with intelligent turn-taking and visual feedback.

## What is Duet Mode?

Duet mode transforms BabySynth into a **collaborative instrument** for two players. Perfect for:
- **👶 Parent-child bonding** - Take turns making music together
- **🎸 Collaborative composition** - Build pieces together
- **🧑‍⚕️ Therapeutic interaction** - Structured turn-taking for therapy
- **🎓 Music education** - Call-and-response exercises
- **🎪 Performance duets** - Live collaborative shows

## Quick Start

```bash
python profiles/launch_duet.py
```

You'll be prompted for:
1. Player names
2. Turn-taking mode
3. Optional alternate config (for A/B switching)

Then start playing! The **top row shows whose turn it is**.

---

## 🎮 Turn-Taking Modes

### 1. Free Play 🎉
**Both players can play anytime**

- No restrictions
- Great for jamming together
- Top row shows both players lit
- Perfect for collaborative improvisation

**When to use:**
- Parent and child exploring together
- Two musicians creating freely
- Warm-up before structured practice

---

### 2. Strict Turns 📋
**Only the current player can press buttons**

- One player at a time
- Top row shows current player (red=P1, blue=P2)
- Other player's presses are blocked with visual feedback
- Manual turn switching

**When to use:**
- Structured music lessons
- Teaching patience and listening
- Building a piece one layer at a time
- Therapeutic sessions requiring clear boundaries

**How it works:**
- Player 1 (left side) plays their turn
- When done, press a control button or wait
- Player 2 (right side) takes their turn
- Continue alternating

---

### 3. Call & Response 💬
**Musical conversation mode**

- Player 1 plays a "call" (question)
- Player 2 plays a "response" (answer)
- Automatic turn switching after 2 seconds of silence
- Top row pulses on turn change

**When to use:**
- Music therapy (building social interaction)
- Jazz/blues call-response practice
- Teaching musical phrases
- Creative back-and-forth composition

**Example session:**
1. Parent plays: C-D-E (simple ascending)
2. Child responds: E-D-C (descending mirror!)
3. Parent: C-C-G-G (rhythmic pattern)
4. Child: A-A-E-E (variation!)

---

### 4. Timed Turns ⏱️
**Fair sharing - each gets 10 seconds**

- Automatic timer for each turn
- Visual countdown (top row brightness?)
- Forces quick thinking and sharing
- Great for young children learning to share

**When to use:**
- Fairness with young kids
- Fast-paced creative sessions
- Teaching time management in music
- High-energy performances

---

## 🗺️ Grid Zones

Players are assigned zones on the grid:

```
         Player 1     Gap      Player 2
         (Left)                 (Right)
      ┌─────────┬────┬─────────┐
  0   │   🔴    │    │   🔵    │  ← Turn indicators
      ├─────────┼────┼─────────┤
  1-8 │ Notes   │    │ Notes   │  ← Playing area
      │ for P1  │    │ for P2  │
      └─────────┴────┴─────────┘
        x: 0-3        x: 5-8
```

**Player 1 Zone:** Left half (x: 0-3)
- Warm colors (red, orange, yellow)
- Visual identity: Red indicator

**Player 2 Zone:** Right half (x: 5-8)
- Cool colors (cyan, blue, purple)
- Visual identity: Blue indicator

**Middle column (x: 4):** Neutral/shared space

---

## 📊 Visual Feedback

### Turn Indicators (Top Row, y=0)

| Mode | Indicator Behavior |
|------|-------------------|
| **Free Play** | Both sides lit (red & blue) |
| **Strict Turns** | Current player's side lit, pulses on change |
| **Call-Response** | Alternates with pulse animation |
| **Timed Turns** | Current player's side, fades as time runs out |

### Invalid Press Feedback

If you press during the other player's turn:
- ⚠️ Console message: "Not [Name]'s turn!"
- ✨ Visual: Current player's zone pulses (reminder)
- 🚫 Sound: Not played (blocked)

### Turn Change Feedback

When turns switch:
- 🔄 Console: "Turn: Player 1 → Player 2"
- 💫 LED: Pulse animation in new player's color
- 🎵 Optional: Turn change sound (future)

---

## ⚙️ Configuration

### Custom Turn Duration

Edit in `launch_duet.py`:

```python
turn_taker.set_turn_duration(15.0)  # 15 seconds per turn
```

### Custom Grid Zones

```python
# Top/bottom instead of left/right
turn_taker.set_player_zones(GridZone.TOP_HALF, GridZone.BOTTOM_HALF)
```

### Custom Player Colors

```python
turn_taker.set_player_colors(
    (255, 0, 255),  # Magenta for player 1
    (0, 255, 255)   # Cyan for player 2
)
```

### Disable Turn-Taking

Set mode to FREE_PLAY in the launcher, or just use regular `python main.py`

---

## 🎬 Use Cases & Stories

### 👶 Sarah & Emma (Parent-Child Bonding)

**Scenario:** Teaching Emma (age 3) about turn-taking

**Setup:**
```bash
python profiles/launch_duet.py
> Player 1: Mom
> Player 2: Emma
> Mode: 3 (Call & Response)
```

**Session flow:**
1. Mom plays simple pattern: C-C-C (three reds)
2. Emma watches, top row shows it's her turn (blue)
3. Emma presses blue buttons randomly: G-A-G
4. Mom: "Great! Let's try again..."
5. Mom: E-E-E (three blues on her side)
6. Emma: Tries to match: E-E-E!

**Result:**
- Emma learns turn-taking through music
- Visual cues (top row) help her understand whose turn
- Session recorded shows developmental progress
- Mom can replay to see patterns emerge

---

### 🎸 Marcus & Alex (Collaborative Composition)

**Scenario:** Two musicians building a live looping piece

**Setup:**
```bash
python profiles/launch_duet.py
> Player 1: Marcus
> Player 2: Alex
> Mode: 1 (Free Play)
```

**Session flow:**
1. Both start with bass notes (left side)
2. Marcus holds sustained notes (breathing animation)
3. Alex adds rhythmic patterns on top
4. They build layers together
5. Marcus hits (6,0) to cycle to new config mid-performance
6. New sounds, new possibilities!

**Result:**
- Free flowing collaboration
- Hot-reload allows live soundscape changes
- Session recorded captures the entire composition
- Can replay at 0.5x speed to study interactions

---

### 🧑‍⚕️ James & Client (Music Therapy)

**Scenario:** Building social interaction skills

**Setup:**
```bash
python profiles/launch_duet.py
> Player 1: James
> Player 2: Client_007
> Mode: 3 (Call & Response)
```

**Session flow:**
1. James plays simple 2-note pattern
2. Waits (top row shows client's turn)
3. Client responds after 5 seconds (documented!)
4. James mirrors client's pattern back
5. Client initiates their own pattern!
6. Turn-taking becomes natural conversation

**Result:**
- Visual turn indicators reduce verbal prompting
- Automatic switching removes pressure
- Response times documented in session
- Patterns show increasing social engagement

---

## 📈 Turn Statistics

After each duet session, see:

```
📊 Turn Statistics:
   Player 1 (Mom):
      Turns: 12
      Total time: 145.3s
      Avg turn: 12.1s

   Player 2 (Emma):
      Turns: 11
      Total time: 133.7s
      Avg turn: 12.2s
```

**What to track:**
- **Turn count** - Did both players participate equally?
- **Avg turn duration** - Is one player dominating?
- **Response time** - How quickly does player 2 respond? (future)
- **Pattern complexity** - Notes per turn, variety (future)

---

## 🔥 Hot-Reload Configs (Phase 5)

### Live Config Switching

**Control Buttons (top-right corner):**

| Position | Function | Description |
|----------|----------|-------------|
| **(8, 0)** | 🔄 **Toggle A/B** | Switch between two configs instantly |
| **(7, 0)** | ♻️ **Reload** | Reload current config from disk |
| **(6, 0)** | 🔁 **Cycle** | Cycle through all configs in `configs/` |

### Example: Live Performance

**Setup:**
```bash
python profiles/launch_duet.py
> Alternate config: configs/duet_drums.yaml
```

**During performance:**
1. Start with melodic config (duet_left_right.yaml)
2. Build a musical idea together
3. Press **(8, 0)** - instant switch to drum kit!
4. Continue with rhythmic variation
5. Press **(6, 0)** - cycle to another config
6. Explore new sounds without stopping

**Visual feedback:**
- Smooth fade-out of old colors
- Brief pause (0.3s)
- Fade-in of new colors
- Top indicators maintain turn state

### Automatic File Watching

The duet launcher automatically watches your config file for changes:

**Workflow:**
1. Start duet session
2. Edit `config.yaml` in another editor
3. Save the file
4. **Automatic reload!** (within 1 second)
5. Console: "✨ Config reloaded: config.yaml"
6. Continue playing with new settings

**Great for:**
- Live coding performances
- Iterating on color schemes
- Adjusting animation speeds
- Testing new layouts

### Error Handling

If config reload fails:
- ❌ Console: "Config reload failed: [error]"
- 🔄 Previous config automatically restored
- Session continues uninterrupted
- History shows failure for debugging

---

## 🔧 Advanced Features

### Turn Change Callbacks

Hook into turn events:

```python
def on_turn_change(old_player, new_player):
    print(f"Turn changed: {old_player} → {new_player}")
    # Trigger animation, sound, etc.

turn_taker.add_turn_change_callback(on_turn_change)
```

### Config Reload Callbacks

React to config changes:

```python
def on_config_reload(path, success):
    if success:
        print(f"Loaded: {path}")
        # Update UI, notify players
    else:
        print(f"Failed: {path}")
        # Show error, restore backup

config_reloader.add_reload_callback(on_config_reload)
```

### Custom Zones

Define your own zones:

```python
# Checkerboard pattern
def is_in_player1_zone(x, y):
    return (x + y) % 2 == 0

# Override zone checking
turn_taker.is_in_zone = is_in_player1_zone
```

---

## 🎓 Teaching Scenarios

### Lesson 1: Introduction to Turn-Taking
**Age: 3-5 years**

1. **Mode:** Strict Turns
2. **Duration:** 5 minutes
3. **Goal:** Understand "my turn" vs "your turn"
4. **Activity:**
   - Parent plays one note, waits
   - Child copies the note
   - Celebrate successful turn-taking!

**Progress indicators:**
- Child waits for top row to show their color
- Decreasing invalid presses over time
- Initiating their own patterns

---

### Lesson 2: Call & Response
**Age: 6-10 years**

1. **Mode:** Call-Response
2. **Duration:** 10 minutes
3. **Goal:** Musical conversation
4. **Activity:**
   - Teacher plays 2-3 note "question"
   - Student plays 2-3 note "answer"
   - Build on each other's ideas

**Advanced:**
- Try to match rhythm
- Answer in opposite direction (ascending→descending)
- Use same notes, different rhythm

---

### Lesson 3: Collaborative Composition
**Age: 10+ / Adults**

1. **Mode:** Free Play
2. **Duration:** 15-20 minutes
3. **Goal:** Create together
4. **Activity:**
   - Both players build layers
   - One holds bass (left hand)
   - Other plays melody (right hand)
   - Switch roles dynamically

**Recording:**
- Save session
- Replay together
- Identify favorite moments
- Export for sharing

---

## 🐛 Troubleshooting

### "Turn indicator not showing"

Check:
1. Is duet mode actually enabled?
2. Top row (y=0) not blocked by config layout
3. Try: `turn_taker.update_turn_indicator()`

### "Both players can always press"

- Mode is set to FREE_PLAY
- Change mode: `turn_taker.set_mode(TurnMode.STRICT_TURNS)`

### "Config won't reload"

Check:
1. Config file exists and is valid YAML
2. File watcher is running: `config_reloader.start_watching()`
3. Check console for error messages

### "Turns not switching automatically"

- Only TIMED_TURNS and CALL_RESPONSE auto-switch
- STRICT_TURNS requires manual switching
- Check minimum turn duration (default: 2s)

---

## 🌟 Philosophy

From the values assessment:

> **James (Therapist):** "TIMING that emerges at client's own pace"

> **Sarah (Parent):** "INVITATIONS she makes to share experiences"

Duet mode serves these by:

1. **Patient waiting** - No pressure to hurry
2. **Clear visual cues** - Less verbal intervention needed
3. **Structured freedom** - Safe space for interaction
4. **Documented progress** - Turn stats show engagement growth
5. **Flexible pacing** - Multiple modes for different needs

**Turn-taking isn't just about fairness - it's about creating space for musical dialogue.** 🎵💬🎵

---

## 📚 Related Documentation

- **SESSION_RECORDING.md** - Session recording includes turn stats
- **LED_ANIMATIONS.md** - Turn indicators use pulse/fade animations
- **VALUES_ASSESSMENT.md** - Why we built duet mode

---

## 🚀 What's Next?

Future duet enhancements:
- **Audio turn cues** - Sound when turn changes
- **Progressive difficulty** - Longer patterns as skill grows
- **Score keeping** - Points for matching, creativity
- **Video export** - Visual playback of duet sessions
- **3+ players** - Not just duets!

---

**Try it now:**

```bash
# Start a duet!
python profiles/launch_duet.py

# Or regular play with hot-reload
python main.py  # Then edit config.yaml - auto reloads!
```

**Make music together. Take turns. Build something beautiful. 🎵✨🎵**
