#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Platform Streaming Configuration
多平台直播推流配置
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class PlatformStatus(Enum):
    """平台状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONNECTING = "connecting"

@dataclass
class StreamPlatform:
    """直播平台配置"""
    name: str                    # 平台名称
    rtmp_url: str               # RTMP 服务器地址
    stream_key: str             # 推流密钥
    enabled: bool = True        # 是否启用
    status: PlatformStatus = PlatformStatus.INACTIVE
    bitrate: str = "2500k"      # 码率
    fps: int = 30               # 帧率
    
    @property
    def full_url(self) -> str:
        """获取完整推流地址"""
        return f"{self.rtmp_url}/{self.stream_key}"
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "rtmp_url": self.rtmp_url,
            "stream_key": self.stream_key[:8] + "..." if len(self.stream_key) > 8 else self.stream_key,
            "enabled": self.enabled,
            "status": self.status.value,
            "bitrate": self.bitrate,
            "fps": self.fps
        }

# ==================== 预设平台配置 ====================

PLATFORM_PRESETS = {
    "youtube": StreamPlatform(
        name="YouTube",
        rtmp_url="rtmp://a.rtmp.youtube.com/live2",
        stream_key="hdb0-bxcg-ua45-hg30-78r0",  # 替换为你的密钥
        enabled=True
    ),
    
    "tiktok": StreamPlatform(
        name="TikTok",
        rtmp_url="rtmp://push.tiktok.com/live",
        stream_key="",  # 需要填写你的 TikTok 推流密钥
        enabled=False
    ),
    
    "bilibili": StreamPlatform(
        name="B站 (Bilibili)",
        rtmp_url="rtmp://live-push.bilivideo.com/live-bvc",
        stream_key="",  # 需要填写你的 B站 推流密钥
        enabled=False
    ),
    
    "douyin": StreamPlatform(
        name="抖音",
        rtmp_url="rtmp://push.douyin.com/live",
        stream_key="",  # 需要填写你的抖音推流密钥
        enabled=False
    ),
    
    "twitch": StreamPlatform(
        name="Twitch",
        rtmp_url="rtmp://live.twitch.tv/app",
        stream_key="",  # 需要填写你的 Twitch 推流密钥
        enabled=False
    ),
    
    "facebook": StreamPlatform(
        name="Facebook",
        rtmp_url="rtmps://live-api-s.facebook.com:443/rtmp",
        stream_key="",  # 需要填写你的 Facebook 推流密钥
        enabled=False
    ),
    
    "kuaishou": StreamPlatform(
        name="快手",
        rtmp_url="rtmp://live-push.kuaishou.com/live",
        stream_key="",  # 需要填写你的快手推流密钥
        enabled=False
    ),
    
    "huya": StreamPlatform(
        name="虎牙",
        rtmp_url="rtmp://live.huya.com/live",
        stream_key="",  # 需要填写你的虎牙推流密钥
        enabled=False
    ),
    
    "douyu": StreamPlatform(
        name="斗鱼",
        rtmp_url="rtmp://live.douyu.com/live",
        stream_key="",  # 需要填写你的斗鱼推流密钥
        enabled=False
    ),
    
    "xiaohongshu": StreamPlatform(
        name="小红书",
        rtmp_url="rtmp://live-push.xiaohongshu.com/live",
        stream_key="",  # 需要填写你的小红书推流密钥
        enabled=False
    ),
}

class MultiPlatformConfig:
    """多平台配置管理"""
    
    def __init__(self):
        self.platforms: Dict[str, StreamPlatform] = {}
        self._load_presets()
    
    def _load_presets(self):
        """加载预设配置"""
        for key, platform in PLATFORM_PRESETS.items():
            self.platforms[key] = platform
    
    def get_enabled_platforms(self) -> List[StreamPlatform]:
        """获取已启用的平台"""
        return [p for p in self.platforms.values() if p.enabled and p.stream_key]
    
    def enable_platform(self, platform_key: str, stream_key: str = None):
        """启用平台"""
        if platform_key in self.platforms:
            self.platforms[platform_key].enabled = True
            if stream_key:
                self.platforms[platform_key].stream_key = stream_key
    
    def disable_platform(self, platform_key: str):
        """禁用平台"""
        if platform_key in self.platforms:
            self.platforms[platform_key].enabled = False
    
    def set_stream_key(self, platform_key: str, stream_key: str):
        """设置推流密钥"""
        if platform_key in self.platforms:
            self.platforms[platform_key].stream_key = stream_key
    
    def get_platform(self, platform_key: str) -> Optional[StreamPlatform]:
        """获取平台配置"""
        return self.platforms.get(platform_key)
    
    def list_platforms(self) -> List[Dict]:
        """列出所有平台"""
        return [p.to_dict() for p in self.platforms.values()]
    
    def to_dict(self) -> Dict:
        return {
            "platforms": {k: p.to_dict() for k, p in self.platforms.items()},
            "enabled_count": len(self.get_enabled_platforms())
        }


# 全局配置实例
config = MultiPlatformConfig()

def get_config() -> MultiPlatformConfig:
    return config
