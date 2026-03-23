"""
Director API routes - 智能导播控制
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import os
from pathlib import Path

router = APIRouter()

# 全局状态
_director_state = {
    "is_running": False,
    "start_time": None,
    "current_content": None,
    "content_queue": [],
}

# 示例内容库 - 包含在线测试资源
SAMPLE_CONTENT = [
    # 视频内容
    {
        "type": "video",
        "id": "video_001",
        "name": "Big Buck Bunny",
        "title": "Big Buck Bunny - 开源动画短片",
        "duration": 634,
        "artist": None,
        "path": "/content/videos/big_buck_bunny.mp4",
        "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "thumbnail": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Big_buck_bunny_poster_big.jpg/320px-Big_buck_bunny_poster_big.jpg"
    },
    {
        "type": "video",
        "id": "video_002",
        "name": "Sintel Trailer",
        "title": "Sintel - Blender 开源电影",
        "duration": 888,
        "artist": None,
        "path": "/content/videos/sintel.mp4",
        "url": "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8",
        "thumbnail": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Sintel-poster.jpg/320px-Sintel-poster.jpg"
    },
    {
        "type": "video",
        "id": "video_003",
        "name": "Tears of Steel",
        "title": "Tears of Steel - 科幻短片",
        "duration": 734,
        "artist": None,
        "path": "/content/videos/tears_of_steel.mp4",
        "url": "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
        "thumbnail": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Tears_of_Steel_poster.jpg/320px-Tears_of_Steel_poster.jpg"
    },
    # 音乐内容
    {
        "type": "music",
        "id": "music_001",
        "name": "Relaxing Piano",
        "title": "轻松钢琴曲",
        "duration": 372,
        "artist": "SoundHelix",
        "path": "/content/music/relaxing_piano.mp3",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    },
    {
        "type": "music",
        "id": "music_002",
        "name": "Electronic Beat",
        "title": "电子节拍",
        "duration": 432,
        "artist": "SoundHelix",
        "path": "/content/music/electronic.mp3",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"
    },
    {
        "type": "music",
        "id": "music_003",
        "name": "Ambient Sounds",
        "title": "环境音乐",
        "duration": 389,
        "artist": "SoundHelix",
        "path": "/content/music/ambient.mp3",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
    },
    # 新闻内容
    {
        "type": "news",
        "id": "news_001",
        "name": "AI News",
        "title": "AI 技术突破：大语言模型进入新时代",
        "duration": 120,
        "artist": None,
        "path": "/content/news/ai_news.txt"
    },
    {
        "type": "news",
        "id": "news_002",
        "name": "Tech News",
        "title": "科技公司发布新一代产品",
        "duration": 90,
        "artist": None,
        "path": "/content/news/tech_news.txt"
    },
    # 图片内容（用于静态背景）
    {
        "type": "image",
        "id": "img_001",
        "name": "Nature Landscape",
        "title": "自然风景背景",
        "duration": 9999,
        "artist": None,
        "path": "/content/images/nature.jpg",
        "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920",
        "thumbnail": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=320"
    },
]


class DirectorStatus(BaseModel):
    """Director status response"""
    is_running: bool
    current_content: Optional[str] = None
    content_queue: List[Dict[str, Any]] = []
    uptime: float = 0


class ContentSwitchRequest(BaseModel):
    """Request to switch content"""
    content_type: str  # "news", "music", "video"
    content_id: Optional[str] = None


@router.get("", response_model=DirectorStatus)
@router.get("/", response_model=DirectorStatus)
async def get_director_root():
    """Get director status (root endpoint)"""
    uptime = 0
    if _director_state["is_running"] and _director_state["start_time"]:
        uptime = time.time() - _director_state["start_time"]
    
    return DirectorStatus(
        is_running=_director_state["is_running"],
        current_content=_director_state["current_content"],
        content_queue=_director_state["content_queue"],
        uptime=uptime
    )


class ActionRequest(BaseModel):
    """Request with action"""
    action: str
    data: Optional[Dict[str, Any]] = None


@router.post("")
@router.post("/")
async def director_action(request: ActionRequest):
    """Handle director actions (start, stop, next, switch)"""
    action = request.action
    
    if action == "start":
        return await start_director()
    elif action == "stop":
        return await stop_director()
    elif action == "next":
        return await switch_content(ContentSwitchRequest(content_type="next"))
    elif action == "switch":
        content_id = request.data.get("index") if request.data else None
        return await switch_content(ContentSwitchRequest(content_type="video", content_id=str(content_id) if content_id else None))
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")


@router.get("/status", response_model=DirectorStatus)
async def get_director_status():
    """Get director status"""
    return await get_director_root()


@router.post("/start")
async def start_director():
    """Start the director"""
    global _director_state
    _director_state["is_running"] = True
    _director_state["start_time"] = time.time()
    _director_state["current_content"] = SAMPLE_CONTENT[0]["title"] if SAMPLE_CONTENT else "示例直播内容"
    _director_state["content_queue"] = SAMPLE_CONTENT.copy()
    
    return {
        "success": True,
        "message": "Director started",
        "is_running": True,
        "preview_url": "/api/v1/stream/preview",  # 本地预览地址
        "preview_hls": "/api/v1/stream/preview.m3u8",  # HLS 预览地址
        "current_content": _director_state["current_content"],
        "content_count": len(_director_state["content_queue"])
    }


@router.post("/stop")
async def stop_director():
    """Stop the director"""
    global _director_state
    _director_state["is_running"] = False
    _director_state["start_time"] = None
    _director_state["current_content"] = None
    
    return {
        "success": True,
        "message": "Director stopped",
        "is_running": False
    }


@router.post("/switch")
async def switch_content(request: ContentSwitchRequest):
    """Switch to different content"""
    global _director_state
    
    # 查找内容
    content = None
    if request.content_id:
        for item in SAMPLE_CONTENT:
            if item["path"] == request.content_id or str(SAMPLE_CONTENT.index(item)) == request.content_id:
                content = item
                break
    
    if content:
        _director_state["current_content"] = content["title"]
        return {
            "success": True,
            "message": f"Switched to {content['title']}",
            "content": content
        }
    
    # 切换到下一个
    if _director_state["content_queue"]:
        next_item = _director_state["content_queue"].pop(0)
        _director_state["current_content"] = next_item["title"]
        _director_state["content_queue"].append(next_item)
        return {
            "success": True,
            "message": f"Switched to next: {next_item['title']}",
            "content": next_item
        }
    
    return {
        "success": True,
        "message": f"Switched to {request.content_type}",
        "content_id": request.content_id
    }


@router.get("/queue")
async def get_content_queue():
    """Get content queue"""
    return {
        "queue": SAMPLE_CONTENT,
        "total": len(SAMPLE_CONTENT),
        "news_count": len([x for x in SAMPLE_CONTENT if x["type"] == "news"]),
        "music_count": len([x for x in SAMPLE_CONTENT if x["type"] == "music"]),
        "video_count": len([x for x in SAMPLE_CONTENT if x["type"] == "video"]),
    }


@router.post("/queue/add")
async def add_to_queue(content_type: str, content_path: str):
    """Add content to queue"""
    new_item = {
        "type": content_type,
        "name": os.path.basename(content_path),
        "title": os.path.basename(content_path),
        "path": content_path,
        "duration": 120,
        "artist": None
    }
    SAMPLE_CONTENT.append(new_item)
    return {"success": True, "message": f"Added {content_type} to queue", "item": new_item}


@router.get("/content/list")
async def get_content_list():
    """Get all content"""
    return {
        "success": True,
        "data": SAMPLE_CONTENT,
        "total": len(SAMPLE_CONTENT)
    }
