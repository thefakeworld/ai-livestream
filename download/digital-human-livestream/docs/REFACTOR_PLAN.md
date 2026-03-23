# AI Livestream 项目重构方案

## 当前问题分析

### 1. 代码重复问题
| 位置 | 内容 | 问题 |
|------|------|------|
| `download/digital-human-livestream/` | Python 后端 + 运行时文件 | 包含日志、输出、venv 等 |
| `download/digital-human-livestream-project/backend/` | Python 后端 | 与上面重复 |
| `download/digital-human-livestream-project/frontend/` | Next.js 前端 | 独立副本 |
| `src/` | Next.js 前端 | 与上面重复 |

### 2. 模块职责不清
- 所有 Python 文件平铺在根目录
- 推流、TTS、新闻、视频等功能混杂
- 缺少清晰的模块边界

### 3. 配置分散
- `config.py` 和 `multi_platform_config.py` 分离
- 平台配置硬编码

### 4. 缺少标准化
- 无 Docker 支持
- 无 API 标准（仅前端 API route）
- 无统一日志管理

---

## 新架构设计

```
ai-livestream/
├── backend/                          # Python 后端服务
│   ├── core/                         # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py                 # 统一配置管理
│   │   ├── exceptions.py             # 自定义异常
│   │   └── logger.py                 # 日志配置
│   │
│   ├── services/                     # 业务服务
│   │   ├── __init__.py
│   │   ├── tts_service.py            # TTS 语音合成
│   │   ├── news_service.py           # 新闻抓取处理
│   │   ├── music_service.py          # 音乐管理
│   │   ├── video_service.py          # 视频合成
│   │   └── playlist_service.py       # 播放列表管理
│   │
│   ├── streaming/                    # 推流模块
│   │   ├── __init__.py
│   │   ├── base.py                   # 推流基类
│   │   ├── ffmpeg_streamer.py        # FFmpeg 推流实现
│   │   ├── realtime_streamer.py      # 实时推流
│   │   └── playlist_streamer.py      # 播放列表推流
│   │
│   ├── platforms/                    # 平台适配器
│   │   ├── __init__.py
│   │   ├── base.py                   # 平台基类
│   │   ├── youtube.py                # YouTube
│   │   ├── tiktok.py                 # TikTok
│   │   ├── bilibili.py               # B站
│   │   ├── douyin.py                 # 抖音
│   │   ├── twitch.py                 # Twitch
│   │   └── manager.py                # 多平台管理器
│   │
│   ├── director/                     # 智能导播系统
│   │   ├── __init__.py
│   │   ├── scheduler.py              # 内容调度
│   │   ├── state_manager.py          # 状态管理
│   │   └── content_switcher.py       # 内容切换
│   │
│   ├── api/                          # FastAPI 接口
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── stream.py             # 推流接口
│   │   │   ├── director.py           # 导播接口
│   │   │   ├── content.py            # 内容管理接口
│   │   │   └── platform.py           # 平台管理接口
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── stream.py             # 推流数据模型
│   │       └── platform.py           # 平台数据模型
│   │
│   ├── utils/                        # 工具函数
│   │   ├── __init__.py
│   │   ├── ffmpeg_utils.py           # FFmpeg 工具
│   │   ├── file_utils.py             # 文件工具
│   │   └── network_utils.py          # 网络工具
│   │
│   ├── requirements.txt              # Python 依赖
│   └── run.py                        # 启动入口
│
├── frontend/                         # Next.js 前端
│   ├── src/
│   │   ├── app/                      # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # 首页仪表盘
│   │   │   ├── director/
│   │   │   │   └── page.tsx          # 导播台页面
│   │   │   ├── platforms/
│   │   │   │   └── page.tsx          # 平台管理页面
│   │   │   └── api/                  # Next.js API Routes (可选代理)
│   │   │       └── proxy/
│   │   │           └── [...slug]/route.ts
│   │   ├── components/               # React 组件
│   │   │   ├── ui/                   # UI 组件 (shadcn)
│   │   │   ├── dashboard/            # 仪表盘组件
│   │   │   ├── director/             # 导播台组件
│   │   │   └── platform/             # 平台管理组件
│   │   ├── lib/                      # 工具库
│   │   │   ├── utils.ts
│   │   │   ├── api.ts                # API 客户端
│   │   │   └── websocket.ts          # WebSocket 客户端
│   │   └── hooks/                    # React Hooks
│   │       ├── useStreamStatus.ts
│   │       └── useDirector.ts
│   ├── public/                       # 静态资源
│   ├── package.json
│   ├── next.config.ts
│   └── tsconfig.json
│
├── docker/                           # Docker 配置
│   ├── Dockerfile.backend            # 后端镜像
│   ├── Dockerfile.frontend           # 前端镜像
│   └── nginx.conf                    # Nginx 配置
│
├── docs/                             # 文档
│   ├── README.md                     # 项目说明
│   ├── API.md                        # API 文档
│   ├── DEPLOYMENT.md                 # 部署指南
│   └── video-and-music.md            # 视频/音乐文档
│
├── scripts/                          # 脚本
│   ├── install.sh                    # 安装脚本
│   ├── start.sh                      # 启动脚本
│   └── docker-build.sh               # Docker 构建
│
├── docker-compose.yml                # Docker Compose
├── docker-compose.prod.yml           # 生产环境配置
└── README.md                         # 项目根文档
```

