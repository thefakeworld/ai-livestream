"""
Platform adapters module
"""

from .base import PlatformAdapter, PlatformConfig, PlatformStatus
from .adapters import (
    TikTokAdapter,
    BilibiliAdapter,
    DouyinAdapter,
    TwitchAdapter,
    FacebookAdapter,
    KuaishouAdapter,
    HuyaAdapter,
    DouyuAdapter,
    XiaohongshuAdapter,
    ADAPTER_REGISTRY,
    create_adapter,
)
from .youtube import YouTubeAdapter, create_youtube_adapter
from .manager import PlatformManager, get_platform_manager

__all__ = [
    "PlatformAdapter",
    "PlatformConfig",
    "PlatformStatus",
    "YouTubeAdapter",
    "TikTokAdapter",
    "BilibiliAdapter",
    "DouyinAdapter",
    "TwitchAdapter",
    "FacebookAdapter",
    "KuaishouAdapter",
    "HuyaAdapter",
    "DouyuAdapter",
    "XiaohongshuAdapter",
    "ADAPTER_REGISTRY",
    "create_adapter",
    "create_youtube_adapter",
    "PlatformManager",
    "get_platform_manager",
]
