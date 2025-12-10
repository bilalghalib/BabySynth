# Daf & Tabla Sound Files Guide

This guide explains how to set up sound files for the Daf/Tabla percussion demo.

## Required Sound Files

The daf_tabla.yaml configuration expects the following sound files:

### Tabla Sounds (sounds/tabla/)
- `na.wav` - Open stroke on rim (Na/Ta)
- `tin.wav` - Closed stroke on rim (Tin)
- `te.wav` - Middle stroke (Te/Ti)
- `ge.wav` - Open bass (Ge/Ga from bayan)
- `ka.wav` - Bass slap (Ka from bayan)
- `dha.wav` - Combined stroke (Na + Ge played together)

### Daf Sounds (sounds/daf/)
- `dum.wav` - Bass center stroke (Dum/Doom)
- `tak.wav` - Treble rim stroke (Tak)
- `roll.wav` - Finger roll technique

## Directory Structure

Create the following directory structure:

```
sounds/
├── tabla/
│   ├── na.wav
│   ├── tin.wav
│   ├── te.wav
│   ├── ge.wav
│   ├── ka.wav
│   └── dha.wav
└── daf/
    ├── dum.wav
    ├── tak.wav
    └── roll.wav
```

## Where to Find Sound Samples

### Option 1: Free Sample Libraries

**Freesound.org** (requires free account)
- Search for "tabla" or "daf" samples
- Filter by: Creative Commons license, WAV format
- Download individual stroke samples

**Tabla Samples:**
- https://freesound.org/search/?q=tabla
- Look for samples labeled with specific stroke names (na, tin, te, ge, ka, dha)

**Daf Samples:**
- https://freesound.org/search/?q=daf
- https://freesound.org/search/?q=frame+drum

### Option 2: Sample Pack Websites

**Free:**
- **99Sounds** - https://99sounds.org (search for percussion)
- **Bedroom Producers Blog** - Free sample packs
- **Splice** - Free tier includes some percussion samples

**Paid (high quality):**
- **Sampleism** - Professional tabla libraries
- **8Dio** - Ethnic percussion collections
- **Native Instruments** - Kontakt libraries (if you own Kontakt)

### Option 3: YouTube Audio Library
- YouTube Audio Library has some percussion samples
- Download and extract the specific strokes you need using audio editing software

### Option 4: Record Your Own
If you have access to a daf or tabla:
1. Record each stroke separately
2. Trim to remove silence before/after
3. Normalize the volume
4. Export as WAV (16-bit, 44.1kHz recommended)

## Audio Format Requirements

- **Format:** WAV (preferred) or MP3
- **Sample Rate:** 44.1kHz or 48kHz
- **Bit Depth:** 16-bit or 24-bit
- **Channels:** Mono or Stereo (mono recommended for percussion)
- **Length:** 0.5 to 2 seconds per sample (trim off silence)

## Preparing Your Samples

### Using Audacity (free audio editor):

1. **Import your sample**
2. **Trim silence:**
   - Select the audio
   - Effect → Truncate Silence
   - Or manually trim start/end
3. **Normalize volume:**
   - Effect → Normalize
   - Set to -3dB to prevent clipping
4. **Export:**
   - File → Export → Export as WAV
   - Choose 16-bit PCM
   - Save with the appropriate filename

### Using FFmpeg (command line):

```bash
# Convert MP3 to WAV
ffmpeg -i input.mp3 output.wav

# Normalize audio
ffmpeg -i input.wav -af "loudnorm" output.wav

# Trim silence from start and end
ffmpeg -i input.wav -af "silenceremove=1:0:-50dB" output.wav
```

## Quick Start with Placeholder Sounds

If you want to test the demo immediately without real samples:

1. Create the directories:
```bash
mkdir -p sounds/tabla sounds/daf
```

2. Use the existing sounds in the sounds/ directory as placeholders:
```bash
# Copy existing sounds as placeholders
cp sounds/upla.wav sounds/tabla/na.wav
cp sounds/beezoo.wav sounds/tabla/tin.wav
cp sounds/hopla.wav sounds/tabla/te.wav
cp sounds/bisou.wav sounds/tabla/ge.wav
cp sounds/yallah.wav sounds/tabla/ka.wav
cp sounds/upla.wav sounds/tabla/dha.wav
cp sounds/beezoo.wav sounds/daf/dum.wav
cp sounds/hopla.wav sounds/daf/tak.wav
cp sounds/bisou.wav sounds/daf/roll.wav
```

3. Run the demo to test functionality
4. Replace with real percussion samples later

## Traditional Stroke Descriptions

### Tabla Strokes

**Right Hand (Dayan - treble drum):**
- **Na/Ta** - Open resonant stroke on the edge/rim
- **Tin** - Closed stroke on the rim, dampened with fingertips
- **Te/Ti** - Stroke on the center/maidan (middle area)
- **Tun** - Bass stroke on the center

**Left Hand (Bayan - bass drum):**
- **Ge/Ga** - Open bass stroke in center, palm lifted for resonance
- **Ke** - High-pitched stroke, palm pressed
- **Ka** - Sharp slap with palm

**Combined:**
- **Dha** - Na + Ge played simultaneously
- **Dhin** - Tin + Ge played simultaneously

### Daf Strokes

- **Dum/Doom** - Deep bass stroke in the center with fingertips
- **Tak** - Sharp high stroke on the rim/edge
- **Ka** - Slap stroke
- **Roll** - Rapid finger roll around the rim
- **Sak** - Muted stroke

## Recording Tips

If recording your own samples:

1. **Environment:** Record in a quiet room, away from echo
2. **Microphone:** Place 6-12 inches from the drum
3. **Consistency:** Record each stroke type with similar force
4. **Multiple takes:** Record 3-5 takes of each stroke, pick the best
5. **Labeling:** Name files clearly (na_1.wav, na_2.wav for variations)

## Troubleshooting

**"File not found" error:**
- Verify the directory structure matches exactly
- Check that file names are lowercase and match the config
- Ensure files are in WAV format

**No sound playing:**
- Check that files aren't corrupted
- Verify sample rate is supported (44.1kHz or 48kHz)
- Test files in a media player first

**Distorted/clipping sound:**
- Normalize audio levels
- Check that bit depth is 16 or 24-bit
- Reduce volume in the audio editor before exporting

## Next Steps

Once you have the sound files set up:

1. Place all files in the correct directories
2. Run the demo: `python demos/daf_tabla.py`
3. Or use with main app: `python main_web.py` and load the daf_tabla config
4. Experiment with different layouts in the config file

## Resources

- **Tabla Tutorial:** https://www.taalmala.com (learn stroke techniques)
- **Daf Tutorial:** YouTube - Search "daf tutorial basic strokes"
- **Sample Editing:** Audacity - https://www.audacityteam.org
- **More Samples:** https://freesound.org, https://99sounds.org
