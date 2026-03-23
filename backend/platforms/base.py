"""
Platform adapter base class
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class PlatformStatus(Enum):
    """Platform connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class PlatformConfig:
    """Platform configuration"""
    name: str
    platform_type: str
    rtmp_url: str
    stream_key: str
    enabled: bool = True
    video_params: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_rtmp_url(self) -> str:
        """Get full RTMP URL with stream key"""
        return f"{self.rtmp_url}/{self.stream_key}" if self.stream_key else self.rtmp_url

    def is_configured(self) -> bool:
        """Check if platform is properly configured"""
        return bool(self.rtmp_url and self.stream_key)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "name": self.name,
            "platform_type": self.platform_type,
            "rtmp_url": self.rtmp_url,
            "has_stream_key": bool(self.stream_key),
            "enabled": self.enabled,
            "configured": self.is_configured(),
        }


class PlatformAdapter(ABC):
    """Base class for platform adapters"""

    def __init__(self, config: PlatformConfig):
        self.config = config
        self._status = PlatformStatus.DISCONNECTED
        self._last_error: Optional[str] = None

    @property
    @abstractmethod
    def platform_type(self) -> str:
        """Platform type identifier"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human readable platform name"""
        pass

    @property
    def status(self) -> PlatformStatus:
        """Current platform status"""
        return self._status

    @property
    def last_error(self) -> Optional[str]:
        """Last error message"""
        return self._last_error

    @property
    def is_enabled(self) -> bool:
        """Check if platform is enabled"""
        return self.config.enabled and self.config.is_configured()

    def get_ffmpeg_video_params(self) -> List[str]:
        """Get FFmpeg video parameters for this platform"""
        params = [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-b:v", "2500k",
            "-maxrate", "3000k",
            "-bufsize", "6000k",
            "-pix_fmt", "yuv420p",
            "-g", "60",
            "-keyint_min", "60",
        ]

        # Add platform-specific params
        for key, value in self.config.video_params.items():
            if key == "preset":
                params.extend(["-preset", str(value)])
            elif key == "g":
                params.extend(["-g", str(value), "-keyint_min", str(value)])
            elif key == "profile":
                params.extend(["-profile:v", str(value)])

        return params

    def get_ffmpeg_audio_params(self) -> List[str]:
        """Get FFmpeg audio parameters"""
        return [
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
        ]

    def get_ffmpeg_output_params(self) -> List[str]:
        """Get FFmpeg output parameters"""
        return [
            "-f", "flv",
            self.config.full_rtmp_url
        ]

    def set_status(self, status: PlatformStatus, error: Optional[str] = None):
        """Update platform status"""
        self._status = status
        self._last_error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "platform_type": self.platform_type,
            "display_name": self.display_name,
            "enabled": self.config.enabled,
            "configured": self.config.is_configured(),
            "status": self._status.value,
            "rtmp_url": self.config.rtmp_url,
            "has_stream_key": bool(self.config.stream_key),
            "last_error": self._last_error,
        }
