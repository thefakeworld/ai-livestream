# AI Livestream - AI 数字人直播系统

一个模块化、可扩展的 AI 数字人直播系统，支持多平台推流、智能导播、内容管理。

## ✨ 特性

- 🎬 **多平台推流**: 支持 YouTube、TikTok、B站、抖音、Twitch、Facebook、快手、虎牙、斗鱼、小红书
- 🎙️ **智能 TTS**: 支持多种语音引擎，生成自然的语音播报
- 📰 **新闻自动抓取**: 从 RSS 源自动获取新闻内容
- 🎵 **音乐管理**: 自动下载和管理背景音乐
- 🎥 **视频合成**: 自动合成数字人视频
- 🎛️ **导播台**: 实时切换内容，智能调度
- 🔄 **无人值守**: 支持长时间自动运行

## 📁 项目结构

```
ai-livestream/
├── backend/                    # Python 后端
│   ├── api/                   # FastAPI 路由
│   │   ├── routes/           # API 端点
│   │   │   ├── stream.py     # 推流控制
│   │   │   ├── director.py   # 导播台
│   │   │   ├── content.py    # 内容管理
│   │   │   └── platform.py   # 平台配置
│   │   └── main.py           # FastAPI 应用
│   ├── core/                  # 核心模块
│   │   ├── config.py         # 配置管理
│   │   ├── logger.py         # 日志系统
│   │   └── exceptions.py     # 自定义异常
│   ├── services/              # 业务服务
│   │   ├── tts_service.py    # TTS 服务
│   │   ├── news_service.py   # 新闻服务
│   │   ├── music_service.py  # 音乐服务
│   │   ├── video_service.py  # 视频服务
│   │   └── playlist_service.py # 播放列表服务
│   ├── streaming/             # 推流模块
│   │   ├── base.py           # 基础流类
│   │   └── ffmpeg_streamer.py # FFmpeg 实现
│   ├── platforms/             # 平台适配器
│   │   ├── base.py           # 平台基类
│   │   ├── adapters.py       # 各平台适配
│   │   ├── youtube.py        # YouTube 适配
│   │   └── manager.py        # 平台管理器
│   ├── director/              # 导播模块
│   ├── run.py                 # 启动入口
│   └── requirements.txt       # Python 依赖
├── frontend/                   # Next.js 前端
│   ├── src/
│   │   ├── app/              # 页面
│   │   ├── components/       # 组件
│   │   └── lib/              # 工具库
│   └── package.json
├── docker/                     # Docker 配置
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

**后端 (Python 3.8+)**:
```bash
cd backend
pip install -r requirements.txt
```

**前端 (Node.js 18+)**:
```bash
cd frontend
npm install
```

**系统依赖**:
```bash
# FFmpeg (必需)
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS

# yt-dlp (音乐下载可选)
pip install yt-dlp
```

### 2. 配置

创建 `.env` 文件:
```env
# YouTube
YOUTUBE_STREAM_KEY=your-stream-key
YOUTUBE_RTMP_URL=rtmp://a.rtmp.youtube.com/live2

# B站
BILIBILI_STREAM_KEY=your-stream-key
BILIBILI_RTMP_URL=rtmp://live-push.bilivideo.com/live

# 抖音
DOUYIN_STREAM_KEY=your-stream-key
DOUYIN_RTMP_URL=rtmp://push.douyin.com/live

# 其他平台...
```

### 3. 运行

**开发模式**:
```bash
# 后端
cd backend
python run.py --reload --debug

# 前端
cd frontend
npm run dev
```

**生产模式**:
```bash
# 后端
cd backend
python run.py --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm run build
npm start
```

## 📡 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/stream/start` | POST | 开始推流 |
| `/api/v1/stream/stop` | POST | 停止推流 |
| `/api/v1/stream/status` | GET | 获取推流状态 |
| `/api/v1/director/start` | POST | 启动导播台 |
| `/api/v1/director/switch` | POST | 切换内容 |
| `/api/v1/platform/list` | GET | 获取平台列表 |
| `/api/v1/platform/config` | POST | 配置平台 |
| `/api/v1/content/news` | GET | 获取新闻列表 |
| `/api/v1/content/music` | GET | 获取音乐列表 |

完整 API 文档: http://localhost:8000/docs

## 🔧 服务模块

### TTS 服务
```python
from services import TTSService

tts = TTSService()
result = await tts.generate("你好，欢迎观看直播")
print(result.audio_path)
```

### 新闻服务
```python
from services import NewsService

news = NewsService()
items = await news.fetch_all()
for item in items:
    print(f"{item.title} - {item.source}")
```

### 音乐服务
```python
from services import MusicService

music = MusicService()

# 获取随机音乐
track = music.get_random_track()

# 下载新音乐
await music.download("Blinding Lights The Weeknd")
```

### 视频服务
```python
from services import VideoService

video = VideoService()
result = video.create_from_audio(
    audio_path="speech.wav",
    text="新闻标题"
)
```

## 🐳 Docker 部署

```bash
# 构建镜像
docker-compose build

# 运行
docker-compose up -d
```

## 📝 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `DEBUG` | 调试模式 | `false` |
| `YOUTUBE_STREAM_KEY` | YouTube 推流密钥 | - |
| `BILIBILI_STREAM_KEY` | B站推流密钥 | - |
| `VIDEO_WIDTH` | 视频宽度 | `1280` |
| `VIDEO_HEIGHT` | 视频高度 | `720` |
| `VIDEO_FPS` | 帧率 | `30` |
| `VIDEO_BITRATE` | 视频码率 | `2500k` |
| `TTS_VOICE` | TTS 语音 | `zh-CN-XiaoxiaoNeural` |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
