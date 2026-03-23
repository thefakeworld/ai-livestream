"""
AI Agent API routes - 智能弹幕分析和响应
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import time
import random

router = APIRouter()


class DanmakuMessage(BaseModel):
    """弹幕消息模型"""
    id: str
    user: str
    content: str
    platform: str  # bilibili, douyin, youtube, tiktok, other
    timestamp: float
    avatar: Optional[str] = None


class IntentAnalysis(BaseModel):
    """意图分析结果"""
    intent_type: str  # switch_content, greeting, question, request, chat
    confidence: float
    action: Optional[Dict[str, Any]] = None
    reply: Optional[str] = None


class AIResponse(BaseModel):
    """AI 响应"""
    success: bool
    intents: List[IntentAnalysis] = []
    suggestions: List[Dict[str, Any]] = []


# Mock AI 意图识别 (实际应调用 z-ai-sdk)
def analyze_intent(message: str) -> IntentAnalysis:
    """分析弹幕意图"""
    message_lower = message.lower()
    
    # 切换内容意图
    switch_keywords = ["切歌", "换歌", "播放", "放首", "切视频", "换个", "next", "switch", "play"]
    for kw in switch_keywords:
        if kw in message_lower:
            # 尝试提取目标
            target = None
            if "周杰伦" in message:
                target = "周杰伦"
            elif "爵士" in message:
                target = "爵士"
            elif "下一个" in message or "next" in message_lower:
                target = "next"
            
            return IntentAnalysis(
                intent_type="switch_content",
                confidence=0.85 + random.random() * 0.1,
                action={"type": "switch_music" if "歌" in message or "music" in message_lower else "switch_video", "target": target},
                reply=f"检测到切换请求，是否切换到 {target or '下一个'}？"
            )
    
    # 打招呼意图
    greeting_keywords = ["主播好", "大家好", "hello", "hi", "你好", "晚上好", "早上好", "第一次来"]
    for kw in greeting_keywords:
        if kw in message_lower:
            return IntentAnalysis(
                intent_type="greeting",
                confidence=0.90 + random.random() * 0.08,
                reply=f"欢迎来到直播间！感谢关注～"
            )
    
    # 问题意图
    question_keywords = ["?", "？", "什么", "怎么", "为什么", "哪里", "who", "what", "how", "where", "why"]
    for kw in question_keywords:
        if kw in message_lower:
            return IntentAnalysis(
                intent_type="question",
                confidence=0.75 + random.random() * 0.15,
                reply="这是个好问题，让我想想..."
            )
    
    # 默认闲聊
    return IntentAnalysis(
        intent_type="chat",
        confidence=0.6 + random.random() * 0.2,
        reply=None
    )


@router.post("/analyze", response_model=AIResponse)
async def analyze_messages(messages: List[DanmakuMessage]):
    """批量分析弹幕意图"""
    intents = []
    suggestions = []
    
    for msg in messages[-10:]:  # 只分析最近 10 条
        intent = analyze_intent(msg.content)
        intents.append(intent)
        
        # 高置信度的建议才返回
        if intent.confidence > 0.8 and intent.reply:
            suggestions.append({
                "id": f"sug_{int(time.time()*1000)}_{random.randint(1000,9999)}",
                "type": intent.intent_type,
                "confidence": intent.confidence,
                "message": msg.dict(),
                "action": intent.action,
                "reply": intent.reply
            })
    
    return AIResponse(
        success=True,
        intents=intents,
        suggestions=suggestions
    )


@router.post("/respond")
async def generate_response(message: str, context: Optional[Dict[str, Any]] = None):
    """生成 AI 回复"""
    intent = analyze_intent(message)
    
    return {
        "success": True,
        "intent": intent.dict(),
        "reply": intent.reply or "收到！",
        "should_tts": intent.confidence > 0.85  # 高置信度时语音播报
    }


@router.get("/suggestions")
async def get_suggestions():
    """获取当前 AI 建议 (用于轮询)"""
    # 返回一些模拟建议
    return {
        "suggestions": [
            {
                "id": f"sug_{int(time.time())}_1",
                "type": "greeting",
                "confidence": 0.92,
                "message": {
                    "id": "m1",
                    "user": "新观众",
                    "content": "主播好，第一次来",
                    "platform": "bilibili",
                    "timestamp": time.time() * 1000
                },
                "reply": "欢迎新观众来到直播间！点个关注不迷路～"
            },
            {
                "id": f"sug_{int(time.time())}_2",
                "type": "switch_content",
                "confidence": 0.88,
                "message": {
                    "id": "m2",
                    "user": "粉丝A",
                    "content": "放首周杰伦的歌吧",
                    "platform": "bilibili",
                    "timestamp": time.time() * 1000
                },
                "action": {"type": "switch_music", "target": "周杰伦"},
                "reply": "检测到想听周杰伦的歌，是否切换到周杰伦歌单？"
            }
        ]
    }


@router.post("/suggestions/{suggestion_id}/accept")
async def accept_suggestion(suggestion_id: str):
    """接受 AI 建议"""
    # TODO: 实际执行动作
    return {
        "success": True,
        "message": f"Suggestion {suggestion_id} accepted",
        "executed": True
    }


@router.post("/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(suggestion_id: str):
    """忽略 AI 建议"""
    return {
        "success": True,
        "message": f"Suggestion {suggestion_id} dismissed"
    }
