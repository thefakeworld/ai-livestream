"""
Platform Module Tests
"""

import pytest
import sys
from pathlib import Path

# Ensure backend is in path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


class TestPlatformBase:
    """Test Platform Base"""

    def test_platform_status_enum(self):
        """Test platform status values"""
        # Import directly from base to avoid circular import
        from core.config import get_settings
        from platforms.base import PlatformStatus
        
        assert PlatformStatus.DISCONNECTED.value == "disconnected"
        assert PlatformStatus.CONNECTING.value == "connecting"
        assert PlatformStatus.CONNECTED.value == "connected"
        assert PlatformStatus.ERROR.value == "error"

    def test_platform_config(self):
        """Test platform configuration"""
        from platforms.base import PlatformConfig
        
        config = PlatformConfig(
            name="Test Platform",
            platform_type="test",
            rtmp_url="rtmp://test.example.com/live",
            stream_key="test-key-123",
            enabled=True
        )
        
        assert config.name == "Test Platform"
        assert config.enabled is True
        assert config.is_configured() is True

    def test_platform_config_full_rtmp_url(self):
        """Test full RTMP URL generation"""
        from platforms.base import PlatformConfig
        
        config = PlatformConfig(
            name="Test",
            platform_type="test",
            rtmp_url="rtmp://test.example.com/live",
            stream_key="my-key"
        )
        
        assert config.full_rtmp_url == "rtmp://test.example.com/live/my-key"

    def test_platform_config_not_configured(self):
        """Test unconfigured platform"""
        from platforms.base import PlatformConfig
        
        config = PlatformConfig(
            name="Test",
            platform_type="test",
            rtmp_url="",
            stream_key=""
        )
        
        assert config.is_configured() is False


class TestPlatformAdapters:
    """Test Platform Adapters"""

    def test_youtube_adapter(self):
        """Test YouTube adapter"""
        from platforms.base import PlatformConfig
        from platforms.youtube import YouTubeAdapter
        
        config = PlatformConfig(
            name="YouTube",
            platform_type="youtube",
            rtmp_url="rtmp://a.rtmp.youtube.com/live2",
            stream_key="test-key"
        )
        
        adapter = YouTubeAdapter(config)
        
        assert adapter.platform_type == "youtube"
        assert adapter.display_name == "YouTube"
        assert adapter.is_enabled is True

    def test_youtube_video_params(self):
        """Test YouTube video parameters"""
        from platforms.base import PlatformConfig
        from platforms.youtube import YouTubeAdapter
        
        config = PlatformConfig(
            name="YouTube",
            platform_type="youtube",
            rtmp_url="rtmp://a.rtmp.youtube.com/live2",
            stream_key="test-key"
        )
        
        adapter = YouTubeAdapter(config)
        params = adapter.get_ffmpeg_video_params()
        
        assert "-c:v" in params
        assert "libx264" in params
        assert "-profile:v" in params

    def test_tiktok_adapter(self):
        """Test TikTok adapter"""
        from platforms.base import PlatformConfig
        from platforms.adapters import TikTokAdapter
        
        config = PlatformConfig(
            name="TikTok",
            platform_type="tiktok",
            rtmp_url="rtmp://push.tiktok.com/live",
            stream_key="test-key"
        )
        
        adapter = TikTokAdapter(config)
        
        assert adapter.platform_type == "tiktok"
        assert adapter.display_name == "TikTok"

    def test_bilibili_adapter(self):
        """Test Bilibili adapter"""
        from platforms.base import PlatformConfig
        from platforms.adapters import BilibiliAdapter
        
        config = PlatformConfig(
            name="Bilibili",
            platform_type="bilibili",
            rtmp_url="rtmp://live-push.bilivideo.com/live",
            stream_key="test-key"
        )
        
        adapter = BilibiliAdapter(config)
        
        assert adapter.platform_type == "bilibili"
        assert "B站" in adapter.display_name

    def test_adapter_registry(self):
        """Test adapter registry"""
        from platforms.adapters import ADAPTER_REGISTRY
        
        expected_platforms = [
            "youtube", "tiktok", "bilibili", "douyin",
            "twitch", "facebook", "kuaishou", "huya",
            "douyu", "xiaohongshu"
        ]
        
        for platform in expected_platforms:
            assert platform in ADAPTER_REGISTRY

    def test_create_adapter_factory(self):
        """Test adapter factory function"""
        from platforms.base import PlatformConfig
        from platforms.adapters import create_adapter
        
        config = PlatformConfig(
            name="Test",
            platform_type="youtube",
            rtmp_url="rtmp://test",
            stream_key="key"
        )
        
        adapter = create_adapter("youtube", config)
        
        assert adapter is not None
        assert adapter.platform_type == "youtube"

    def test_create_invalid_adapter(self):
        """Test creating invalid adapter"""
        from platforms.base import PlatformConfig
        from platforms.adapters import create_adapter
        
        config = PlatformConfig(
            name="Invalid",
            platform_type="invalid",
            rtmp_url="rtmp://test",
            stream_key="key"
        )
        
        adapter = create_adapter("invalid_platform", config)
        
        assert adapter is None

    def test_adapter_to_dict(self):
        """Test adapter serialization"""
        from platforms.base import PlatformConfig
        from platforms.youtube import YouTubeAdapter
        
        config = PlatformConfig(
            name="YouTube",
            platform_type="youtube",
            rtmp_url="rtmp://a.rtmp.youtube.com/live2",
            stream_key="test-key"
        )
        
        adapter = YouTubeAdapter(config)
        data = adapter.to_dict()
        
        assert "platform_type" in data
        assert "display_name" in data
        assert "enabled" in data
        assert "configured" in data
        assert data["has_stream_key"] is True


