#!/usr/bin/env python3
"""
Music Downloader for Livestream
Downloads popular global songs from SoundCloud as audio files
"""

import os
import subprocess
import json
from pathlib import Path

# Music directory
MUSIC_DIR = Path(__file__).parent / "music"

# Popular global songs (search queries)
POPULAR_SONGS = [
    "Blinding Lights The Weeknd",
    "Shape of You Ed Sheeran",
    "Dance Monkey Tones and I",
    "Uptown Funk Bruno Mars",
    "Someone You Loved Lewis Capaldi",
    "Bad Guy Billie Eilish",
    "Sunflower Post Malone",
    "Senorita Shawn Mendes Camila Cabello",
    "Perfect Ed Sheeran",
    "Havana Camila Cabello",
    "Rockabye Clean Bandit",
    "Closer Chainsmokers",
    "Love Me Like You Do Ellie Goulding",
    "See You Again Wiz Khalifa",
    "Sorry Justin Bieber",
    "Faded Alan Walker",
    "Despacito Luis Fonsi",
    "Old Town Road Lil Nas X",
    "Levitating Dua Lipa",
    "Watermelon Sugar Harry Styles",
]


def download_song(query: str, output_dir: Path, index: int) -> bool:
    """
    Download a song from SoundCloud as audio file using yt-dlp
    """
    output_template = str(output_dir / f"song_{index:02d}_%(title)s.%(ext)s")

    # Use full path to yt-dlp
    yt_dlp_path = os.path.expanduser("~/.local/bin/yt-dlp")

    cmd = [
        yt_dlp_path,
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",  # Best quality
        "--output", output_template,
        "--max-filesize", "30M",  # Limit file size
        "--add-metadata",
        f"scsearch1:{query}",  # SoundCloud search
    ]

    try:
        print(f"[{index}/20] Downloading: {query}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"  ✓ Downloaded successfully")
            return True
        else:
            print(f"  ✗ Failed: {result.stderr[:100]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def download_all_songs():
    """
    Download all popular songs
    """
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Music Downloader - Downloading 20 Popular Global Songs")
    print("Source: SoundCloud")
    print("=" * 60)
    print(f"Output directory: {MUSIC_DIR}")
    print()

    success_count = 0
    for i, song in enumerate(POPULAR_SONGS, 1):
        if download_song(song, MUSIC_DIR, i):
            success_count += 1

    print()
    print("=" * 60)
    print(f"Download complete: {success_count}/20 songs downloaded")
    print(f"Music files saved to: {MUSIC_DIR}")
    print("=" * 60)

    # List downloaded files
    music_files = list(MUSIC_DIR.glob("*.mp3"))
    print(f"\nDownloaded files ({len(music_files)}):")
    for f in sorted(music_files):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name} ({size_mb:.1f} MB)")


def get_music_playlist():
    """
    Get list of downloaded music files
    """
    music_files = sorted(MUSIC_DIR.glob("*.mp3"))
    return [str(f) for f in music_files]


if __name__ == "__main__":
    download_all_songs()
