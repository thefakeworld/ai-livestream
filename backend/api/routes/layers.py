"""
Layer API routes - 图层管理接口
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
import os

from streaming.layer_compositor import LayerType, LayerOptions, Layer, get_compositor

router = APIRouter()


class LayerTypeEnum(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio"


class LayerOptionsRequest(BaseModel):
    """图层选项请求"""
    position_x: Optional[int] = 0
    position_y: Optional[int] = 0
    width: Optional[int] = None
    height: Optional[int] = None
    opacity: Optional[float] = 1.0
    font_size: Optional[int] = 48
    font_color: Optional[str] = "white"
    font_family: Optional[str] = "Arial"
    volume: Optional[float] = 1.0


class LayerCreateRequest(BaseModel):
    """创建图层请求"""
    id: str
    type: LayerTypeEnum
    name: str
    source: str  # 文件路径或URL
    visible: Optional[bool] = True
    order: Optional[int] = 0
    options: Optional[LayerOptionsRequest] = None


class LayerUpdateRequest(BaseModel):
    """更新图层请求"""
    visible: Optional[bool] = None
    order: Optional[int] = None
    name: Optional[str] = None
    source: Optional[str] = None
    options: Optional[LayerOptionsRequest] = None


class LayerResponse(BaseModel):
    """图层响应"""
    id: str
    type: str
    name: str
    source: str
    visible: bool
    order: int
    options: Dict[str, Any]


class LayerListResponse(BaseModel):
    """图层列表响应"""
    layers: List[LayerResponse]
    total: int
    visible_count: int


@router.get("", response_model=LayerListResponse)
async def list_layers():
    """获取所有图层"""
    compositor = get_compositor()
    layers = compositor.get_all_layers()
    
    return LayerListResponse(
        layers=[LayerResponse(**l.to_dict()) for l in layers],
        total=len(layers),
        visible_count=len([l for l in layers if l.visible]),
    )


@router.get("/{layer_id}", response_model=LayerResponse)
async def get_layer(layer_id: str):
    """获取单个图层"""
    compositor = get_compositor()
    layer = compositor.get_layer(layer_id)
    
    if not layer:
        raise HTTPException(status_code=404, detail=f"Layer {layer_id} not found")
    
    return LayerResponse(**layer.to_dict())


@router.post("/add", response_model=LayerResponse)
async def add_layer(request: LayerCreateRequest):
    """添加图层"""
    compositor = get_compositor()
    
    # 创建 Layer 对象
    options = LayerOptions()
    if request.options:
        options = LayerOptions(
            position_x=request.options.position_x or 0,
            position_y=request.options.position_y or 0,
            width=request.options.width,
            height=request.options.height,
            opacity=max(0, min(1, request.options.opacity or 1.0)),
            font_size=request.options.font_size or 48,
            font_color=request.options.font_color or "white",
            font_family=request.options.font_family or "Arial",
            volume=max(0, min(2, request.options.volume or 1.0)),
        )
    
    layer = Layer(
        id=request.id,
        type=LayerType(request.type.value),
        name=request.name,
        source=request.source,
        visible=request.visible or True,
        order=request.order or 0,
        options=options,
    )
    
    success = compositor.add_layer(layer)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add layer")
    
    return LayerResponse(**layer.to_dict())


@router.post("/update/{layer_id}", response_model=LayerResponse)
async def update_layer(layer_id: str, request: LayerUpdateRequest):
    """更新图层属性"""
    compositor = get_compositor()
    
    # 构建更新字典
    update_dict: Dict[str, Any] = {}
    if request.visible is not None:
        update_dict["visible"] = request.visible
    if request.order is not None:
        update_dict["order"] = request.order
    if request.name is not None:
        update_dict["name"] = request.name
    if request.source is not None:
        update_dict["source"] = request.source
    if request.options:
        update_dict["options"] = request.options.dict()
    
    success = compositor.update_layer(layer_id, update_dict)
    if not success:
        raise HTTPException(status_code=404, detail=f"Layer {layer_id} not found")
    
    layer = compositor.get_layer(layer_id)
    return LayerResponse(**layer.to_dict())


@router.delete("/{layer_id}")
async def remove_layer(layer_id: str):
    """移除图层"""
    compositor = get_compositor()
    success = compositor.remove_layer(layer_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Layer {layer_id} not found")
    
    return {"success": True, "message": f"Layer {layer_id} removed"}


@router.post("/reorder")
async def reorder_layers(layer_ids: List[str]):
    """重新排序图层"""
    compositor = get_compositor()
    
    for i, layer_id in enumerate(layer_ids):
        compositor.update_layer(layer_id, {"order": i})
    
    return {"success": True, "message": f"Reordered {len(layer_ids)} layers"}


@router.post("/clear")
async def clear_layers():
    """清除所有图层"""
    compositor = get_compositor()
    compositor.clear_layers()
    return {"success": True, "message": "All layers cleared"}


# 预设图层模板
LAYER_TEMPLATES = {
    "logo": {
        "name": "Logo 水印",
        "type": "image",
        "default_options": {"position_x": 1700, "position_y": 20, "width": 200, "height": 100},
    },
    "subtitle": {
        "name": "底部字幕",
        "type": "text",
        "default_options": {"position_x": 100, "position_y": 1000, "font_size": 48},
    },
    "news_ticker": {
        "name": "新闻滚动条",
        "type": "text",
        "default_options": {"position_x": 0, "position_y": 1040, "font_size": 32},
    },
    "background_music": {
        "name": "背景音乐",
        "type": "audio",
        "default_options": {"volume": 0.3},
    },
}


@router.get("/templates/list")
async def list_templates():
    """获取图层模板列表"""
    return {"templates": LAYER_TEMPLATES}


@router.post("/templates/apply/{template_name}")
async def apply_template(template_name: str, source: str, layer_id: Optional[str] = None):
    """应用图层模板"""
    if template_name not in LAYER_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
    
    template = LAYER_TEMPLATES[template_name]
    compositor = get_compositor()
    
    import time
    layer = Layer(
        id=layer_id or f"{template_name}_{int(time.time()*1000)}",
        type=LayerType(template["type"]),
        name=template["name"],
        source=source,
        visible=True,
        order=len(compositor.get_all_layers()),
        options=LayerOptions(**template["default_options"]),
    )
    
    compositor.add_layer(layer)
    return {"success": True, "layer": layer.to_dict()}


# ========== 合成控制 ==========

@router.post("/composition/start")
async def start_composition(duration: float = 3600):
    """开始图层合成输出 - 生成 HLS 流"""
    compositor = get_compositor()
    success = compositor.start_composite(duration=duration)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start composition")
    
    return {
        "success": True,
        "message": "Composition started",
        "hls_url": "/api/v1/layers/hls/stream.m3u8",
        "status": compositor.get_status()
    }


@router.post("/composition/stop")
async def stop_composition():
    """停止图层合成"""
    compositor = get_compositor()
    success = compositor.stop_composite()
    
    return {"success": success, "message": "Composition stopped"}


@router.get("/composition/status")
async def get_composition_status():
    """获取合成状态"""
    compositor = get_compositor()
    return compositor.get_status()


# ========== HLS 流服务 ==========

HLS_DIR = "/tmp/hls_stream"


@router.get("/hls/stream.m3u8")
async def get_hls_playlist():
    """获取 HLS 播放列表"""
    playlist_path = os.path.join(HLS_DIR, "stream.m3u8")
    if not os.path.exists(playlist_path):
        raise HTTPException(status_code=404, detail="HLS stream not available. Start composition first.")
    
    return FileResponse(
        playlist_path,
        media_type="application/vnd.apple.mpegurl",
        headers={"Cache-Control": "no-cache"}
    )


@router.get("/hls/{segment_name}")
async def get_hls_segment(segment_name: str):
    """获取 HLS 分片"""
    segment_path = os.path.join(HLS_DIR, segment_name)
    if not os.path.exists(segment_path):
        raise HTTPException(status_code=404, detail=f"Segment {segment_name} not found")
    
    return FileResponse(
        segment_path,
        media_type="video/MP2T",
        headers={"Cache-Control": "public, max-age=3600"}
    )


# ========== 预览快照 ==========

@router.get("/preview")
async def get_preview_info():
    """获取预览信息"""
    compositor = get_compositor()
    status = compositor.get_status()
    
    return {
        "status": status,
        "hls_available": os.path.exists(os.path.join(HLS_DIR, "stream.m3u8")),
        "preview_url": "/api/v1/layers/hls/stream.m3u8" if status["is_running"] else None,
        "instructions": {
            "start": "POST /api/v1/layers/composition/start",
            "stop": "POST /api/v1/layers/composition/stop",
            "status": "GET /api/v1/layers/composition/status",
        }
    }
