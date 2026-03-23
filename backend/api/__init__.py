"""
FastAPI application module
"""

# Lazy import to avoid circular dependencies
def get_app():
    from .main import app
    return app

def get_streamer():
    from .app_state import get_streamer
    return get_streamer()

def get_director():
    from .app_state import get_director
    return get_director()

__all__ = ["get_app", "get_streamer", "get_director"]
