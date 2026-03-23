"""
Platform management API routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from platforms import get_platform_manager, PlatformStatus

router = APIRouter()


class PlatformConfig(BaseModel):
    """Platform configuration model"""
    platform_type: str
    rtmp_url: str
    stream_key: str
    enabled: bool = True


class PlatformResponse(BaseModel):
    """Platform response model"""
    platform_type: str
    display_name: str
    enabled: bool
    configured: bool
    status: str
    has_stream_key: bool
    last_error: Optional[str] = None


# 平台显示名称映射（静态数据，避免实例化问题）
PLATFORM_DISPLAY_NAMES = {
    "youtube": "YouTube",
    "tiktok": "TikTok",
    "bilibili": "B站 (Bilibili)",
    "douyin": "抖音",
    "twitch": "Twitch",
    "facebook": "Facebook",
    "kuaishou": "快手",
    "huya": "虎牙",
    "douyu": "斗鱼",
    "xiaohongshu": "小红书",
}


@router.get("/list")
async def list_platforms():
    """List all platforms"""
    manager = get_platform_manager()
    return manager.to_dict()


@router.get("/available")
async def list_available_platforms():
    """List all available platform types"""
    from platforms import ADAPTER_REGISTRY
    return {
        "platforms": [
            {"type": p, "name": PLATFORM_DISPLAY_NAMES.get(p, p)}
            for p in ADAPTER_REGISTRY.keys()
        ]
    }


@router.get("/{platform_type}", response_model=PlatformResponse)
async def get_platform(platform_type: str):
    """Get specific platform info"""
    manager = get_platform_manager()
    platform = manager.get_platform(platform_type)

    if not platform:
        raise HTTPException(status_code=404, detail=f"Platform {platform_type} not found")

    return PlatformResponse(
        platform_type=platform.platform_type,
        display_name=platform.display_name,
        enabled=platform.config.enabled,
        configured=platform.config.is_configured(),
        status=platform.status.value,
        has_stream_key=bool(platform.config.stream_key),
        last_error=platform.last_error,
    )


@router.post("/add")
async def add_platform(config: PlatformConfig):
    """Add or update a platform"""
    manager = get_platform_manager()

    adapter = manager.add_platform(
        platform_type=config.platform_type,
        rtmp_url=config.rtmp_url,
        stream_key=config.stream_key,
        enabled=config.enabled
    )

    if not adapter:
        raise HTTPException(status_code=400, detail=f"Invalid platform type: {config.platform_type}")

    return {"message": f"Platform {config.platform_type} added", "platform": adapter.to_dict()}


@router.delete("/{platform_type}")
async def remove_platform(platform_type: str):
    """Remove a platform"""
    manager = get_platform_manager()
    success = manager.remove_platform(platform_type)

    if not success:
        raise HTTPException(status_code=404, detail=f"Platform {platform_type} not found")

    return {"message": f"Platform {platform_type} removed"}


@router.post("/{platform_type}/enable")
async def enable_platform(platform_type: str):
    """Enable a platform"""
    manager = get_platform_manager()
    success = manager.enable_platform(platform_type)

    if not success:
        raise HTTPException(status_code=404, detail=f"Platform {platform_type} not found")

    return {"message": f"Platform {platform_type} enabled"}


@router.post("/{platform_type}/disable")
async def disable_platform(platform_type: str):
    """Disable a platform"""
    manager = get_platform_manager()
    success = manager.disable_platform(platform_type)

    if not success:
        raise HTTPException(status_code=404, detail=f"Platform {platform_type} not found")

    return {"message": f"Platform {platform_type} disabled"}


@router.post("/{platform_type}/key")
async def update_stream_key(platform_type: str, stream_key: str):
    """Update stream key for a platform"""
    manager = get_platform_manager()
    success = manager.update_stream_key(platform_type, stream_key)

    if not success:
        raise HTTPException(status_code=404, detail=f"Platform {platform_type} not found")

    return {"message": f"Stream key updated for {platform_type}"}
