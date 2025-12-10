# Percussion Sample Download Guide

You have **3 options** for downloading real tabla and daf samples from Freesound.org:

## Current Status

✓ **Placeholder samples are already installed!**
- All 9 sound files are in place (tabla and daf directories)
- The demo will work right now with these placeholders
- They're copies of existing baby sounds - good for testing

```bash
# Try it now!
python demos/daf_tabla.py
```

---

## Option 1: Quick Download (Recommended) ⚡

**No API key needed!** Downloads curated samples directly.

```bash
python quick_download_samples.py
```

**Features:**
- Downloads pre-selected high-quality samples
- No authentication required
- Fast and simple
- Downloads as MP3 (works fine with demo)

**Downloaded samples:**
- Tabla strokes from ajaysm's pack
- Frame drum samples from Metzik
- All Creative Commons licensed

---

## Option 2: Intelligent Scraper (Best Quality) 🔍

Uses BeautifulSoup to search and find the best samples automatically.

```bash
python scrape_percussion_samples.py
```

**Features:**
- Intelligently searches for each stroke type
- Tries multiple search terms per sample
- Downloads the highest-rated results
- No API key needed
- May take 2-3 minutes (searches + downloads)

**How it works:**
1. Searches Freesound for each stroke: "tabla na", "tabla tin", etc.
2. Scrapes search results to find sound IDs
3. Extracts preview download URLs
4. Downloads HQ MP3 previews
5. Saves with correct filenames

---

## Option 3: With Freesound API (Full Access) 🔑

Most control and access to full-quality downloads.

```bash
python download_percussion_samples.py
```

**Setup:**
1. Get API key: https://freesound.org/apiv2/apply/
2. Set environment variable:
   ```bash
   export FREESOUND_API_KEY=your_key_here
   ```
3. Run the script

**Benefits:**
- Access to full-quality files (not just previews)
- Search any collection
- Download entire packs
- Programmatic access to metadata

---

## After Downloading

### If you downloaded MP3 files:

**Option A:** Use MP3 directly (simpleaudio supports MP3)
```bash
# Update config to use .mp3 extension
sed -i '' 's/\.wav/.mp3/g' configs/daf_tabla.yaml

# Run demo
python demos/daf_tabla.py
```

**Option B:** Convert to WAV (better quality)
```bash
# Install ffmpeg if needed
brew install ffmpeg  # macOS
# sudo apt install ffmpeg  # Linux

# Convert all files
for f in sounds/tabla/*.mp3; do
    ffmpeg -i "$f" "${f%.mp3}.wav"
done

for f in sounds/daf/*.mp3; do
    ffmpeg -i "$f" "${f%.mp3}.wav"
done
```

---

## Manual Download (Highest Quality)

For the absolute best samples, download manually:

### Tabla Strokes Pack
**Best source:** https://freesound.org/people/ajaysm/packs/9828/

This pack contains 17 individual tabla strokes:
- Download entire pack as ZIP
- Extract individual files
- Rename and place in `sounds/tabla/`

### Individual Samples

**Tabla:**
- https://freesound.org/people/ajaysm/sounds/171913/ (te stroke)
- https://freesound.org/people/mmiron/sounds/130424/ (ke stroke)
- https://freesound.org/people/sankalp/sounds/153268/ (multiple bols)

**Daf/Frame Drum:**
- https://freesound.org/people/Metzik/sounds/244152/ (Mazhar frame drum)
- https://freesound.org/search/?q=doumbek (similar Middle Eastern drums)
- https://freesound.org/search/?q=riq (frame drum with jingles)

---

## Comparison

| Method | Quality | Speed | Ease | API Key |
|--------|---------|-------|------|---------|
| **Quick Download** | Good (HQ MP3) | Fast | Easy | No |
| **Scraper** | Good (HQ MP3) | Medium | Easy | No |
| **API** | Best (Full WAV) | Fast | Medium | Yes |
| **Manual** | Best | Slow | Hard | No |

---

## Recommended Workflow

**For quick testing:**
```bash
# Already done! Use the placeholder files
python demos/daf_tabla.py
```

**For better quality:**
```bash
# Run the scraper
python scrape_percussion_samples.py

# Files will be downloaded as MP3
# Convert to WAV if desired (see above)
```

**For best experience:**
1. Go to https://freesound.org/people/ajaysm/packs/9828/
2. Download the "Tabla Strokes" pack (ZIP)
3. Extract and organize files
4. Enjoy authentic tabla samples!

---

## Troubleshooting

**"Connection error" or "Timeout":**
- Check internet connection
- Freesound.org might be down - try again later
- Use VPN if blocked in your region

**"No results found":**
- Search terms might be too specific
- Try the quick download script instead
- Or download manually from links above

**"Script hangs":**
- Press Ctrl+C to cancel
- Re-run with fewer samples
- Use quick_download_samples.py instead

**Files are distorted:**
- MP3 previews are compressed (okay for testing)
- Convert to WAV for better quality
- Or download full files with API key

---

## License Info

All samples from Freesound.org are Creative Commons licensed:
- **CC0**: Public domain, use freely
- **CC-BY**: Attribution required
- **CC-BY-NC**: Non-commercial only

Check individual sound pages for specific licenses.

**Attribution format:**
```
Sound "tabla_te" by ajaysm (freesound.org/s/171913/)
Licensed under CC-BY 3.0
```

---

## Next Steps

1. Choose a download method above
2. Run the script
3. Test the demo: `python demos/daf_tabla.py`
4. Try different layouts: `--layout TABLA_FULL` or `--layout DAF_FULL`
5. Record and playback patterns!

For more info, see: `sounds/DAF_TABLA_SOUNDS.md`
