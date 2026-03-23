"""
Music Service - Music download and management
"""

import asyncio
import random
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json

from core.config import get_settings
from core.logger import get_logger

logger = get_logger("music")


@dataclass
class MusicTrack:
    """Music track info"""
    path: Path
    title: str
    duration: float
    artist: str = ""
    size_mb: float = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "title": self.title,
            "duration": self.duration,
            "artist": self.artist,
            "size_mb": self.size_mb,
        }


class MusicService:
    """Music download and management service"""

    # Default popular songs for download
    DEFAULT_SONGS = [
        "Blinding Lights The Weeknd",
        "Shape of You Ed Sheeran",
        "Dance Monkey Tones and I",
        "Uptown Funk Bruno Mars",
        "Bad Guy Billie Eilish",
        "Senorita Shawn Mendes Camila Cabello",
        "Havana Camila Cabello",
        "Closer Chainsmokers",
        "Sorry Justin Bieber",
        "Faded Alan Walker",
        "Old Town Road Lil Nas X",
        "Watermelon Sugar Harry Styles",
    ]

    def __init__(self, music_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.music_dir = music_dir or self.settings.MUSIC_DIR
        self.music_dir.mkdir(parents=True, exist_ok=True)
        
        self._tracks: List[MusicTrack] = []
        self._scan_music_dir()
        
        logger.info(f"Music Service initialized: {len(self._tracks)} tracks in {self.music_dir}")

    def _scan_music_dir(self):
        """Scan music directory for tracks"""
        self._tracks = []
        
        for ext in ['*.mp3', '*.wav', '*.m4a', '*.flac']:
            for path in self.music_dir.glob(ext):
                try:
                    duration = self._get_audio_duration(path)
                    size_mb = path.stat().st_size / (1024 * 1024)
                    
                    # Extract title from filename
                    title = path.stem
                    if '_' in title:
                        # Format: song_XX_Title
                        parts = title.split('_', 2)
                        if len(parts) >= 3:
                            title = parts[2].replace('_', ' ')
                    
                    track = MusicTrack(
                        path=path,
                        title=title,
                        duration=duration,
                        size_mb=size_mb,
                    )
                    self._tracks.append(track)
                    
                except Exception as e:
                    logger.warning(f"Failed to process {path}: {e}")
        
        # Sort by title
        self._tracks.sort(key=lambda t: t.title)

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration using ffprobe"""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(audio_path)
                ],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def get_all_tracks(self) -> List[MusicTrack]:
        """Get all music tracks"""
        return self._tracks

    def get_random_track(self) -> Optional[MusicTrack]:
        """Get a random music track"""
        if self._tracks:
            return random.choice(self._tracks)
        return None

    def get_track(self, title: str) -> Optional[MusicTrack]:
        """Get track by title (partial match)"""
        for track in self._tracks:
            if title.lower() in track.title.lower():
                return track
        return None

    def get_playlist(self, shuffle: bool = False) -> List[Path]:
        """Get list of music file paths"""
        tracks = self._tracks.copy()
        if shuffle:
            random.shuffle(tracks)
        return [t.path for t in tracks]

    async def download(
        self, 
        query: str, 
        output_name: Optional[str] = None
    ) -> Optional[MusicTrack]:
        """
        Download music from SoundCloud/YouTube using yt-dlp
        
        Args:
            query: Search query or URL
            output_name: Custom output filename
            
        Returns:
            Downloaded MusicTrack or None
        """
        if output_name:
            output_template = str(self.music_dir / f"{output_name}.%(ext)s")
        else:
            output_template = str(self.music_dir / "%(title)s.%(ext)s")
        
        cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--output", output_template,
            "--max-filesize", "30M",
            "--no-playlist",
            f"scsearch1:{query}",  # SoundCloud search
        ]
        
        try:
            logger.info(f"Downloading: {query}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Rescan directory
                self._scan_music_dir()
                
                # Find the new track
                for track in self._tracks:
                    if query.lower() in track.title.lower():
                        logger.info(f"Downloaded: {track.title}")
                        return track
                
                # Return last added track
                if self._tracks:
                    return self._tracks[-1]
                    
            else:
                error = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Download failed: {error}")
                
        except Exception as e:
            logger.error(f"Download error: {e}")
        
        return None

    async def download_batch(
        self, 
        queries: List[str],
        concurrency: int = 2
    ) -> List[MusicTrack]:
        """Download multiple tracks with limited concurrency"""
        results = []
        semaphore = asyncio.Semaphore(concurrency)
        
        async def download_one(query: str):
            async with semaphore:
                result = await self.download(query)
                return result
        
        tasks = [download_one(q) for q in queries]
        downloaded = await asyncio.gather(*tasks)
        
        results = [r for r in downloaded if r]
        return results

    async def download_default(self) -> List[MusicTrack]:
        """Download default popular songs"""
        return await self.download_batch(self.DEFAULT_SONGS)

    def refresh(self):
        """Rescan music directory"""
        self._scan_music_dir()
        logger.info(f"Refreshed: {len(self._tracks)} tracks")

    def get_stats(self) -> Dict[str, Any]:
        """Get music library statistics"""
        total_duration = sum(t.duration for t in self._tracks)
        total_size = sum(t.size_mb for t in self._tracks)
        
        return {
            "track_count": len(self._tracks),
            "total_duration_hours": total_duration / 3600,
            "total_size_mb": total_size,
            "music_dir": str(self.music_dir),
        }
