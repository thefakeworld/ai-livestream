"""
Custom exceptions for the application
"""

from typing import Optional, Any


class AILivestreamError(Exception):
    """Base exception for AI Livestream"""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


# Configuration errors
class ConfigError(AILivestreamError):
    """Configuration related errors"""
    pass


class MissingConfigError(ConfigError):
    """Required configuration is missing"""
    pass


# Streaming errors
class StreamingError(AILivestreamError):
    """Streaming related errors"""
    pass


class StreamConnectionError(StreamingError):
    """Failed to connect to streaming server"""
    pass


class StreamInterruptedError(StreamingError):
    """Stream was interrupted"""
    pass


class FFmpegError(StreamingError):
    """FFmpeg related errors"""

    def __init__(self, message: str, return_code: Optional[int] = None, stderr: Optional[str] = None):
        super().__init__(message, {"return_code": return_code, "stderr": stderr})
        self.return_code = return_code
        self.stderr = stderr


# Platform errors
class PlatformError(AILivestreamError):
    """Platform related errors"""
    pass


class PlatformNotConfiguredError(PlatformError):
    """Platform is not configured"""
    pass


class PlatformConnectionError(PlatformError):
    """Failed to connect to platform"""
    pass


# Content errors
class ContentError(AILivestreamError):
    """Content related errors"""
    pass


class NoContentError(ContentError):
    """No content available"""
    pass


class ContentNotFoundError(ContentError):
    """Content not found"""
    pass


# Service errors
class ServiceError(AILivestreamError):
    """Service related errors"""
    pass


class TTSError(ServiceError):
    """TTS service errors"""
    pass


class NewsServiceError(ServiceError):
    """News service errors"""
    pass


class MusicServiceError(ServiceError):
    """Music service errors"""
    pass


class VideoServiceError(ServiceError):
    """Video service errors"""
    pass


# Director errors
class DirectorError(AILivestreamError):
    """Director system errors"""
    pass


class DirectorNotRunningError(DirectorError):
    """Director is not running"""
    pass


class ContentSwitchError(DirectorError):
    """Failed to switch content"""
    pass
