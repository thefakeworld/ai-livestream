"""
FFmpeg-based streamer implementation
"""

from typing import Optional, List, Dict, Any
from pathlib import Path

from streaming.base import BaseStreamer, StreamStatus
from core.config import get_settings
from core.logger import get_logger
from platforms import PlatformManager, get_platform_manager

logger = get_logger("ffmpeg_streamer")


class FFmpegStreamer(BaseStreamer):
    """FFmpeg-based video streamer"""

    def __init__(
        self,
        video_source: Optional[str] = None,
        audio_source: Optional[str] = None,
        platforms: Optional[List[str]] = None,
    ):
        super().__init__()
        self.settings = get_settings()
        self.platform_manager = get_platform_manager()

        self.video_source = video_source
        self.audio_source = audio_source
        self.platforms = platforms  # Specific platforms, or None for all enabled

    def set_video_source(self, source: str):
        """Set video source (file, URL, or device)"""
        self.video_source = source

    def set_audio_source(self, source: str):
        """Set audio source (file or URL)"""
        self.audio_source = source

    def build_command(self) -> List[str]:
        """Build FFmpeg command for streaming"""
        cmd = ["ffmpeg", "-y"]

        # Video input
        if self.video_source:
            if self.video_source.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                # Video file with loop
                cmd.extend([
                    "-stream_loop", "-1",
                    "-i", self.video_source,
                ])
            elif self.video_source.endswith(('.png', '.jpg', '.jpeg')):
                # Static image
                cmd.extend([
                    "-loop", "1",
                    "-i", self.video_source,
                    "-t", "86400",  # 24 hours max
                ])
            else:
                cmd.extend(["-i", self.video_source])
        else:
            # Generate test pattern
            cmd.extend([
                "-f", "lavfi",
                "-i", f"testsrc=size={self.settings.VIDEO_WIDTH}x{self.settings.VIDEO_HEIGHT}:rate={self.settings.VIDEO_FPS}",
            ])

        # Audio input
        if self.audio_source:
            cmd.extend(["-i", self.audio_source])
        else:
            # Generate silent audio
            cmd.extend([
                "-f", "lavfi",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            ])

        # Video encoding
        cmd.extend([
            "-c:v", self.settings.VIDEO_CODEC,
            "-preset", self.settings.VIDEO_PRESET,
            "-b:v", self.settings.VIDEO_BITRATE,
            "-maxrate", "3000k",
            "-bufsize", "6000k",
            "-pix_fmt", "yuv420p",
            "-g", "60",
            "-keyint_min", "60",
        ])

        # Audio encoding
        cmd.extend([
            "-c:a", self.settings.AUDIO_CODEC,
            "-b:a", self.settings.AUDIO_BITRATE,
            "-ar", str(self.settings.AUDIO_SAMPLE_RATE),
        ])

        # Output
        enabled_platforms = self.platform_manager.get_enabled_platforms()
        if not enabled_platforms:
            raise ValueError("No enabled platforms configured")

        if len(enabled_platforms) == 1:
            # Single platform - direct output
            platform = enabled_platforms[0]
            cmd.extend([
                "-f", "flv",
                platform.config.full_rtmp_url
            ])
        else:
            # Multiple platforms - use tee muxer
            tee_outputs = []
            for platform in enabled_platforms:
                if platform.config.is_configured():
                    tee_outputs.append(f"[f=flv]{platform.config.full_rtmp_url}")

            if not tee_outputs:
                raise ValueError("No properly configured platforms")

            cmd.extend([
                "-f", "tee",
                "-map", "0:v",
                "-map", "1:a",
                "|".join(tee_outputs),
            ])

        return cmd


class PlaylistStreamer(FFmpegStreamer):
    """Stream from a playlist of videos"""

    def __init__(
        self,
        playlist_file: Optional[str] = None,
        platforms: Optional[List[str]] = None,
    ):
        super().__init__(platforms=platforms)
        self.playlist_file = playlist_file
        self.playlist: List[str] = []
        self.current_index = 0

        if playlist_file:
            self._load_playlist()

    def _load_playlist(self):
        """Load playlist from file"""
        if not self.playlist_file:
            return

        try:
            with open(self.playlist_file, 'r') as f:
                self.playlist = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith('#')
                ]
            logger.info(f"Loaded playlist with {len(self.playlist)} items")
        except Exception as e:
            logger.error(f"Failed to load playlist: {e}")

    def get_current_video(self) -> Optional[str]:
        """Get current video in playlist"""
        if self.playlist:
            return self.playlist[self.current_index % len(self.playlist)]
        return None

    def next_video(self) -> Optional[str]:
        """Move to next video in playlist"""
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            return self.get_current_video()
        return None
