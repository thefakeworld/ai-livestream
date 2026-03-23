"""
Content management API routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path

router = APIRouter()


class ContentItem(BaseModel):
    """Content item model"""
    id: str
    type: str  # "video", "audio", "news", "music", "image", "template"
    name: str
    path: str
    url: Optional[str] = None  # Online URL
    duration: Optional[float] = None
    size: Optional[int] = None
    thumbnail: Optional[str] = None
    artist: Optional[str] = None
    description: Optional[str] = None


class ContentList(BaseModel):
    """Content list response"""
    videos: List[ContentItem] = []
    audios: List[ContentItem] = []
    news: List[ContentItem] = []
    music: List[ContentItem] = []
    images: List[ContentItem] = []
    templates: List[ContentItem] = []


# 在线测试视频资源 - 使用公开可用的测试视频
ONLINE_VIDEOS = [
    {
        "id": "video_001",
        "type": "video",
        "name": "Big Buck Bunny",
        "title": "Big Buck Bunny - 开源动画短片",
        "path": "/content/videos/big_buck_bunny.mp4",
        "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "duration": 634.0,
        "thumbnail": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Big_buck_bunny_poster_big.jpg/320px-Big_buck_bunny_poster_big.jpg",
        "description": "开源动画短片，适合测试直播推流"
    },
    {
        "id": "video_002",
        "type": "video",
        "name": "Sintel Trailer",
        "title": "Sintel - Blender 开源电影",
        "path": "/content/videos/sintel.mp4",
        "url": "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8",
        "duration": 888.0,
        "thumbnail": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Sintel-poster.jpg/320px-Sintel-poster.jpg",
        "description": "Blender基金会制作的开源电影"
    },
    {
        "id": "video_003",
        "type": "video",
        "name": "Tears of Steel",
        "title": "Tears of Steel - 科幻短片",
        "path": "/content/videos/tears_of_steel.mp4",
        "url": "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
        "duration": 734.0,
        "thumbnail": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Tears_of_Steel_poster.jpg/320px-Tears_of_Steel_poster.jpg",
        "description": "Blender制作的科幻短片"
    },
    {
        "id": "video_004",
        "type": "video",
        "name": "Test Pattern",
        "title": "FFmpeg 测试模式",
        "path": "/content/videos/test_pattern.mp4",
        "url": None,  # 使用 FFmpeg 内置生成
        "duration": 9999.0,
        "thumbnail": None,
        "description": "FFmpeg 生成的测试图案，无需外部资源"
    },
]

# 在线图片资源 - 公开的图片资源
ONLINE_IMAGES = [
    {
        "id": "img_001",
        "type": "image",
        "name": "Nature Landscape",
        "title": "自然风景",
        "path": "/content/images/nature.jpg",
        "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920",
        "thumbnail": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=320",
        "description": "壮丽的山脉风景，适合作为直播背景"
    },
    {
        "id": "img_002",
        "type": "image",
        "name": "City Skyline",
        "title": "城市天际线",
        "path": "/content/images/city.jpg",
        "url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1920",
        "thumbnail": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=320",
        "description": "现代都市夜景，适合科技类直播"
    },
    {
        "id": "img_003",
        "type": "image",
        "name": "Tech Abstract",
        "title": "科技抽象",
        "path": "/content/images/tech.jpg",
        "url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1920",
        "thumbnail": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=320",
        "description": "科技感抽象图案"
    },
    {
        "id": "img_004",
        "type": "image",
        "name": "News Studio",
        "title": "新闻演播室背景",
        "path": "/content/images/studio.jpg",
        "url": "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=1920",
        "thumbnail": "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=320",
        "description": "专业新闻演播室背景"
    },
    {
        "id": "img_005",
        "type": "image",
        "name": "Gradient Background",
        "title": "渐变背景",
        "path": "/content/images/gradient.jpg",
        "url": None,  # 使用 FFmpeg 生成
        "thumbnail": None,
        "description": "渐变色背景，FFmpeg 动态生成"
    },
]

# 在线音乐资源 - 公开的背景音乐
ONLINE_MUSIC = [
    {
        "id": "music_001",
        "type": "music",
        "name": "Relaxing Piano",
        "title": "轻松钢琴曲",
        "path": "/content/music/relaxing_piano.mp3",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "duration": 372.0,
        "artist": "SoundHelix",
        "thumbnail": None,
        "description": "轻松舒缓的钢琴音乐"
    },
    {
        "id": "music_002",
        "type": "music",
        "name": "Electronic Beat",
        "title": "电子节拍",
        "path": "/content/music/electronic.mp3",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "duration": 432.0,
        "artist": "SoundHelix",
        "thumbnail": None,
        "description": "动感电子音乐"
    },
    {
        "id": "music_003",
        "type": "music",
        "name": "Ambient Sounds",
        "title": "环境音乐",
        "path": "/content/music/ambient.mp3",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "duration": 389.0,
        "artist": "SoundHelix",
        "thumbnail": None,
        "description": "舒缓的环境背景音乐"
    },
    {
        "id": "music_004",
        "type": "music",
        "name": "Jazz Cafe",
        "title": "爵士咖啡",
        "path": "/content/music/jazz.mp3",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
        "duration": 412.0,
        "artist": "SoundHelix",
        "thumbnail": None,
        "description": "慵懒的爵士风格"
    },
    {
        "id": "music_005",
        "type": "music",
        "name": "Generated Tone",
        "title": "生成音调",
        "path": "/content/music/tone.mp3",
        "url": None,  # 使用 FFmpeg 生成
        "duration": 9999.0,
        "artist": "FFmpeg",
        "thumbnail": None,
        "description": "FFmpeg 生成的静音或测试音调"
    },
]

# 视频模板资源
ONLINE_TEMPLATES = [
    {
        "id": "tpl_001",
        "type": "template",
        "name": "News Lower Third",
        "title": "新闻字幕条模板",
        "path": "/content/templates/news_lower_third",
        "url": "local",
        "duration": 5.0,
        "thumbnail": None,
        "description": "新闻直播使用的底部字幕条动画"
    },
    {
        "id": "tpl_002",
        "type": "template",
        "name": "Breaking News",
        "title": "突发新闻模板",
        "path": "/content/templates/breaking_news",
        "url": "local",
        "duration": 3.0,
        "thumbnail": None,
        "description": "突发新闻警报动画"
    },
    {
        "id": "tpl_003",
        "type": "template",
        "name": "Logo Watermark",
        "title": "Logo 水印模板",
        "path": "/content/templates/logo_watermark",
        "url": "local",
        "duration": 9999.0,
        "thumbnail": None,
        "description": "右下角 Logo 水印模板"
    },
    {
        "id": "tpl_004",
        "type": "template",
        "name": "Countdown Timer",
        "title": "倒计时模板",
        "path": "/content/templates/countdown",
        "url": "local",
        "duration": 60.0,
        "thumbnail": None,
        "description": "直播开始倒计时动画"
    },
]

# 新闻内容示例
ONLINE_NEWS = [
    {
        "id": "news_001",
        "type": "news",
        "name": "AI News",
        "title": "AI 技术突破：大语言模型进入新时代",
        "path": "/content/news/ai_news.txt",
        "duration": 120.0,
        "artist": None,
        "thumbnail": None,
        "description": "人工智能领域最新进展"
    },
    {
        "id": "news_002",
        "type": "news",
        "name": "Tech News",
        "title": "科技公司发布新一代产品",
        "path": "/content/news/tech_news.txt",
        "duration": 90.0,
        "artist": None,
        "thumbnail": None,
        "description": "科技行业最新动态"
    },
    {
        "id": "news_003",
        "type": "news",
        "name": "Finance News",
        "title": "全球市场今日收盘分析",
        "path": "/content/news/finance_news.txt",
        "duration": 180.0,
        "artist": None,
        "thumbnail": None,
        "description": "金融市场分析"
    },
]


@router.get("/list", response_model=ContentList)
async def list_content():
    """List all available content including online test resources"""
    return ContentList(
        videos=[ContentItem(**v) for v in ONLINE_VIDEOS],
        audios=[ContentItem(**m) for m in ONLINE_MUSIC],
        news=[ContentItem(**n) for n in ONLINE_NEWS],
        music=[ContentItem(**m) for m in ONLINE_MUSIC],
        images=[ContentItem(**i) for i in ONLINE_IMAGES],
        templates=[ContentItem(**t) for t in ONLINE_TEMPLATES],
    )


@router.get("/news")
async def get_news():
    """Get latest news"""
    return {
        "news": ONLINE_NEWS,
        "count": len(ONLINE_NEWS)
    }


@router.post("/news/refresh")
async def refresh_news():
    """Refresh news from sources"""
    return {"message": "News refresh started"}


@router.get("/music")
async def get_music():
    """Get music playlist"""
    return {
        "music": ONLINE_MUSIC,
        "count": len(ONLINE_MUSIC)
    }


@router.post("/music/download")
async def download_music(query: str):
    """Download music by search query"""
    return {"message": f"Download started for: {query}"}


@router.get("/videos")
async def get_videos():
    """Get available videos"""
    return {
        "videos": ONLINE_VIDEOS,
        "count": len(ONLINE_VIDEOS)
    }


@router.get("/images")
async def get_images():
    """Get available images"""
    return {
        "images": ONLINE_IMAGES,
        "count": len(ONLINE_IMAGES)
    }


@router.get("/templates")
async def get_templates():
    """Get available templates"""
    return {
        "templates": ONLINE_TEMPLATES,
        "count": len(ONLINE_TEMPLATES)
    }


@router.get("/all")
async def get_all_content():
    """Get all content types in a single request"""
    return {
        "videos": ONLINE_VIDEOS,
        "images": ONLINE_IMAGES,
        "music": ONLINE_MUSIC,
        "news": ONLINE_NEWS,
        "templates": ONLINE_TEMPLATES,
        "counts": {
            "videos": len(ONLINE_VIDEOS),
            "images": len(ONLINE_IMAGES),
            "music": len(ONLINE_MUSIC),
            "news": len(ONLINE_NEWS),
            "templates": len(ONLINE_TEMPLATES),
        }
    }
