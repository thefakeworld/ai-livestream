"""
Danmaku (弹幕) API routes
"""

from fastapi import APIRouter, HTTPException
from fastapi.websockets import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional
import time
import random
import asyncio
import json

router = APIRouter()


class DanmakuMessage(BaseModel):
    """弹幕消息"""
    id: str
    user: str
    content: str
    platform: str
    timestamp: float
    avatar: Optional[str] = None


# 模拟弹幕数据
MOCK_USERS = ["小明", "Alice", "观众甲", "粉丝B", "新用户", "老粉", "路人", "VIP用户"]
MOCK_MESSAGES = [
    "主播好！",
    "第一次来，关注了",
    "放首周杰伦的歌吧",
    "切歌切歌",
    "这个视频好看",
    "主播唱得不错",
    "什么时候直播",
    "点个关注",
    "666",
    "厉害了",
    "继续加油",
    "有什么推荐的内容吗",
    "下一个视频",
    "声音大一点",
    "画质不错",
]


def generate_mock_danmaku() -> DanmakuMessage:
    """生成模拟弹幕"""
    return DanmakuMessage(
        id=f"d{int(time.time()*1000)}_{random.randint(1000,9999)}",
        user=random.choice(MOCK_USERS),
        content=random.choice(MOCK_MESSAGES),
        platform=random.choice(["bilibili", "douyin", "youtube", "tiktok"]),
        timestamp=time.time() * 1000
    )


class ConnectionManager:
    """WebSocket 连接管理器"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@router.get("/history", response_model=List[DanmakuMessage])
async def get_danmaku_history(limit: int = 50, platform: Optional[str] = None):
    """获取弹幕历史"""
    messages = []
    for i in range(min(limit, 20)):
        msg = generate_mock_danmaku()
        if platform and msg.platform != platform:
            msg.platform = platform
        messages.append(msg)
    return messages


@router.post("/send")
async def send_danmaku(user: str, content: str, platform: str = "other"):
    """发送弹幕/回复"""
    msg = DanmakuMessage(
        id=f"d{int(time.time()*1000)}_{random.randint(1000,9999)}",
        user=user,
        content=content,
        platform=platform,
        timestamp=time.time() * 1000
    )
    
    # 广播给所有连接
    await manager.broadcast({
        "type": "danmaku",
        "data": msg.dict()
    })
    
    return {"success": True, "message": msg.dict()}


@router.websocket("/ws")
async def websocket_danmaku(websocket: WebSocket):
    """WebSocket 弹幕流"""
    await manager.connect(websocket)
    
    try:
        # 发送历史消息
        for _ in range(5):
            msg = generate_mock_danmaku()
            await websocket.send_json({
                "type": "danmaku",
                "data": msg.dict()
            })
        
        # 持续推送新弹幕
        while True:
            # 模拟每 2-5 秒收到一条弹幕
            await asyncio.sleep(random.uniform(2, 5))
            
            msg = generate_mock_danmaku()
            await websocket.send_json({
                "type": "danmaku",
                "data": msg.dict()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/stats")
async def get_danmaku_stats():
    """获取弹幕统计"""
    return {
        "total": random.randint(100, 1000),
        "per_minute": random.randint(5, 30),
        "platforms": {
            "bilibili": random.randint(50, 200),
            "douyin": random.randint(30, 150),
            "youtube": random.randint(20, 100),
            "tiktok": random.randint(10, 50),
        },
        "top_users": [
            {"user": "粉丝A", "count": random.randint(10, 50)},
            {"user": "Alice", "count": random.randint(10, 50)},
            {"user": "观众甲", "count": random.randint(10, 50)},
        ]
    }
