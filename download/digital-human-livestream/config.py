#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Digital Human YouTube Livestream - Configuration
数字人YouTube直播配置文件
"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.absolute()

# ==================== YouTube 推流配置 ====================
YOUTUBE_RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"
YOUTUBE_STREAM_KEY = "hdb0-bxcg-ua45-hg30-78r0"

# 完整推流地址
RTMP_PUSH_URL = f"{YOUTUBE_RTMP_URL}/{YOUTUBE_STREAM_KEY}"

# ==================== 视频配置 ====================
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 30
VIDEO_BITRATE = "2500k"

# 视频模板路径
VIDEO_TEMPLATE_PATH = BASE_DIR / "assets" / "video" / "template.mp4"
# 静态数字人图片路径（如果没有视频模板）
DIGITAL_HUMAN_IMAGE = BASE_DIR / "assets" / "video" / "digital_human.png"

# ==================== 音频配置 ====================
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 2
AUDIO_BITRATE = "128k"

# 背景音乐目录
BG_MUSIC_DIR = BASE_DIR / "assets" / "audio" / "music"
# 音乐间隔时间（秒）
MUSIC_INTERVAL_SECONDS = 30

# ==================== 新闻抓取配置 ====================
NEWS_SOURCES = [
    # RSS 源
    "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "https://www.reddit.com/r/worldnews/.rss",
    # 可添加更多RSS源
]

# 新闻更新间隔（秒）
NEWS_UPDATE_INTERVAL = 3600  # 1小时更新一次

# 每次抓取新闻数量
NEWS_COUNT_PER_FETCH = 10

# 新闻缓存目录
NEWS_CACHE_DIR = BASE_DIR / "assets" / "news"

# ==================== TTS 配置 ====================
TTS_OUTPUT_DIR = BASE_DIR / "output" / "tts"
# TTS 语速
TTS_SPEED = 1.0

# ==================== 输出配置 ====================
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# ==================== 播放控制配置 ====================
# 新闻循环次数后更新新闻
NEWS_LOOP_COUNT = 3
# 单条新闻最大时长（秒）
MAX_NEWS_DURATION = 120

# ==================== FFmpeg 配置 ====================
FFMPEG_PRESET = "veryfast"
FFMPEG_THREADS = 4

# ==================== 日志配置 ====================
LOG_LEVEL = "INFO"
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# 确保所有目录存在
for dir_path in [NEWS_CACHE_DIR, TTS_OUTPUT_DIR, OUTPUT_DIR, LOGS_DIR, BG_MUSIC_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
