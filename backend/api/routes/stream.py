"""
Stream API routes
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
import os
import subprocess
import threading
import time
import json

from api.app_state import get_streamer

router = APIRouter()

# 全局预览状态
_preview_state = {
    "is_running": False,
    "process": None,
    "current_source": None,
    "hls_dir": "/tmp/hls_preview",
    "start_time": None,
}


class StreamStartRequest(BaseModel):
    """Request to start streaming"""
    video_source: Optional[str] = None
    audio_source: Optional[str] = None
    platforms: Optional[List[str]] = None


class StreamResponse(BaseModel):
    """Stream status response"""
    status: str
    duration: float
    bitrate: str
    current_content: Optional[str] = None
    error_message: Optional[str] = None


class PreviewStartRequest(BaseModel):
    """Request to start preview"""
    source_url: Optional[str] = None  # HLS/RTMP/MP4 URL
    source_type: Optional[str] = "hls"  # hls, rtmp, file, test


@router.get("/status", response_model=StreamResponse)
async def get_status():
    """Get current stream status"""
    streamer = get_streamer()
    status = streamer.status

    return StreamResponse(
        status=status.status.value,
        duration=status.duration,
        bitrate=status.bitrate,
        current_content=status.current_content,
        error_message=status.error_message,
    )


@router.post("/start")
async def start_stream(request: StreamStartRequest):
    """Start streaming"""
    streamer = get_streamer()

    if streamer.is_running:
        raise HTTPException(status_code=400, detail="Stream is already running")

    if request.video_source:
        streamer.set_video_source(request.video_source)
    if request.audio_source:
        streamer.set_audio_source(request.audio_source)
    if request.platforms:
        streamer.platforms = request.platforms

    success = streamer.start()

    if not success:
        raise HTTPException(
            status_code=500,
            detail=streamer.status.error_message or "Failed to start stream"
        )

    return {"message": "Stream started", "status": streamer.status.to_dict()}


@router.post("/stop")
async def stop_stream():
    """Stop streaming"""
    streamer = get_streamer()

    if not streamer.is_running:
        raise HTTPException(status_code=400, detail="Stream is not running")

    success = streamer.stop()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop stream")

    return {"message": "Stream stopped"}


@router.post("/restart")
async def restart_stream():
    """Restart streaming"""
    streamer = get_streamer()
    success = streamer.restart()

    if not success:
        raise HTTPException(
            status_code=500,
            detail=streamer.status.error_message or "Failed to restart stream"
        )

    return {"message": "Stream restarted", "status": streamer.status.to_dict()}


# ============= 本地预览功能 =============

# 在线测试流 URL 列表
ONLINE_TEST_STREAMS = {
    "big_buck_bunny": {
        "name": "Big Buck Bunny",
        "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "type": "hls",
        "thumbnail": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Big_buck_bunny_poster_big.jpg/320px-Big_buck_bunny_poster_big.jpg"
    },
    "sintel": {
        "name": "Sintel",
        "url": "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8",
        "type": "hls",
        "thumbnail": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Sintel-poster.jpg/320px-Sintel-poster.jpg"
    },
    "tears_of_steel": {
        "name": "Tears of Steel",
        "url": "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
        "type": "hls",
        "thumbnail": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Tears_of_Steel_poster.jpg/320px-Tears_of_Steel_poster.jpg"
    },
    "test_pattern": {
        "name": "Test Pattern (FFmpeg)",
        "url": "internal://testsrc",
        "type": "internal",
        "thumbnail": None
    }
}


@router.get("/preview/sources")
async def get_preview_sources():
    """Get available preview sources"""
    return {
        "sources": ONLINE_TEST_STREAMS,
        "default": "big_buck_bunny"
    }


@router.get("/preview")
async def get_preview_info():
    """Get preview stream info - returns an online HLS stream URL for direct playback"""
    return {
        "status": "available",
        "message": "Use the HLS URLs directly in your player",
        "streams": ONLINE_TEST_STREAMS,
        "recommended_player": "HLS.js or video.js",
        "usage": {
            "direct_playback": "Use stream URL directly in HLS-capable player",
            "example": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
        }
    }


@router.get("/preview/current")
async def get_current_preview():
    """Get current preview stream URL"""
    if _preview_state["is_running"] and _preview_state["current_source"]:
        return {
            "is_running": True,
            "source": _preview_state["current_source"],
            "uptime": time.time() - _preview_state["start_time"] if _preview_state["start_time"] else 0
        }
    
    # 返回默认测试流
    return {
        "is_running": False,
        "source": ONLINE_TEST_STREAMS["big_buck_bunny"],
        "message": "Preview not started, returning default stream"
    }


@router.post("/preview/start")
async def start_preview(request: PreviewStartRequest = None):
    """Start preview stream - returns an HLS URL for the player"""
    global _preview_state
    
    # 确定要播放的源
    source_key = "big_buck_bunny"  # 默认
    if request and request.source_url:
        # 如果提供了 URL，直接使用
        source_info = {
            "name": "Custom Source",
            "url": request.source_url,
            "type": request.source_type or "hls"
        }
    else:
        # 使用预设源
        source_info = ONLINE_TEST_STREAMS.get(source_key, ONLINE_TEST_STREAMS["big_buck_bunny"])
    
    _preview_state["is_running"] = True
    _preview_state["current_source"] = source_info
    _preview_state["start_time"] = time.time()
    
    return {
        "success": True,
        "message": "Preview ready",
        "source": source_info,
        "player_url": source_info["url"],  # 前端直接播放这个 URL
        "hls_url": source_info["url"] if source_info["type"] == "hls" else None
    }


@router.post("/preview/stop")
async def stop_preview():
    """Stop preview stream"""
    global _preview_state
    
    _preview_state["is_running"] = False
    _preview_state["current_source"] = None
    _preview_state["start_time"] = None
    
    return {
        "success": True,
        "message": "Preview stopped"
    }


@router.get("/preview/playlist.m3u8")
async def get_preview_playlist():
    """Return a redirect to the HLS stream or generate one"""
    # 直接返回一个在线测试 HLS 流
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")
