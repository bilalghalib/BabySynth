#!/usr/bin/env python3
"""
Working percussion sample downloader
Fetches current preview URLs from Freesound pages
"""

import os
import sys
import re
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

# Known good sound IDs from Freesound
SAMPLES = {
    'tabla': {
        'na.wav': '171913',  # ajaysm - tabla te stroke (using as na)
        'tin.wav': '130424',  # mmiron - tabla ke stroke (using as tin)
        'te.wav': '171913',   # ajaysm - tabla te stroke
        'ge.wav': '153268',   # sankalp - tabla bols
        'ka.wav': '130424',   # mmiron - tabla ke stroke (using as ka)
        'dha.wav': '153268',  # sankalp - tabla bols (using as dha)
    },
    'daf': {
        'dum.wav': '244152',  # Metzik - frame drum
        'tak.wav': '244152',  # Metzik - frame drum
        'roll.wav': '244152', # Metzik - frame drum
    }
}


def get_preview_url_from_page(sound_id):
    """Fetch sound page and extract current preview URL"""
    # First try to get username from sound ID
    url = f'https://freesound.org/apiv2/sounds/{sound_id}/'

    # Try direct page fetch (works without knowing username)
    search_url = f'https://freesound.org/search/?q={sound_id}'

    try:
        print(f'      Fetching sound page...')
        response = requests.get(search_url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return None

        # Find the sound link in search results
        soup = BeautifulSoup(response.text, 'html.parser')
        sound_links = soup.find_all('a', href=re.compile(f'/sounds/{sound_id}/'))

        if not sound_links:
            return None

        sound_url = 'https://freesound.org' + sound_links[0]['href']

        # Now fetch the actual sound page
        print(f'      Loading: {sound_url}')
        response = requests.get(sound_url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return None

        # Extract preview URLs
        # Look for CDN URLs with previews
        pattern = r'https://cdn\.freesound\.org/previews/\d+/\d+_\d+-(lq|hq)\.mp3'
        matches = re.findall(pattern, response.text)

        if matches:
            # Prefer HQ, fallback to LQ
            hq_urls = [m for m in re.findall(pattern.replace('(lq|hq)', 'hq'), response.text)]
            lq_urls = [m for m in re.findall(pattern.replace('(lq|hq)', 'lq'), response.text)]

            url = hq_urls[0] if hq_urls else (lq_urls[0] if lq_urls else None)
            if url:
                print(f'      Found: {url}')
                return url

        return None

    except Exception as e:
        print(f'      Error: {e}')
        return None


def download_file(url, output_path):
    """Download file from URL"""
    try:
        print(f'      Downloading...')
        response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        size_kb = os.path.getsize(output_path) / 1024
        return True, size_kb

    except Exception as e:
        return False, str(e)


def main():
    print('='*70)
    print('  WORKING PERCUSSION SAMPLE DOWNLOADER')
    print('='*70)
    print('\nDownloading curated tabla and daf samples from Freesound.org')
    print()

    # Create directories
    os.makedirs('sounds/tabla', exist_ok=True)
    os.makedirs('sounds/daf', exist_ok=True)
    print('✓ Directories ready\n')

    stats = {'downloaded': 0, 'failed': 0, 'skipped': 0}

    for category, files in SAMPLES.items():
        print('='*70)
        print(f'  {category.upper()} SAMPLES')
        print('='*70 + '\n')

        for filename, sound_id in files.items():
            output_path = f'sounds/{category}/{filename}'
            mp3_path = output_path.replace('.wav', '.mp3')

            # Check if already exists
            if os.path.exists(mp3_path) or os.path.exists(output_path):
                print(f'✓ {filename}: Already exists\n')
                stats['skipped'] += 1
                continue

            print(f'[{filename}]')
            print(f'    Sound ID: {sound_id}')

            # Get current preview URL
            preview_url = get_preview_url_from_page(sound_id)

            if not preview_url:
                print(f'    ✗ Could not find preview URL\n')
                stats['failed'] += 1
                continue

            # Download
            success, info = download_file(preview_url, mp3_path)

            if success:
                print(f'    ✓ Downloaded: {info:.1f} KB → {mp3_path}\n')
                stats['downloaded'] += 1
            else:
                print(f'    ✗ Download failed: {info}\n')
                stats['failed'] += 1

            time.sleep(2)  # Be nice to Freesound

    # Summary
    print('='*70)
    print('  DOWNLOAD SUMMARY')
    print('='*70)
    print(f'\n  ✓ Downloaded: {stats["downloaded"]} files')
    if stats['skipped'] > 0:
        print(f'  ⊙ Skipped: {stats["skipped"]} files (already exist)')
    if stats['failed'] > 0:
        print(f'  ✗ Failed: {stats["failed"]} files')

    if stats['downloaded'] > 0:
        print('\n' + '-'*70)
        print('  NEXT STEPS')
        print('-'*70)
        print('\n1. Files downloaded as MP3 (HQ preview quality)')
        print('\n2. Update config to use MP3:')
        print('   Edit configs/daf_tabla.yaml')
        print('   Change all .wav to .mp3')
        print('\n3. Or convert to WAV (optional):')
        print('   for f in sounds/*/*.mp3; do ffmpeg -i "$f" "${f%.mp3}.wav"; done')
        print('\n4. Run the demo:')
        print('   python demos/daf_tabla.py')
        print('\n' + '='*70 + '\n')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nCancelled by user.')
        sys.exit(0)
