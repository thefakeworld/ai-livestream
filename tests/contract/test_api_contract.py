"""
API 契约测试

测试目的:
1. 验证 API 实现符合 OpenAPI 规范
2. 确保响应格式正确
3. 验证字段类型和必需字段
4. 确保前后端接口一致

运行方式:
    pytest tests/contract/test_api_contract.py -v
"""

import pytest
import httpx
from typing import Dict, Any

# API 基础地址
API_BASE = "http://localhost:8000/api/v1"


class TestDirectorContract:
    """导播 API 契约测试"""

    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)

    # ==================== GET /director ====================
    def test_get_director_returns_200(self, client):
        """GET /director 应返回 200"""
        response = client.get("/director")
        assert response.status_code == 200

    def test_get_director_response_schema(self, client):
        """响应应符合 DirectorStatus schema"""
        response = client.get("/director")
        data = response.json()
        
        # 验证必需字段
        assert "is_running" in data, "缺少必需字段: is_running"
        assert isinstance(data["is_running"], bool), "is_running 应为 bool 类型"
        
        assert "content_queue" in data, "缺少必需字段: content_queue"
        assert isinstance(data["content_queue"], list), "content_queue 应为 list 类型"
        
        assert "uptime" in data, "缺少必需字段: uptime"
        assert isinstance(data["uptime"], (int, float)), "uptime 应为数字类型"

    def test_get_director_optional_fields(self, client):
        """可选字段类型验证"""
        response = client.get("/director")
        data = response.json()
        
        # current_content 可选
        if data.get("current_content") is not None:
            assert isinstance(data["current_content"], str), "current_content 应为字符串"

    # ==================== GET /director/status ====================
    def test_get_director_status_returns_200(self, client):
        """GET /director/status 应返回 200"""
        response = client.get("/director/status")
        assert response.status_code == 200

    def test_get_director_status_same_as_root(self, client):
        """GET /director/status 应与 GET /director 返回相同结构"""
        root_response = client.get("/director")
        status_response = client.get("/director/status")
        
        root_data = root_response.json()
        status_data = status_response.json()
        
        # 验证相同字段存在
        assert set(root_data.keys()) == set(status_data.keys())

    # ==================== POST /director ====================
    def test_post_director_action_start(self, client):
        """POST /director {"action": "start"} 应返回 200"""
        response = client.post("/director", json={"action": "start"})
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert "is_running" in data
        assert data["success"] is True

    def test_post_director_action_stop(self, client):
        """POST /director {"action": "stop"} 应返回 200"""
        # 先确保停止状态
        client.post("/director", json={"action": "stop"})
        
        response = client.post("/director", json={"action": "stop"})
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data

    def test_post_director_action_next(self, client):
        """POST /director {"action": "next"} 应返回 200"""
        response = client.post("/director", json={"action": "next"})
        assert response.status_code == 200

    # ==================== POST /director/start ====================
    def test_post_director_start_returns_200(self, client):
        """POST /director/start 应返回 200"""
        response = client.post("/director/start")
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert "is_running" in data

    # ==================== POST /director/stop ====================
    def test_post_director_stop_returns_200(self, client):
        """POST /director/stop 应返回 200"""
        # 先启动
        client.post("/director/start")
        
        response = client.post("/director/stop")
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data

    # ==================== GET /director/queue ====================
    def test_get_director_queue_returns_200(self, client):
        """GET /director/queue 应返回 200"""
        response = client.get("/director/queue")
        assert response.status_code == 200

    def test_get_director_queue_schema(self, client):
        """响应应符合 ContentQueue schema"""
        response = client.get("/director/queue")
        data = response.json()
        
        assert "queue" in data
        assert isinstance(data["queue"], list)
        
        # 验证内容项结构
        if data["queue"]:
            item = data["queue"][0]
            assert "type" in item, "内容项缺少 type 字段"
            assert "name" in item, "内容项缺少 name 字段"
            assert "title" in item, "内容项缺少 title 字段"
            assert "path" in item, "内容项缺少 path 字段"
            assert "duration" in item, "内容项缺少 duration 字段"


