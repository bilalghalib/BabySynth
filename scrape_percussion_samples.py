#!/usr/bin/env python3
"""
Advanced percussion sample scraper using BeautifulSoup
Scrapes Freesound.org to find and download the best tabla/daf samples
"""

import os
import sys
import re
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, quote

# User agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

# Search queries for each stroke type
SEARCH_QUERIES = {
    'tabla': {
        'na.wav': ['tabla na stroke', 'tabla ta stroke'],
        'tin.wav': ['tabla tin stroke', 'tabla closed stroke'],
        'te.wav': ['tabla te stroke', 'tabla ti stroke'],
        'ge.wav': ['tabla ge stroke', 'tabla bass open'],
        'ka.wav': ['tabla ka stroke', 'tabla bass slap'],
        'dha.wav': ['tabla dha stroke', 'tabla dha']
    },
    'daf': {
        'dum.wav': ['daf dum', 'frame drum bass', 'doumbek dum'],
        'tak.wav': ['daf tak', 'frame drum high', 'doumbek tak'],
        'roll.wav': ['frame drum roll', 'daf roll', 'riq roll']
    }
}


def search_freesound(query, max_results=10):
    """
    Search Freesound.org and scrape results
    Returns list of sound info dicts
    """
    search_url = f"https://freesound.org/search/?q={quote(query)}&f=duration:[0 TO 3]&s=downloads+desc"

    try:
        print(f"    Searching: {query}")
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find sound results
        results = []
        sound_items = soup.find_all('div', class_='sample_player_small')

        for item in sound_items[:max_results]:
            try:
                # Extract sound ID from player
                sound_id_match = re.search(r'sound_id:\s*(\d+)', str(item))
                if not sound_id_match:
                    continue

                sound_id = sound_id_match.group(1)

                # Find the link to get more info
                parent = item.find_parent('div', class_='sound_filename')
                if not parent:
                    parent = item.find_parent()

                title_elem = parent.find('a') if parent else None
                title = title_elem.text.strip() if title_elem else f"sound_{sound_id}"

                # Get username
                user_elem = soup.find('a', href=re.compile(f'/people/[^/]+/sounds/{sound_id}/'))
                username = 'unknown'
                if user_elem:
                    user_match = re.search(r'/people/([^/]+)/', user_elem.get('href', ''))
                    if user_match:
                        username = user_match.group(1)

                results.append({
                    'id': sound_id,
                    'title': title,
                    'username': username,
                    'url': f'https://freesound.org/people/{username}/sounds/{sound_id}/'
                })

            except Exception as e:
                print(f"      Error parsing result: {e}")
                continue

        print(f"    Found {len(results)} results")
        return results

    except Exception as e:
        print(f"    Error searching: {e}")
        return []


