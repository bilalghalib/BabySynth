#!/usr/bin/env python3
"""
Download Tabla and Daf samples from Freesound.org
Requires a free Freesound API key
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# Freesound API configuration
FREESOUND_API_KEY = os.environ.get('FREESOUND_API_KEY', '')
BASE_URL = 'https://freesound.org/apiv2'

# Sample mappings - best samples found on Freesound
TABLA_SAMPLES = {
    'na.wav': {
        'search': 'tabla na stroke',
        'sound_id': 171913,  # ajaysm's te stroke (we'll use as na)
        'description': 'Open rim stroke (Na)'
    },
    'tin.wav': {
        'search': 'tabla tin stroke',
        'sound_id': None,  # Will search
        'description': 'Closed rim stroke (Tin)'
    },
    'te.wav': {
        'search': 'tabla te stroke',
        'sound_id': 171913,  # ajaysm's te stroke
        'description': 'Middle stroke (Te)'
    },
    'ge.wav': {
        'search': 'tabla ge bass',
        'sound_id': None,
        'description': 'Open bass (Ge)'
    },
    'ka.wav': {
        'search': 'tabla ka stroke',
        'sound_id': 130424,  # mmiron's ke_2.wav
        'description': 'Bass slap (Ka)'
    },
    'dha.wav': {
        'search': 'tabla dha stroke',
        'sound_id': None,
        'description': 'Combined stroke (Dha)'
    }
}

DAF_SAMPLES = {
    'dum.wav': {
        'search': 'daf dum frame drum bass',
        'sound_id': None,
        'description': 'Bass center stroke (Dum)'
    },
    'tak.wav': {
        'search': 'daf tak frame drum',
        'sound_id': None,
        'description': 'Treble rim stroke (Tak)'
    },
    'roll.wav': {
        'search': 'frame drum roll',
        'sound_id': 244152,  # Metzik's Mazhar playing
        'description': 'Finger roll'
    }
}


def get_api_key():
    """Get Freesound API key from user"""
    if FREESOUND_API_KEY:
        return FREESOUND_API_KEY

    print("\n" + "="*60)
    print("  FREESOUND API KEY REQUIRED")
    print("="*60)
    print("\nTo download samples, you need a free Freesound API key.")
    print("\nSteps to get your API key:")
    print("1. Go to: https://freesound.org/")
    print("2. Create a free account (or login)")
    print("3. Go to: https://freesound.org/apiv2/apply/")
    print("4. Fill out the form (Name: BabySynth, Description: Downloading percussion samples)")
    print("5. You'll receive an API key instantly")
    print("\nOnce you have your API key, either:")
    print("  - Set environment variable: export FREESOUND_API_KEY=your_key_here")
    print("  - Or paste it below")
    print("\n" + "="*60 + "\n")

    api_key = input("Enter your Freesound API key (or 'skip' to see alternative options): ").strip()

    if api_key.lower() == 'skip':
        return None

    return api_key


def search_sounds(query, api_key, max_results=5):
    """Search for sounds on Freesound"""
    url = f"{BASE_URL}/search/text/"
    params = {
        'query': query,
        'token': api_key,
        'fields': 'id,name,description,url,previews,download',
        'filter': 'duration:[0.1 TO 3]',  # Short samples only
        'sort': 'downloads_desc'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()
        return results.get('results', [])[:max_results]
    except Exception as e:
        print(f"Error searching: {e}")
        return []


def download_sound(sound_id, output_path, api_key):
    """Download a sound file from Freesound"""
    # Get sound info
    info_url = f"{BASE_URL}/sounds/{sound_id}/"
    params = {'token': api_key}

    try:
        # Get sound metadata
        response = requests.get(info_url, params=params)
        response.raise_for_status()
        sound_info = response.json()

        # Use preview URL (doesn't require OAuth)
        preview_url = sound_info['previews']['preview-hq-mp3']

        print(f"  Downloading: {sound_info['name']}")
        print(f"  By: {sound_info['username']}")

        # Download the file
        audio_response = requests.get(preview_url)
        audio_response.raise_for_status()

        # Save as MP3 first
        mp3_path = output_path.replace('.wav', '.mp3')
        with open(mp3_path, 'wb') as f:
            f.write(audio_response.content)

        print(f"  ✓ Downloaded to: {mp3_path}")
        print(f"    (Note: Downloaded as MP3 - convert to WAV if needed)")

        return True

    except Exception as e:
        print(f"  ✗ Error downloading sound {sound_id}: {e}")
        return False


def manual_download_instructions():
    """Print manual download instructions"""
    print("\n" + "="*60)
    print("  MANUAL DOWNLOAD INSTRUCTIONS")
    print("="*60)
    print("\nHere are direct links to download the samples manually:")
    print("\nTABLA SAMPLES:")
    print("1. Go to: https://freesound.org/people/ajaysm/packs/9828/")
    print("   - Download the 'Tabla Strokes' pack (17 strokes)")
    print("   - Extract and rename files as needed:")
    print("     te.wav → sounds/tabla/te.wav")
    print("     na.wav → sounds/tabla/na.wav")
    print("     etc.")

    print("\n2. Individual samples:")
    print("   https://freesound.org/people/ajaysm/sounds/171913/ (te stroke)")
    print("   https://freesound.org/people/mmiron/sounds/130424/ (ke stroke)")
    print("   https://freesound.org/people/sankalp/sounds/153268/ (multiple bols)")

    print("\nDAF/FRAME DRUM SAMPLES:")
    print("   https://freesound.org/people/Metzik/sounds/244152/ (Mazhar/frame drum)")

    print("\nAlternative sources:")
    print("   - https://99sounds.org (search: percussion)")
    print("   - https://freesound.org/search/?q=tabla&f=duration:[0+TO+3]")

    print("\nAfter downloading:")
    print("1. Place files in sounds/tabla/ and sounds/daf/")
    print("2. Convert MP3 to WAV if needed:")
    print("   ffmpeg -i input.mp3 output.wav")
    print("\n" + "="*60 + "\n")


def main():
    print("="*60)
    print("  PERCUSSION SAMPLES DOWNLOADER")
    print("="*60)

    # Create directories
    os.makedirs('sounds/tabla', exist_ok=True)
    os.makedirs('sounds/daf', exist_ok=True)
    print("\n✓ Created directories: sounds/tabla/ and sounds/daf/")

    # Get API key
    api_key = get_api_key()

    if not api_key:
        manual_download_instructions()
        return

    # Verify API key
    print("\nVerifying API key...")
    test_url = f"{BASE_URL}/search/text/"
    try:
        response = requests.get(test_url, params={'query': 'tabla', 'token': api_key})
        response.raise_for_status()
        print("✓ API key verified!")
    except Exception as e:
        print(f"✗ API key validation failed: {e}")
        print("\nPlease check your API key and try again.")
        manual_download_instructions()
        return

    # Download tabla samples
    print("\n" + "-"*60)
    print("Downloading TABLA samples...")
    print("-"*60)

    for filename, info in TABLA_SAMPLES.items():
        output_path = f"sounds/tabla/{filename}"

        if os.path.exists(output_path):
            print(f"\n{filename}: Already exists, skipping...")
            continue

        print(f"\n{filename}: {info['description']}")

        if info['sound_id']:
            # Download specific sound
            download_sound(info['sound_id'], output_path, api_key)
        else:
            # Search for best match
            print(f"  Searching: {info['search']}")
            results = search_sounds(info['search'], api_key)

            if results:
                print(f"  Found {len(results)} results")
                # Download first result
                download_sound(results[0]['id'], output_path, api_key)
            else:
                print(f"  No results found for: {info['search']}")

        time.sleep(1)  # Rate limiting

    # Download daf samples
    print("\n" + "-"*60)
    print("Downloading DAF samples...")
    print("-"*60)

    for filename, info in DAF_SAMPLES.items():
        output_path = f"sounds/daf/{filename}"

        if os.path.exists(output_path):
            print(f"\n{filename}: Already exists, skipping...")
            continue

        print(f"\n{filename}: {info['description']}")

        if info['sound_id']:
            download_sound(info['sound_id'], output_path, api_key)
        else:
            print(f"  Searching: {info['search']}")
            results = search_sounds(info['search'], api_key)

            if results:
                print(f"  Found {len(results)} results")
                download_sound(results[0]['id'], output_path, api_key)
            else:
                print(f"  No results found for: {info['search']}")

        time.sleep(1)  # Rate limiting

    print("\n" + "="*60)
    print("  DOWNLOAD COMPLETE!")
    print("="*60)
    print("\nNote: Files were downloaded as MP3 (preview quality).")
    print("To convert to WAV (if needed):")
    print("  ffmpeg -i sounds/tabla/na.mp3 sounds/tabla/na.wav")
    print("\nOr use them as-is - simpleaudio can play MP3 files.")
    print("\nRun the demo:")
    print("  python demos/daf_tabla.py")
    print("="*60 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user.")
        sys.exit(0)