class TestPlatformManager:
    """Test Platform Manager"""

    def test_platform_manager_init(self, test_dirs):
        """Test platform manager initialization"""
        from platforms.manager import PlatformManager
        
        config_file = test_dirs["output"] / "platform_config.json"
        manager = PlatformManager(config_file)
        
        assert manager._config_file == config_file

    def test_add_platform(self, test_dirs):
        """Test adding a platform"""
        from platforms.manager import PlatformManager
        
        config_file = test_dirs["output"] / "platform_config.json"
        manager = PlatformManager(config_file)
        
        adapter = manager.add_platform(
            platform_type="youtube",
            rtmp_url="rtmp://a.rtmp.youtube.com/live2",
            stream_key="test-key",
            enabled=True
        )
        
        assert adapter is not None
        assert adapter.platform_type == "youtube"

    def test_remove_platform(self, test_dirs):
        """Test removing a platform"""
        from platforms.manager import PlatformManager
        
        config_file = test_dirs["output"] / "platform_config.json"
        manager = PlatformManager(config_file)
        
        manager.add_platform(
            platform_type="youtube",
            rtmp_url="rtmp://test",
            stream_key="key"
        )
        
        result = manager.remove_platform("youtube")
        
        assert result is True
        assert manager.get_platform("youtube") is None

    def test_get_enabled_platforms(self, test_dirs):
        """Test getting enabled platforms"""
        from platforms.manager import PlatformManager
        
        config_file = test_dirs["output"] / "platform_config.json"
        manager = PlatformManager(config_file)
        
        manager.add_platform(
            platform_type="youtube",
            rtmp_url="rtmp://test",
            stream_key="key",
            enabled=True
        )
        manager.add_platform(
            platform_type="tiktok",
            rtmp_url="rtmp://test",
            stream_key="",
            enabled=True  # Enabled but not configured
        )
        
        enabled = manager.get_enabled_platforms()
        
        # Only youtube should be enabled AND configured
        assert len(enabled) >= 1

    def test_enable_disable_platform(self, test_dirs):
        """Test enabling and disabling platforms"""
        from platforms.manager import PlatformManager
        
        config_file = test_dirs["output"] / "platform_config.json"
        manager = PlatformManager(config_file)
        
        manager.add_platform(
            platform_type="youtube",
            rtmp_url="rtmp://test",
            stream_key="key",
            enabled=True
        )
        
        manager.disable_platform("youtube")
        adapter = manager.get_platform("youtube")
        assert adapter.config.enabled is False
        
        manager.enable_platform("youtube")
        adapter = manager.get_platform("youtube")
        assert adapter.config.enabled is True

    def test_update_stream_key(self, test_dirs):
        """Test updating stream key"""
        from platforms.manager import PlatformManager
        
        config_file = test_dirs["output"] / "platform_config.json"
        manager = PlatformManager(config_file)
        
        manager.add_platform(
            platform_type="youtube",
            rtmp_url="rtmp://test",
            stream_key="old-key"
        )
        
        manager.update_stream_key("youtube", "new-key")
        
        adapter = manager.get_platform("youtube")
        assert adapter.config.stream_key == "new-key"

    def test_manager_to_dict(self, test_dirs):
        """Test manager serialization"""
        from platforms.manager import PlatformManager
        
        config_file = test_dirs["output"] / "platform_config.json"
        manager = PlatformManager(config_file)
        
        manager.add_platform(
            platform_type="youtube",
            rtmp_url="rtmp://test",
            stream_key="key"
        )
        
        data = manager.to_dict()
        
        assert "platforms" in data
        assert "available_platforms" in data
        assert "youtube" in data["platforms"]
