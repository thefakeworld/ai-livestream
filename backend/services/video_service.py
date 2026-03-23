"""
Video Service - Video composition and generation
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import random

from core.config import get_settings
from core.logger import get_logger

logger = get_logger("video")


@dataclass
class VideoResult:
    """Video generation result"""
    path: Path
    duration: float
    resolution: str
    size_mb: float

    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "path": str(self.path),
            "duration": self.duration,
            "resolution": self.resolution,
            "size_mb": self.size_mb,
        }


class VideoService:
    """Video composition and generation service"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.output_dir = output_dir or self.settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Asset paths
        self.assets_dir = self.settings.ASSETS_DIR
        self.video_template = self.assets_dir / "video" / "template.mp4"
        self.static_image = self.assets_dir / "video" / "digital_human.png"
        
        logger.info(f"Video Service initialized: output={self.output_dir}")

    @property
    def has_video_template(self) -> bool:
        return self.video_template.exists()

    @property
    def has_static_image(self) -> bool:
        return self.static_image.exists()

    def create_from_audio(
        self,
        audio_path: Path,
        output_path: Optional[Path] = None,
        text: str = "",
        use_template: bool = True
    ) -> Optional[VideoResult]:
        """
        Create video from audio file
        
        Args:
            audio_path: Audio file path
            output_path: Output video path (optional)
            text: Text to display (optional)
            use_template: Whether to use video template
            
        Returns:
            VideoResult or None
        """
        output_path = output_path or self.output_dir / f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        # Get audio duration
        duration = self._get_audio_duration(audio_path)
        if duration <= 0:
            logger.error(f"Invalid audio duration: {audio_path}")
            return None
        
        # Limit duration
        duration = min(duration, self.settings.MAX_NEWS_DURATION)
        
        try:
            if use_template and self.has_video_template:
                result = self._create_from_template(audio_path, output_path, duration)
            elif self.has_static_image:
                result = self._create_from_image(audio_path, output_path, duration, text)
            else:
                result = self._create_gradient_video(audio_path, output_path, duration, text)
            
            if result and output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"Video created: {output_path} ({size_mb:.1f}MB)")
                return VideoResult(
                    path=output_path,
                    duration=duration,
                    resolution=f"{self.settings.VIDEO_WIDTH}x{self.settings.VIDEO_HEIGHT}",
                    size_mb=size_mb
                )
                
        except Exception as e:
            logger.error(f"Failed to create video: {e}")
        
        return None

    def _create_from_template(
        self, 
        audio_path: Path, 
        output_path: Path,
        duration: float
    ) -> bool:
        """Create video from video template"""
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(self.video_template),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-preset", self.settings.VIDEO_PRESET,
            "-c:a", "aac",
            "-b:a", self.settings.AUDIO_BITRATE,
            "-t", str(duration),
            "-shortest",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def _create_from_image(
        self, 
        audio_path: Path, 
        output_path: Path,
        duration: float,
        text: str
    ) -> bool:
        """Create video from static image"""
        # Create image with text overlay
        temp_image = self.output_dir / "temp_frame.png"
        self._create_text_overlay(self.static_image, temp_image, text)
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(temp_image),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-preset", self.settings.VIDEO_PRESET,
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", self.settings.AUDIO_BITRATE,
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-shortest",
            "-r", str(self.settings.VIDEO_FPS),
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Cleanup temp file
        if temp_image.exists():
            temp_image.unlink()
        
        return result.returncode == 0

    def _create_gradient_video(
        self, 
        audio_path: Path, 
        output_path: Path,
        duration: float,
        text: str
    ) -> bool:
        """Create video with gradient background"""
        # Generate gradient with text using FFmpeg filter
        text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c='#1a1e3c':s={self.settings.VIDEO_WIDTH}x{self.settings.VIDEO_HEIGHT}:r={self.settings.VIDEO_FPS}:d={duration}",
            "-i", str(audio_path),
            "-vf", f"drawtext=text='{text_escaped}':fontsize=32:fontcolor=white:x=(w-text_w)/2:y=h-100",
            "-c:v", "libx264",
            "-preset", self.settings.VIDEO_PRESET,
            "-c:a", "aac",
            "-b:a", self.settings.AUDIO_BITRATE,
            "-t", str(duration),
            "-shortest",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def _create_text_overlay(
        self, 
        source_image: Path, 
        output_image: Path,
        text: str
    ) -> bool:
        """Create image with text overlay using FFmpeg"""
        if not text:
            return False
            
        text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(source_image),
            "-vf", f"drawtext=text='{text_escaped}':fontsize=32:fontcolor=white:x=(w-text_w)/2:y=h-100",
            str(output_image)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def create_news_broadcast(
        self,
        news_items: List[Dict[str, Any]],
        audio_paths: List[Path],
        music_path: Optional[Path] = None,
        music_interval: float = 30
    ) -> Optional[VideoResult]:
        """
        Create complete news broadcast video
        
        Args:
            news_items: List of news items with title
            audio_paths: Corresponding audio files
            music_path: Background music for intervals
            music_interval: Duration of music intervals
            
        Returns:
            VideoResult or None
        """
        if len(news_items) != len(audio_paths):
            logger.error("Mismatch between news items and audio paths")
            return None
        
        output_path = self.output_dir / f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        segments = []
        temp_dir = self.output_dir / "temp_segments"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Create video segments
            for i, (news, audio) in enumerate(zip(news_items, audio_paths)):
                segment_path = temp_dir / f"segment_{i}.mp4"
                
                result = self.create_from_audio(
                    audio_path=audio,
                    output_path=segment_path,
                    text=news.get('title', '')
                )
                
                if result:
                    segments.append(segment_path)
                
                # Add music interval
                if music_path and i < len(news_items) - 1:
                    music_segment = self._create_music_segment(
                        music_path, 
                        temp_dir / f"music_{i}.mp4",
                        music_interval
                    )
                    if music_segment:
                        segments.append(music_segment)
            
            if not segments:
                logger.error("No segments created")
                return None
            
            # Concatenate segments
            concat_list = temp_dir / "concat_list.txt"
            with open(concat_list, 'w') as f:
                for seg in segments:
                    f.write(f"file '{seg}'\n")
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "aac",
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                duration = self._get_video_duration(output_path)
                
                return VideoResult(
                    path=output_path,
                    duration=duration,
                    resolution=f"{self.settings.VIDEO_WIDTH}x{self.settings.VIDEO_HEIGHT}",
                    size_mb=size_mb
                )
                
        finally:
            # Cleanup
            for seg in segments:
                if seg.exists():
                    seg.unlink()
            if temp_dir.exists():
                temp_dir.rmdir()
        
        return None

    def _create_music_segment(
        self, 
        music_path: Path, 
        output_path: Path,
        duration: float
    ) -> Optional[Path]:
        """Create music interval video segment"""
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c='#2a1a3c':s={self.settings.VIDEO_WIDTH}x{self.settings.VIDEO_HEIGHT}:r={self.settings.VIDEO_FPS}:d={duration}",
            "-i", str(music_path),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-t", str(duration),
            "-shortest",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and output_path.exists():
            return output_path
        return None

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

    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration using ffprobe"""
        return self._get_audio_duration(video_path)
