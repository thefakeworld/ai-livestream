"""
Core module for AI Livestream
"""

from .config import Settings, get_settings, PLATFORM_CONFIGS
from .logger import setup_logger, get_logger
from .exceptions import (
    AILivestreamError,
    ConfigError,
    MissingConfigError,
    StreamingError,
    StreamConnectionError,
    StreamInterruptedError,
    FFmpegError,
    PlatformError,
    PlatformNotConfiguredError,
    PlatformConnectionError,
    ContentError,
    NoContentError,
    ContentNotFoundError,
    ServiceError,
    TTSError,
    NewsServiceError,
    MusicServiceError,
    VideoServiceError,
    DirectorError,
    DirectorNotRunningError,
    ContentSwitchError,
)

__all__ = [
    "Settings",
    "get_settings",
    "PLATFORM_CONFIGS",
    "setup_logger",
    "get_logger",
    "AILivestreamError",
    "ConfigError",
    "MissingConfigError",
    "StreamingError",
    "StreamConnectionError",
    "StreamInterruptedError",
    "FFmpegError",
    "PlatformError",
    "PlatformNotConfiguredError",
    "PlatformConnectionError",
    "ContentError",
    "NoContentError",
    "ContentNotFoundError",
    "ServiceError",
    "TTSError",
    "NewsServiceError",
    "MusicServiceError",
    "VideoServiceError",
    "DirectorError",
    "DirectorNotRunningError",
    "ContentSwitchError",
]
