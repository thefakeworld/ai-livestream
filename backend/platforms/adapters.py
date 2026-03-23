"""
Platform adapters for various streaming platforms
"""

from platforms.base import PlatformAdapter, PlatformConfig, PlatformStatus
from platforms.youtube import YouTubeAdapter, create_youtube_adapter
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


class TikTokAdapter(PlatformAdapter):
    """TikTok Live streaming adapter"""

    @property
    def platform_type(self) -> str:
        return "tiktok"

    @property
    def display_name(self) -> str:
        return "TikTok"

    def get_ffmpeg_video_params(self) -> list:
        params = super().get_ffmpeg_video_params()
        # TikTok prefers 30fps and smaller keyframe interval
        params.extend([
            "-g", "30",
            "-keyint_min", "30",
        ])
        return params


class BilibiliAdapter(PlatformAdapter):
    """Bilibili (B站) Live streaming adapter"""

    @property
    def platform_type(self) -> str:
        return "bilibili"

    @property
    def display_name(self) -> str:
        return "B站 (Bilibili)"


class DouyinAdapter(PlatformAdapter):
    """Douyin (抖音) Live streaming adapter"""

    @property
    def platform_type(self) -> str:
        return "douyin"

    @property
    def display_name(self) -> str:
        return "抖音"

    def get_ffmpeg_video_params(self) -> list:
        params = super().get_ffmpeg_video_params()
        params.extend([
            "-g", "30",
            "-keyint_min", "30",
        ])
        return params


class TwitchAdapter(PlatformAdapter):
    """Twitch Live streaming adapter"""

    @property
    def platform_type(self) -> str:
        return "twitch"

    @property
    def display_name(self) -> str:
        return "Twitch"

    def get_ffmpeg_video_params(self) -> list:
        params = super().get_ffmpeg_video_params()
        # Twitch specific settings
        params.extend([
            "-profile:v", "high",
            "-level", "4.1",
        ])
        return params


class FacebookAdapter(PlatformAdapter):
    """Facebook Live streaming adapter"""

    @property
    def platform_type(self) -> str:
        return "facebook"

    @property
    def display_name(self) -> str:
        return "Facebook"


class KuaishouAdapter(PlatformAdapter):
    """Kuaishou (快手) Live streaming adapter"""

    @property
    def platform_type(self) -> str:
        return "kuaishou"

    @property
    def display_name(self) -> str:
        return "快手"


class HuyaAdapter(PlatformAdapter):
    """Huya (虎牙) Live streaming adapter"""

    @property
    def platform_type(self) -> str:
        return "huya"

    @property
    def display_name(self) -> str:
        return "虎牙"


class DouyuAdapter(PlatformAdapter):
    """Douyu (斗鱼) Live streaming adapter"""

    @property
    def platform_type(self) -> str:
        return "douyu"

    @property
    def display_name(self) -> str:
        return "斗鱼"


class XiaohongshuAdapter(PlatformAdapter):
    """Xiaohongshu (小红书) Live streaming adapter"""

    @property
    def platform_type(self) -> str:
        return "xiaohongshu"

    @property
    def display_name(self) -> str:
        return "小红书"

    def get_ffmpeg_video_params(self) -> list:
        params = super().get_ffmpeg_video_params()
        params.extend([
            "-g", "30",
            "-keyint_min", "30",
        ])
        return params


# Platform adapter registry
ADAPTER_REGISTRY: Dict[str, type] = {
    "youtube": YouTubeAdapter,
    "tiktok": TikTokAdapter,
    "bilibili": BilibiliAdapter,
    "douyin": DouyinAdapter,
    "twitch": TwitchAdapter,
    "facebook": FacebookAdapter,
    "kuaishou": KuaishouAdapter,
    "huya": HuyaAdapter,
    "douyu": DouyuAdapter,
    "xiaohongshu": XiaohongshuAdapter,
}


def create_adapter(platform_type: str, config: PlatformConfig) -> Optional[PlatformAdapter]:
    """Create a platform adapter by type"""
    adapter_class = ADAPTER_REGISTRY.get(platform_type)
    if adapter_class:
        return adapter_class(config)
    return None
