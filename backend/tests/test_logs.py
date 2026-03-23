"""
Logs API Tests
"""

import pytest
from httpx import AsyncClient


class TestLogsAPI:
    """Test logs API endpoints"""

    @pytest.mark.asyncio
    async def test_send_frontend_log(self, async_client: AsyncClient):
        """Test receiving frontend log"""
        response = await async_client.post(
            "/api/v1/logs/frontend",
            json={
                "timestamp": "2024-01-01T00:00:00Z",
                "level": "error",
                "message": "Test error message",
                "context": {"component": "TestComponent"},
                "error": "TestError: something went wrong",
                "stack": "at TestComponent.render",
                "url": "http://localhost:3000/test",
                "userAgent": "Mozilla/5.0",
                "sessionId": "test-session-123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "received" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_get_frontend_logs(self, async_client: AsyncClient):
        """Test getting frontend logs"""
        # First send a log
        await async_client.post(
            "/api/v1/logs/frontend",
            json={
                "timestamp": "2024-01-01T00:00:00Z",
                "level": "info",
                "message": "Test log for retrieval"
            }
        )
        
        # Then get logs
        response = await async_client.get("/api/v1/logs/frontend")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "total" in data
        assert isinstance(data["logs"], list)

    @pytest.mark.asyncio
    async def test_get_frontend_logs_with_limit(self, async_client: AsyncClient):
        """Test getting frontend logs with limit"""
        response = await async_client.get("/api/v1/logs/frontend?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["logs"]) <= 10

    @pytest.mark.asyncio
    async def test_clear_frontend_logs(self, async_client: AsyncClient):
        """Test clearing frontend logs"""
        response = await async_client.delete("/api/v1/logs/frontend")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_send_log_with_minimal_data(self, async_client: AsyncClient):
        """Test sending log with minimal data"""
        response = await async_client.post(
            "/api/v1/logs/frontend",
            json={
                "timestamp": "2024-01-01T00:00:00Z",
                "level": "warn",
                "message": "Minimal warning"
            }
        )
        
        assert response.status_code == 200
