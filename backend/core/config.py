"""
AI Livestream Backend
Core configuration module
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict, List, Optional, Any
from functools import lru_cache
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    APP_NAME: str = "AI Livestream"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, alias="DEBUG")

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    ASSETS_DIR: Path = BASE_DIR / "assets"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    LOGS_DIR: Path = BASE_DIR / "logs"
    MUSIC_DIR: Path = BASE_DIR / "music"

    # Video settings
    VIDEO_WIDTH: int = 1280
    VIDEO_HEIGHT: int = 720
    VIDEO_FPS: int = 30
    VIDEO_BITRATE: str = "2500k"
    VIDEO_CODEC: str = "libx264"
    VIDEO_PRESET: str = "veryfast"

    # Audio settings
    AUDIO_BITRATE: str = "192k"
    AUDIO_SAMPLE_RATE: int = 44100
    AUDIO_CODEC: str = "aac"

    # Streaming settings
    STREAM_RETRY_COUNT: int = 3
    STREAM_RETRY_DELAY: int = 5
    STREAM_BUFFER_SIZE: str = "2M"

    # News settings
    NEWS_UPDATE_INTERVAL: int = 3600  # seconds
    NEWS_SOURCES: List[str] = [
        "https://news.google.com/rss?hl=zh-CN",
        "https://news.google.com/rss?hl=en&gl=US",
    ]
    MAX_NEWS_DURATION: int = 300  # seconds

    # Music settings
    MUSIC_INTERVAL_SECONDS: int = 30
    MUSIC_MAX_FILES: int = 50

    # TTS settings
    TTS_ENGINE: str = "edge-tts"  # edge-tts, z-ai
    TTS_VOICE: str = "zh-CN-XiaoxiaoNeural"
    TTS_RATE: str = "+0%"
    TTS_VOLUME: str = "+0%"

    # Director settings
    DIRECTOR_STATE_FILE: str = "director_state.json"
    CONTENT_SWITCH_COOLDOWN: int = 5  # seconds

    # Platform stream keys (from environment)
    YOUTUBE_STREAM_KEY: Optional[str] = None
    YOUTUBE_RTMP_URL: str = "rtmp://a.rtmp.youtube.com/live2"

    TIKTOK_STREAM_KEY: Optional[str] = None
    TIKTOK_RTMP_URL: str = "rtmp://push.tiktok.com/live"

    BILIBILI_STREAM_KEY: Optional[str] = None
    BILIBILI_RTMP_URL: str = "rtmp://live-push.bilivideo.com/live-bvc"

    DOUYIN_STREAM_KEY: Optional[str] = None
    DOUYIN_RTMP_URL: str = "rtmp://push.douyin.com/live"

    TWITCH_STREAM_KEY: Optional[str] = None
    TWITCH_RTMP_URL: str = "rtmp://live.twitch.tv/app"

    FACEBOOK_STREAM_KEY: Optional[str] = None
    FACEBOOK_RTMP_URL: str = "rtmp://live-api-s.facebook.com:443/rtmp"

    KUAISHOU_STREAM_KEY: Optional[str] = None
    KUAISHOU_RTMP_URL: str = "rtmp://live-push.kuaishou.com/live"

    HUYA_STREAM_KEY: Optional[str] = None
    HUYA_RTMP_URL: str = "rtmp://live-up.huya.com/live"

    DOUYU_STREAM_KEY: Optional[str] = None
    DOUYU_RTMP_URL: str = "rtmp://live.douyu.com/live"

    XIAOHONGSHU_STREAM_KEY: Optional[str] = None
    XIAOHONGSHU_RTMP_URL: str = "rtmp://live-push.xiaohongshu.com/live"

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # HTTP client
    HTTPX_TIMEOUT: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        for dir_path in [self.ASSETS_DIR, self.OUTPUT_DIR, self.LOGS_DIR, self.MUSIC_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Platform configurations
PLATFORM_CONFIGS: Dict[str, Dict[str, Any]] = {
    "youtube": {
        "name": "YouTube",
        "rtmp_url_env": "YOUTUBE_RTMP_URL",
        "stream_key_env": "YOUTUBE_STREAM_KEY",
        "default_rtmp": "rtmp://a.rtmp.youtube.com/live2",
        "video_params": {
            "preset": "veryfast",
            "g": 60,  # keyframe interval
            "keyint_min": 60,
        }
    },
    "tiktok": {
        "name": "TikTok",
        "rtmp_url_env": "TIKTOK_RTMP_URL",
        "stream_key_env": "TIKTOK_STREAM_KEY",
        "default_rtmp": "rtmp://push.tiktok.com/live",
        "video_params": {
            "preset": "veryfast",
            "g": 30,
        }
    },
    "bilibili": {
        "name": "B站 (Bilibili)",
        "rtmp_url_env": "BILIBILI_RTMP_URL",
        "stream_key_env": "BILIBILI_STREAM_KEY",
        "default_rtmp": "rtmp://live-push.bilivideo.com/live",
        "video_params": {
            "preset": "veryfast",
            "g": 60,
        }
    },
    "douyin": {
        "name": "抖音",
        "rtmp_url_env": "DOUYIN_RTMP_URL",
        "stream_key_env": "DOUYIN_STREAM_KEY",
        "default_rtmp": "rtmp://push.douyin.com/live",
        "video_params": {
            "preset": "veryfast",
            "g": 30,
        }
    },
    "twitch": {
        "name": "Twitch",
        "rtmp_url_env": "TWITCH_RTMP_URL",
        "stream_key_env": "TWITCH_STREAM_KEY",
        "default_rtmp": "rtmp://live.twitch.tv/app",
        "video_params": {
            "preset": "fast",
            "g": 60,
            "profile": "high",
        }
    },
    "facebook": {
        "name": "Facebook",
        "rtmp_url_env": "FACEBOOK_RTMP_URL",
        "stream_key_env": "FACEBOOK_STREAM_KEY",
        "default_rtmp": "rtmp://live-api-s.facebook.com:443/rtmp",
        "video_params": {
            "preset": "veryfast",
            "g": 60,
        }
    },
    "kuaishou": {
        "name": "快手",
        "rtmp_url_env": "KUAISHOU_RTMP_URL",
        "stream_key_env": "KUAISHOU_STREAM_KEY",
        "default_rtmp": "rtmp://live-push.kuaishou.com/live",
        "video_params": {
            "preset": "veryfast",
            "g": 30,
        }
    },
    "huya": {
        "name": "虎牙",
        "rtmp_url_env": "HUYA_RTMP_URL",
        "stream_key_env": "HUYA_STREAM_KEY",
        "default_rtmp": "rtmp://live-up.huya.com/live",
        "video_params": {
            "preset": "veryfast",
            "g": 60,
        }
    },
    "douyu": {
        "name": "斗鱼",
        "rtmp_url_env": "DOUYU_RTMP_URL",
        "stream_key_env": "DOUYU_STREAM_KEY",
        "default_rtmp": "rtmp://live.douyu.com/live",
        "video_params": {
            "preset": "veryfast",
            "g": 60,
        }
    },
    "xiaohongshu": {
        "name": "小红书",
        "rtmp_url_env": "XIAOHONGSHU_RTMP_URL",
        "stream_key_env": "XIAOHONGSHU_STREAM_KEY",
        "default_rtmp": "rtmp://live-push.xiaohongshu.com/live",
        "video_params": {
            "preset": "veryfast",
            "g": 30,
        }
    },
}
