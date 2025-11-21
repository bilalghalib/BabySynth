# User Profile Launchers

Pre-configured launchers for different BabySynth use cases based on our values assessment.

## Quick Start

### For Parents 👶

Track your child's musical development:

```bash
python profiles/launch_parent.py
```

You'll be prompted for:
- Your name
- Child's name
- Child's age (optional)

Creates profile like: `Mom_Emma_age3`

**What gets tracked:**
- Discovery moments (first time pressing buttons)
- Concentration periods (long pauses)
- Coordination development (tempo changes)
- Favorite buttons and patterns

---

### For Musicians 🎸

Discover embodied patterns in your performance:

```bash
python profiles/launch_musician.py
```

You'll be prompted for:
- Artist/stage name
- Session type (practice/performance/experiment)

Creates profile like: `Marcus_practice`

**What gets tracked:**
- Rapid sequences (flow states)
- Muscle memory patterns
- Spatial navigation on grid
- Rhythmic variations

---

### For Therapists 🧑‍⚕️

Document client engagement and progress:

```bash
python profiles/launch_therapist.py
```

You'll be prompted for:
- Therapist name
- Client ID/pseudonym
- Session notes

Creates profile like: `James_client_007`

**What gets tracked:**
- Response timing (engagement signals)
- Processing pauses (concentration)
- Learning patterns (repetition)
- Progress milestones

---

## After Your Session

Each launcher provides a customized summary when you stop (Ctrl+C).

**View all sessions for your profile:**
```bash
python replay.py --list --profile YourProfileName
```

**Review a specific session:**
```bash
python replay.py SESSION_ID --summary
```

**Replay on Launchpad:**
```bash
python replay.py SESSION_ID
```

## Customization

You can edit these launchers to:
- Change default configurations
- Add custom session notes
- Modify scale/model settings
- Adjust output messages

Copy and modify as needed for your use case!

## Values Served

These profiles are designed around **attention policies** - what each user type pays attention to:

- **Parents:** Moments of discovery, physical development, shared presence
- **Musicians:** Embodied patterns, creative constraints, performance honesty
- **Therapists:** Subtle signals, client-paced timing, judgment-free agency

See `VALUES_ASSESSMENT.md` for the full philosophy.
