#!/usr/bin/env python3
"""
Quick download of percussion samples - No API key required!
Uses direct preview links from Freesound
"""

import os
import sys
import requests
from pathlib import Path

# Direct preview links to good samples (no auth required!)
SAMPLES = {
    'tabla': {
        'na.wav': {
            'url': 'https://freesound.org/data/previews/171/171913_1015240-hq.mp3',
            'name': 'Tabla te stroke by ajaysm (using as Na)',
            'source': 'https://freesound.org/people/ajaysm/sounds/171913/'
        },
        'tin.wav': {
            'url': 'https://freesound.org/data/previews/130/130424_1648170-hq.mp3',
            'name': 'Tabla ke stroke by mmiron (using as Tin)',
            'source': 'https://freesound.org/people/mmiron/sounds/130424/'
        },
        'te.wav': {
            'url': 'https://freesound.org/data/previews/171/171913_1015240-hq.mp3',
            'name': 'Tabla te stroke by ajaysm',
            'source': 'https://freesound.org/people/ajaysm/sounds/171913/'
        },
        'ge.wav': {
            'url': 'https://freesound.org/data/previews/153/153268_2729678-hq.mp3',
            'name': 'Tabla bols by sankalp (using as Ge)',
            'source': 'https://freesound.org/people/sankalp/sounds/153268/'
        },
        'ka.wav': {
            'url': 'https://freesound.org/data/previews/130/130424_1648170-hq.mp3',
            'name': 'Tabla ke stroke by mmiron (using as Ka)',
            'source': 'https://freesound.org/people/mmiron/sounds/130424/'
        },
        'dha.wav': {
            'url': 'https://freesound.org/data/previews/153/153268_2729678-hq.mp3',
            'name': 'Tabla bols by sankalp (using as Dha)',
            'source': 'https://freesound.org/people/sankalp/sounds/153268/'
        }
    },
    'daf': {
        'dum.wav': {
            'url': 'https://freesound.org/data/previews/244/244152_1428770-hq.mp3',
            'name': 'Frame drum (Mazhar) by Metzik',
            'source': 'https://freesound.org/people/Metzik/sounds/244152/'
        },
        'tak.wav': {
            'url': 'https://freesound.org/data/previews/244/244152_1428770-hq.mp3',
            'name': 'Frame drum (Mazhar) by Metzik',
            'source': 'https://freesound.org/people/Metzik/sounds/244152/'
        },
        'roll.wav': {
            'url': 'https://freesound.org/data/previews/244/244152_1428770-hq.mp3',
            'name': 'Frame drum (Mazhar) by Metzik',
            'source': 'https://freesound.org/people/Metzik/sounds/244152/'
        }
    }
}


def download_file(url, output_path, description):
    """Download a file from URL"""
    try:
        print(f"\n  Downloading: {description}")
        print(f"  From: {url}")

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Save the file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        file_size = len(response.content) / 1024  # KB
        print(f"  ✓ Saved to: {output_path} ({file_size:.1f} KB)")
        return True

    except requests.RequestException as e:
        print(f"  ✗ Error downloading: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False


def main():
    print("="*70)
    print("  QUICK PERCUSSION SAMPLES DOWNLOAD (No API Key Required!)")
    print("="*70)
    print("\nThis script downloads free percussion samples from Freesound.org")
    print("All samples are licensed under Creative Commons licenses.")
    print()

    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library not found.")
        print("Please install it: pip install requests")
        sys.exit(1)

    # Create directories
    os.makedirs('sounds/tabla', exist_ok=True)
    os.makedirs('sounds/daf', exist_ok=True)
    print("✓ Created directories: sounds/tabla/ and sounds/daf/")

    # Download samples
    total_files = sum(len(files) for files in SAMPLES.values())
    downloaded = 0
    skipped = 0
    failed = 0

    for category, files in SAMPLES.items():
        print(f"\n{'='*70}")
        print(f"  {category.upper()} SAMPLES")
        print(f"{'='*70}")

        for filename, info in files.items():
            output_path = f"sounds/{category}/{filename}"

            # Check if file already exists
            if os.path.exists(output_path):
                print(f"\n✓ {filename}: Already exists, skipping...")
                skipped += 1
                continue

            print(f"\n[{downloaded + skipped + failed + 1}/{total_files}] {filename}")

            # Download the file (as MP3)
            mp3_path = output_path.replace('.wav', '.mp3')
            if download_file(info['url'], mp3_path, info['name']):
                print(f"  Source: {info['source']}")
                downloaded += 1
            else:
                failed += 1

    # Summary
    print("\n" + "="*70)
    print("  DOWNLOAD SUMMARY")
    print("="*70)
    print(f"\n  ✓ Downloaded: {downloaded} files")
    if skipped > 0:
        print(f"  ⊙ Skipped: {skipped} files (already exist)")
    if failed > 0:
        print(f"  ✗ Failed: {failed} files")

    print("\n" + "-"*70)
    print("  IMPORTANT NOTES")
    print("-"*70)
    print("\n1. Files are downloaded as MP3 (HQ preview quality)")
    print("   - These work fine with the demo!")
    print("   - Or convert to WAV: ffmpeg -i file.mp3 file.wav")

    print("\n2. Update the config to use MP3 files:")
    print("   Edit configs/daf_tabla.yaml and change .wav to .mp3")
    print("   OR convert files to WAV using the conversion script below")

    print("\n3. These are the same files used multiple times")
    print("   - For best experience, download individual strokes from:")
    print("     https://freesound.org/people/ajaysm/packs/9828/")
    print("     (Tabla Strokes pack - 17 individual recordings)")

    print("\n4. License: All samples are CC licensed from Freesound.org")
    print("   - Attribution required for commercial use")
    print("   - See individual source URLs above")

    print("\n" + "="*70)
    print("  NEXT STEPS")
    print("="*70)
    print("\nOption A: Use MP3 files directly")
    print("  1. Update configs/daf_tabla.yaml (change .wav → .mp3)")
    print("  2. Run: python demos/daf_tabla.py")

    print("\nOption B: Convert to WAV (better quality)")
    print("  Run the conversion script:")
    print("  python convert_samples_to_wav.py")

    print("\nOption C: Download better samples manually")
    print("  See: sounds/DAF_TABLA_SOUNDS.md")

    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user.")
        sys.exit(0)
