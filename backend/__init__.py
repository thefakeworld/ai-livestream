"""
AI Livestream Backend
"""

__version__ = "2.0.0"

# Lazy imports to avoid circular dependencies
def get_settings():
    from .core.config import get_settings
    return get_settings()

def get_logger(name: str = "ai-livestream"):
    from .core.logger import get_logger
    return get_logger(name)

__all__ = [
    "get_settings",
    "get_logger",
]