---

## 模块职责说明

### Backend Core (核心模块)
- **config.py**: 统一配置管理，支持环境变量覆盖
- **logger.py**: 结构化日志，支持文件和控制台输出
- **exceptions.py**: 自定义异常类型

### Backend Services (服务模块)
- **tts_service.py**: TTS 语音合成，支持多种 TTS 引擎
- **news_service.py**: 新闻抓取、解析、缓存
- **music_service.py**: 音乐下载、管理、播放列表
- **video_service.py**: 视频合成、处理
- **playlist_service.py**: 播放列表生成和管理

### Backend Streaming (推流模块)
- **base.py**: 推流基类，定义接口
- **ffmpeg_streamer.py**: FFmpeg 推流实现
- **realtime_streamer.py**: 实时推流
- **playlist_streamer.py**: 播放列表推流

### Backend Platforms (平台适配)
- **base.py**: 平台适配器基类
- **youtube.py/tiktok.py/...**: 各平台实现
- **manager.py**: 多平台统一管理

### Backend Director (导播系统)
- **scheduler.py**: 内容调度器
- **state_manager.py**: 状态管理
- **content_switcher.py**: 内容切换逻辑

### Backend API (接口层)
- FastAPI 提供标准化 REST API
- WebSocket 支持实时状态推送

---

## 重构步骤

### Phase 1: 目录结构创建
1. 创建新的目录结构
2. 移动现有代码到对应模块
3. 添加 `__init__.py` 文件

### Phase 2: 模块整合
1. 合并重复配置到 `core/config.py`
2. 重构推流模块，继承基类
3. 统一平台配置管理

### Phase 3: API 标准化
1. 创建 FastAPI 应用
2. 定义标准数据模型
3. 实现 REST 接口

### Phase 4: 前端优化
1. 整合前端代码
2. 创建 API 客户端
3. 添加 WebSocket 支持

### Phase 5: 部署配置
1. 创建 Dockerfile
2. 编写 docker-compose.yml
3. 测试部署流程

---

## 配置文件示例

### backend/core/config.py
```python
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    # 基础配置
    APP_NAME: str = "AI Livestream"
    DEBUG: bool = False

    # 视频配置
    VIDEO_WIDTH: int = 1280
    VIDEO_HEIGHT: int = 720
    VIDEO_FPS: int = 30
    VIDEO_BITRATE: str = "2500k"

    # 音频配置
    AUDIO_BITRATE: str = "192k"
    AUDIO_SAMPLE_RATE: int = 44100

    # 推流配置
    STREAM_RETRY_COUNT: int = 3
    STREAM_RETRY_DELAY: int = 5

    # 新闻配置
    NEWS_UPDATE_INTERVAL: int = 3600
    NEWS_SOURCES: List[str] = [
        "https://news.google.com/rss?hl=zh-CN"
    ]

    # TTS 配置
    TTS_ENGINE: str = "edge-tts"  # edge-tts, z-ai
    TTS_VOICE: str = "zh-CN-XiaoxiaoNeural"

    # 平台配置 (从环境变量读取)
    YOUTUBE_STREAM_KEY: Optional[str] = None
    TIKTOK_STREAM_KEY: Optional[str] = None
    BILIBILI_STREAM_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### backend/platforms/base.py
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class PlatformConfig:
    name: str
    rtmp_url: str
    stream_key: str
    enabled: bool = True

class PlatformAdapter(ABC):
    """平台适配器基类"""

    def __init__(self, config: PlatformConfig):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """平台名称"""
        pass

    @property
    @abstractmethod
    def rtmp_url(self) -> str:
        """RTMP 推流地址"""
        pass

    def get_stream_url(self) -> str:
        """获取完整推流地址"""
        return f"{self.rtmp_url}/{self.config.stream_key}"

    @abstractmethod
    def get_ffmpeg_params(self) -> list:
        """获取平台特定的 FFmpeg 参数"""
        pass
```

---

## 预期收益

### 代码质量
- 消除重复代码，减少维护成本
- 清晰的模块边界，便于单元测试
- 标准化接口，便于扩展

### 可维护性
- 统一配置管理，便于环境切换
- 结构化日志，便于问题排查
- 模块化设计，便于功能扩展

### 部署便利
- Docker 支持，一键部署
- 环境隔离，避免依赖冲突
- 可水平扩展，支持高可用

### 开发效率
- 前后端分离，并行开发
- API 标准化，便于对接
- 文档完善，降低上手成本
