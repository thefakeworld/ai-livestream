"""
Application State - Global instances
Avoids circular imports by separating state from main.py
"""

from typing import Optional
from streaming import FFmpegStreamer
from director import Director

# Global instances
_streamer: Optional[FFmpegStreamer] = None
_director: Optional[Director] = None


def init_state():
    """Initialize global state"""
    global _streamer, _director
    _streamer = FFmpegStreamer()
    _director = Director()


def cleanup_state():
    """Cleanup global state"""
    global _streamer, _director
    
    if _streamer and _streamer.is_running:
        _streamer.stop()
    
    if _director and _director.is_running:
        _director.stop()


def get_streamer() -> Optional[FFmpegStreamer]:
    """Get the global streamer instance"""
    return _streamer


def get_director() -> Optional[Director]:
    """Get the global director instance"""
    return _director
