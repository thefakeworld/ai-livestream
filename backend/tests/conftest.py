"""
Test configuration and fixtures
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
import os
import sys

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.absolute()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Set test environment before any imports
os.environ["DEBUG"] = "true"
os.environ["YOUTUBE_STREAM_KEY"] = "test-key-12345"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_dirs():
    """Create temporary directories for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    
    dirs = {
        "base": temp_dir,
        "assets": temp_dir / "assets",
        "output": temp_dir / "output",
        "logs": temp_dir / "logs",
        "music": temp_dir / "music",
        "video": temp_dir / "assets" / "video",
        "audio": temp_dir / "assets" / "audio",
        "news": temp_dir / "assets" / "news",
        "tts": temp_dir / "output" / "tts",
    }
    
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    
    yield dirs
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_app():
    """Create test FastAPI application"""
    from api.main import app
    return app


@pytest.fixture
async def async_client(test_app):
    """Create async HTTP client for testing"""
    from httpx import AsyncClient, ASGITransport
    
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test"
    ) as client:
        yield client
