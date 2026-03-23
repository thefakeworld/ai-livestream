"""
Playlist Service - Playlist management and generation
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

from core.config import get_settings
from core.logger import get_logger

logger = get_logger("playlist")


class ContentType(Enum):
    """Content types"""
    NEWS = "news"
    MUSIC = "music"
    VIDEO = "video"
    CUSTOM = "custom"


@dataclass
class PlaylistItem:
    """Playlist item"""
    id: str
    content_type: ContentType
    path: str
    title: str
    duration: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content_type": self.content_type.value,
            "path": self.path,
            "title": self.title,
            "duration": self.duration,
            "metadata": self.metadata or {},
        }


class PlaylistService:
    """Playlist management and generation service"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.output_dir = output_dir or self.settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.playlist_file = self.output_dir / "playlist.json"
        self.playlist_path = self.output_dir / "stream_playlist.txt"
        
        self._items: List[PlaylistItem] = []
        self._current_index = 0
        
        self._load_playlist()
        
        logger.info(f"Playlist Service initialized: {len(self._items)} items")

    def _load_playlist(self):
        """Load playlist from file"""
        if self.playlist_file.exists():
            try:
                with open(self.playlist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._items = [
                    PlaylistItem(
                        id=item['id'],
                        content_type=ContentType(item['content_type']),
                        path=item['path'],
                        title=item['title'],
                        duration=item['duration'],
                        metadata=item.get('metadata'),
                    )
                    for item in data.get('items', [])
                ]
                self._current_index = data.get('current_index', 0)
                
                logger.debug(f"Loaded {len(self._items)} playlist items")
                
            except Exception as e:
                logger.warning(f"Failed to load playlist: {e}")

    def _save_playlist(self):
        """Save playlist to file"""
        try:
            data = {
                'items': [item.to_dict() for item in self._items],
                'current_index': self._current_index,
                'updated_at': datetime.now().isoformat(),
            }
            
            with open(self.playlist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Also save FFmpeg-compatible playlist
            with open(self.playlist_path, 'w', encoding='utf-8') as f:
                for item in self._items:
                    if Path(item.path).exists():
                        f.write(f"file '{item.path}'\n")
                        f.write(f"duration {item.duration}\n")
                # Add last file again for proper ending
                if self._items:
                    f.write(f"file '{self._items[-1].path}'\n")
            
        except Exception as e:
            logger.error(f"Failed to save playlist: {e}")

    def add_item(
        self,
        content_type: ContentType,
        path: str,
        title: str,
        duration: float,
        metadata: Dict[str, Any] = None
    ) -> PlaylistItem:
        """Add item to playlist"""
        item_id = f"{content_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self._items)}"
        
        item = PlaylistItem(
            id=item_id,
            content_type=content_type,
            path=path,
            title=title,
            duration=duration,
            metadata=metadata,
        )
        
        self._items.append(item)
        self._save_playlist()
        
        logger.info(f"Added playlist item: {item.title}")
        return item

    def remove_item(self, item_id: str) -> bool:
        """Remove item from playlist"""
        for i, item in enumerate(self._items):
            if item.id == item_id:
                self._items.pop(i)
                if self._current_index >= len(self._items):
                    self._current_index = max(0, len(self._items) - 1)
                self._save_playlist()
                logger.info(f"Removed playlist item: {item_id}")
                return True
        return False

    def clear(self):
        """Clear entire playlist"""
        self._items = []
        self._current_index = 0
        self._save_playlist()
        logger.info("Playlist cleared")

    def get_current(self) -> Optional[PlaylistItem]:
        """Get current playlist item"""
        if self._items and 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return None

    def get_next(self) -> Optional[PlaylistItem]:
        """Get next playlist item (with loop)"""
        if not self._items:
            return None
        
        self._current_index = (self._current_index + 1) % len(self._items)
        self._save_playlist()
        return self.get_current()

    def get_previous(self) -> Optional[PlaylistItem]:
        """Get previous playlist item"""
        if not self._items:
            return None
        
        self._current_index = (self._current_index - 1) % len(self._items)
        self._save_playlist()
        return self.get_current()

    def set_current(self, item_id: str) -> bool:
        """Set current item by ID"""
        for i, item in enumerate(self._items):
            if item.id == item_id:
                self._current_index = i
                self._save_playlist()
                return True
        return False

    def get_all(self) -> List[PlaylistItem]:
        """Get all playlist items"""
        return self._items

    def shuffle(self):
        """Shuffle playlist"""
        random.shuffle(self._items)
        self._current_index = 0
        self._save_playlist()
        logger.info("Playlist shuffled")

    def sort_by_duration(self, reverse: bool = False):
        """Sort playlist by duration"""
        self._items.sort(key=lambda x: x.duration, reverse=reverse)
        self._save_playlist()

    def get_total_duration(self) -> float:
        """Get total playlist duration"""
        return sum(item.duration for item in self._items)

    def get_ffmpeg_playlist(self) -> str:
        """Get FFmpeg-compatible playlist path"""
        return str(self.playlist_path)

    def generate_from_music(
        self, 
        music_paths: List[str],
        shuffle: bool = True
    ) -> List[PlaylistItem]:
        """Generate playlist from music files"""
        import subprocess
        
        items = []
        
        for path in music_paths:
            try:
                # Get duration
                result = subprocess.run(
                    [
                        "ffprobe", "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        path
                    ],
                    capture_output=True,
                    text=True
                )
                duration = float(result.stdout.strip())
                
                # Get title from filename
                title = Path(path).stem
                if '_' in title:
                    parts = title.split('_', 2)
                    if len(parts) >= 3:
                        title = parts[2].replace('_', ' ')
                
                item = self.add_item(
                    content_type=ContentType.MUSIC,
                    path=path,
                    title=title,
                    duration=duration,
                )
                items.append(item)
                
            except Exception as e:
                logger.warning(f"Failed to process {path}: {e}")
        
        if shuffle:
            self.shuffle()
        
        return items

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API"""
        return {
            "items": [item.to_dict() for item in self._items],
            "current_index": self._current_index,
            "current_item": self.get_current().to_dict() if self.get_current() else None,
            "total_duration": self.get_total_duration(),
            "total_items": len(self._items),
        }