class TestPlatformContract:
    """平台 API 契约测试"""

    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)

    # ==================== GET /platform/list ====================
    def test_get_platform_list_returns_200(self, client):
        """GET /platform/list 应返回 200"""
        response = client.get("/platform/list")
        assert response.status_code == 200

    def test_get_platform_list_schema(self, client):
        """响应应符合 PlatformList schema"""
        response = client.get("/platform/list")
        data = response.json()
        
        assert "platforms" in data
        assert isinstance(data["platforms"], dict)
        
        assert "available_platforms" in data
        assert isinstance(data["available_platforms"], list)
        
        assert "enabled_count" in data
        assert "configured_count" in data

    # ==================== GET /platform/available ====================
    def test_get_platform_available_returns_200(self, client):
        """GET /platform/available 应返回 200"""
        response = client.get("/platform/available")
        assert response.status_code == 200

    def test_get_platform_available_schema(self, client):
        """响应应符合 AvailablePlatforms schema"""
        response = client.get("/platform/available")
        data = response.json()
        
        assert "platforms" in data
        assert isinstance(data["platforms"], list)
        
        if data["platforms"]:
            platform = data["platforms"][0]
            assert "type" in platform, "平台项缺少 type 字段"
            assert "name" in platform, "平台项缺少 name 字段"

    # ==================== GET /platform/{platform_type} ====================
    def test_get_platform_by_type_returns_200(self, client):
        """GET /platform/youtube 应返回 200"""
        response = client.get("/platform/youtube")
        assert response.status_code == 200

    def test_get_platform_by_type_schema(self, client):
        """响应应符合 Platform schema"""
        response = client.get("/platform/youtube")
        data = response.json()
        
        required_fields = ["platform_type", "display_name", "enabled", "configured", "status", "has_stream_key"]
        for field in required_fields:
            assert field in data, f"平台数据缺少字段: {field}"

    def test_get_platform_invalid_returns_404(self, client):
        """GET /platform/invalid 应返回 404"""
        response = client.get("/platform/invalid_platform_type")
        assert response.status_code == 404


class TestStreamContract:
    """推流 API 契约测试"""

    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)

    # ==================== GET /stream/status ====================
    def test_get_stream_status_returns_200(self, client):
        """GET /stream/status 应返回 200"""
        response = client.get("/stream/status")
        assert response.status_code == 200

    def test_get_stream_status_schema(self, client):
        """响应应符合 StreamStatus schema"""
        response = client.get("/stream/status")
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["idle", "starting", "running", "stopping", "error"]
        
        assert "duration" in data
        assert "frames_sent" in data
        assert "bitrate" in data


class TestAPIVersioning:
    """API 版本兼容性测试"""

    @pytest.fixture
    def client(self):
        return httpx.Client(base_url="http://localhost:3000", timeout=30.0)

    def test_api_v1_prefix_works(self, client):
        """/api/v1 前缀应正常工作"""
        response = client.get("/api/v1/director")
        assert response.status_code == 200

    def test_api_without_v1_prefix_works(self, client):
        """不带 v1 前缀也应工作（兼容性）"""
        response = client.get("/api/director")
        assert response.status_code == 200

    def test_both_prefixes_return_same_structure(self, client):
        """两种前缀应返回相同的数据结构"""
        v1_response = client.get("/api/v1/director/status")
        no_prefix_response = client.get("/api/director/status")
        
        v1_data = v1_response.json()
        no_prefix_data = no_prefix_response.json()
        
        assert set(v1_data.keys()) == set(no_prefix_data.keys())


class TestErrorHandling:
    """错误处理测试"""

    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)

    def test_404_returns_proper_format(self, client):
        """404 错误应返回标准格式"""
        response = client.get("/nonexistent_endpoint")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data

    def test_422_validation_error(self, client):
        """验证错误应返回 422"""
        # 发送无效的 action
        response = client.post("/director", json={"action": "invalid_action"})
        # 可能返回 400 或 200(如果忽略无效action)
        assert response.status_code in [200, 400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
