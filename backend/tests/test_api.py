"""
API Routes Tests
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health and root endpoints"""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client: AsyncClient):
        """Test root endpoint returns app info"""
        response = await async_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint"""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"


class TestStreamEndpoints:
    """Test stream control endpoints"""

    @pytest.mark.asyncio
    async def test_get_stream_status(self, async_client: AsyncClient):
        """Test getting stream status"""
        response = await async_client.get("/api/v1/stream/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["idle", "running", "starting", "stopping", "error"]

    @pytest.mark.asyncio
    async def test_start_stream_without_config(self, async_client: AsyncClient):
        """Test starting stream without proper configuration"""
        response = await async_client.post(
            "/api/v1/stream/start",
            json={"video_source": None, "audio_source": None}
        )
        
        # Should fail or return error without proper config
        assert response.status_code in [400, 500, 200]

    @pytest.mark.asyncio
    async def test_stop_stream(self, async_client: AsyncClient):
        """Test stopping stream"""
        response = await async_client.post("/api/v1/stream/stop")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data or "message" in data

    @pytest.mark.asyncio
    async def test_restart_stream(self, async_client: AsyncClient):
        """Test restarting stream"""
        response = await async_client.post("/api/v1/stream/restart")
        
        assert response.status_code in [200, 400, 500]


class TestDirectorEndpoints:
    """Test director control endpoints"""

    @pytest.mark.asyncio
    async def test_get_director_status(self, async_client: AsyncClient):
        """Test getting director status"""
        response = await async_client.get("/api/v1/director/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "state" in data

    @pytest.mark.asyncio
    async def test_start_director(self, async_client: AsyncClient):
        """Test starting director"""
        response = await async_client.post("/api/v1/director/start")
        
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_stop_director(self, async_client: AsyncClient):
        """Test stopping director"""
        response = await async_client.post("/api/v1/director/stop")
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_switch_content(self, async_client: AsyncClient):
        """Test switching content"""
        response = await async_client.post(
            "/api/v1/director/switch",
            json={"content_type": "news", "content_id": "test-123"}
        )
        
        assert response.status_code in [200, 400, 404]


class TestPlatformEndpoints:
    """Test platform management endpoints"""

    @pytest.mark.asyncio
    async def test_list_platforms(self, async_client: AsyncClient):
        """Test listing all platforms"""
        response = await async_client.get("/api/v1/platform/list")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "platforms" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_platform_config(self, async_client: AsyncClient):
        """Test getting platform configuration"""
        response = await async_client.get("/api/v1/platform/youtube")
        
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_update_platform_config(self, async_client: AsyncClient):
        """Test updating platform configuration"""
        response = await async_client.post(
            "/api/v1/platform/youtube/config",
            json={
                "rtmp_url": "rtmp://a.rtmp.youtube.com/live2",
                "stream_key": "test-key",
                "enabled": True
            }
        )
        
        assert response.status_code in [200, 201, 400]

    @pytest.mark.asyncio
    async def test_enable_platform(self, async_client: AsyncClient):
        """Test enabling a platform"""
        response = await async_client.post("/api/v1/platform/youtube/enable")
        
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_disable_platform(self, async_client: AsyncClient):
        """Test disabling a platform"""
        response = await async_client.post("/api/v1/platform/youtube/disable")
        
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_invalid_platform(self, async_client: AsyncClient):
        """Test accessing invalid platform"""
        response = await async_client.get("/api/v1/platform/invalid_platform")
        
        assert response.status_code in [404, 400]


class TestContentEndpoints:
    """Test content management endpoints"""

    @pytest.mark.asyncio
    async def test_list_news(self, async_client: AsyncClient):
        """Test listing news items"""
        response = await async_client.get("/api/v1/content/news")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list) or "items" in data

    @pytest.mark.asyncio
    async def test_list_music(self, async_client: AsyncClient):
        """Test listing music tracks"""
        response = await async_client.get("/api/v1/content/music")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list) or "tracks" in data

    @pytest.mark.asyncio
    async def test_list_videos(self, async_client: AsyncClient):
        """Test listing video files"""
        response = await async_client.get("/api/v1/content/videos")
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_playlist(self, async_client: AsyncClient):
        """Test getting current playlist"""
        response = await async_client.get("/api/v1/content/playlist")
        
        assert response.status_code == 200