def get_preview_url(sound_url):
    """
    Scrape the sound page to get the preview download URL
    """
    try:
        response = requests.get(sound_url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Method 1: Find preview URLs in the page source
        preview_patterns = [
            r'https://freesound\.org/data/previews/\d+/\d+_\d+-hq\.mp3',
            r'https://freesound\.org/data/previews/\d+/\d+_\d+-lq\.mp3',
        ]

        for pattern in preview_patterns:
            match = re.search(pattern, response.text)
            if match:
                return match.group(0)

        # Method 2: Look for download/preview buttons
        download_links = soup.find_all('a', href=re.compile(r'previews.*\.mp3'))
        if download_links:
            return urljoin(sound_url, download_links[0]['href'])

        # Method 3: Construct preview URL from sound ID
        sound_id_match = re.search(r'/sounds/(\d+)/', sound_url)
        if sound_id_match:
            sound_id = sound_id_match.group(1)
            # Try to extract preview from embedded player
            player_match = re.search(rf'{sound_id}_(\d+)-hq\.mp3', response.text)
            if player_match:
                file_id = player_match.group(1)
                folder = sound_id[:3]  # First 3 digits
                return f'https://freesound.org/data/previews/{folder}/{sound_id}_{file_id}-hq.mp3'

        return None

    except Exception as e:
        print(f"      Error getting preview URL: {e}")
        return None


def download_file(url, output_path):
    """Download a file from URL"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(output_path) / 1024  # KB
        return True, file_size

    except Exception as e:
        return False, str(e)


def download_sample(filename, queries, output_dir):
    """
    Try to download a sample by searching with multiple queries
    """
    output_path = os.path.join(output_dir, filename)

    # Skip if already exists
    if os.path.exists(output_path):
        print(f"  ✓ {filename}: Already exists")
        return True

    print(f"\n  [{filename}]")

    # Try each search query
    for query in queries:
        results = search_freesound(query, max_results=5)

        if not results:
            continue

        # Try to download the first good result
        for i, result in enumerate(results, 1):
            print(f"    Trying result {i}: {result['title']} by {result['username']}")

            # Get preview URL
            preview_url = get_preview_url(result['url'])

            if not preview_url:
                print(f"      ✗ Could not find preview URL")
                continue

            print(f"      Downloading from: {preview_url}")

            # Download to MP3 first
            mp3_path = output_path.replace('.wav', '.mp3')
            success, info = download_file(preview_url, mp3_path)

            if success:
                print(f"      ✓ Downloaded: {info:.1f} KB")
                print(f"      Source: {result['url']}")
                time.sleep(1)  # Be nice to the server
                return True
            else:
                print(f"      ✗ Download failed: {info}")

        # Wait between queries
        time.sleep(2)

    print(f"    ✗ Could not download {filename}")
    return False


def main():
    print("="*70)
    print("  FREESOUND PERCUSSION SCRAPER")
    print("="*70)
    print("\nThis script intelligently searches and downloads percussion samples")
    print("from Freesound.org using web scraping (no API key needed).")
    print()

    # Check dependencies
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Error: BeautifulSoup not installed")
        print("Install with: pip install beautifulsoup4")
        sys.exit(1)

    try:
        import requests
    except ImportError:
        print("Error: requests library not installed")
        print("Install with: pip install requests")
        sys.exit(1)

    # Create directories
    os.makedirs('sounds/tabla', exist_ok=True)
    os.makedirs('sounds/daf', exist_ok=True)
    print("✓ Directories created\n")

    # Download samples
    stats = {'success': 0, 'failed': 0, 'skipped': 0}

    for category, samples in SEARCH_QUERIES.items():
        print(f"\n{'='*70}")
        print(f"  {category.upper()} SAMPLES")
        print(f"{'='*70}")

        output_dir = f'sounds/{category}'

        for filename, queries in samples.items():
            result = download_sample(filename, queries, output_dir)

            if result:
                if os.path.exists(os.path.join(output_dir, filename.replace('.wav', '.mp3'))):
                    stats['success'] += 1
                else:
                    stats['skipped'] += 1
            else:
                stats['failed'] += 1

            time.sleep(1)  # Rate limiting

    # Summary
    print("\n" + "="*70)
    print("  DOWNLOAD COMPLETE")
    print("="*70)
    print(f"\n  ✓ Successfully downloaded: {stats['success']} files")
    if stats['skipped'] > 0:
        print(f"  ⊙ Skipped (already exist): {stats['skipped']} files")
    if stats['failed'] > 0:
        print(f"  ✗ Failed to download: {stats['failed']} files")

    print("\n" + "-"*70)
    print("  NEXT STEPS")
    print("-"*70)
    print("\n1. Files are saved as MP3 format (HQ previews)")

    print("\n2. Update config to use MP3:")
    print("   Edit configs/daf_tabla.yaml")
    print("   Change: ./sounds/tabla/na.wav → ./sounds/tabla/na.mp3")

    print("\n3. Or convert to WAV:")
    print("   for f in sounds/tabla/*.mp3; do")
    print("     ffmpeg -i \"$f\" \"${f%.mp3}.wav\"")
    print("   done")

    print("\n4. Run the demo:")
    print("   python demos/daf_tabla.py")

    print("\n5. License: All samples from Freesound.org (CC licensed)")
    print("   Attribution may be required - check individual sound pages")

    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScraping cancelled by user.")
        sys.exit(0)
