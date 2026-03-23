# 数字人YouTube无人值守直播系统

一个完整的Python实现的数字人推流到YouTube的无人值守直播解决方案。

## 功能特性

- 📰 **自动新闻抓取**: 从多个新闻源自动抓取热点新闻
- 🎙️ **TTS语音生成**: 使用AI语音合成技术生成自然的新闻播报语音
- 🎬 **视频合成**: 自动合成数字人视频（支持视频模板或静态图片）
- 📺 **YouTube推流**: 通过RTMP协议推流到YouTube
- 🎵 **背景音乐**: 新闻间隔自动播放背景音乐
- 🔄 **循环播放**: 支持循环播放和定时更新
- ⏰ **无人值守**: 可长时间自动运行

## 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   新闻抓取模块   │ ──▶ │   TTS语音生成   │ ──▶ │   视频合成模块   │
│  (news_fetcher) │     │ (tts_generator) │     │(video_composer) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   主控制模块     │ ◀── │  FFmpeg推流模块  │
                        │    (main.py)    │     │   (streamer)    │
                        └─────────────────┘     └─────────────────┘
```

## 环境要求

### 必需
- Python 3.8+
- FFmpeg 4.0+

### 可选
- Node.js 16+ (用于z-ai-web-dev-sdk TTS)
- edge-tts (备选TTS引擎)

## 快速开始

### 1. 安装依赖

**Linux/macOS:**
```bash
# 安装FFmpeg
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖（可选，用于更好的TTS效果）
npm install z-ai-web-dev-sdk
```

**Windows:**
```cmd
# 安装FFmpeg: 下载并添加到PATH
# 或使用 chocolatey
choco install ffmpeg

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 配置推流密钥

编辑 `config.py` 文件，修改YouTube推流密钥：

```python
YOUTUBE_STREAM_KEY = "your-stream-key-here"
```

### 3. 添加资源（可选）

- **数字人视频模板**: 放置到 `assets/video/template.mp4`
- **数字人静态图片**: 放置到 `assets/video/digital_human.png`
- **背景音乐**: 放置到 `assets/audio/music/` 目录

### 4. 运行

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
start.bat
```

**命令行运行:**
```bash
# 守护进程模式（定时更新新闻）
python main.py

# 单次运行模式
python main.py --once

# 测试模式（只生成视频，不推流）
python main.py --test

# 使用自定义新闻文件
python main.py --news news.txt

# 直接推流已有视频
python main.py --video my_video.mp4
```

## 配置说明

### config.py 主要配置项

```python
# YouTube推流配置
YOUTUBE_RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"
YOUTUBE_STREAM_KEY = "your-stream-key"

# 视频配置
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 30
VIDEO_BITRATE = "2500k"

# 新闻更新间隔（秒）
NEWS_UPDATE_INTERVAL = 3600  # 1小时

# 音乐间隔时间（秒）
MUSIC_INTERVAL_SECONDS = 30
```

### 新闻源配置

可以添加自定义RSS源：

```python
NEWS_SOURCES = [
    "https://news.google.com/rss?hl=zh-CN",
    # 添加更多RSS源...
]
```

## 文件结构

```
digital-human-livestream/
├── assets/                 # 资源文件
│   ├── video/             # 视频模板
│   │   ├── template.mp4   # 数字人视频模板
│   │   └── digital_human.png  # 数字人静态图
│   ├── audio/             # 音频文件
│   │   └── music/         # 背景音乐
│   └── news/              # 新闻缓存
├── output/                # 输出文件
│   └── tts/              # TTS语音文件
├── logs/                  # 日志文件
├── config.py             # 配置文件
├── news_fetcher.py       # 新闻抓取模块
├── tts_generator.py      # TTS语音生成模块
├── tts_bridge.js         # Node.js TTS桥接
├── video_composer.py     # 视频合成模块
├── streamer.py           # 推流模块
├── main.py               # 主程序
├── start.sh              # Linux启动脚本
├── start.bat             # Windows启动脚本
├── requirements.txt      # Python依赖
└── README.md             # 说明文档
```

## YouTube直播设置

### 获取推流密钥

1. 登录YouTube Studio
2. 进入"创建" > "开始直播"
3. 复制"串流密钥"
4. 将密钥配置到 `config.py`

### 推荐直播设置

- 分辨率: 1280x720 (720p) 或 1920x1080 (1080p)
- 码率: 2500-6000 kbps
- 帧率: 30 fps
- 编码: H.264

## 高级用法

### 自定义新闻内容

创建一个文本文件，每行一条新闻：

```text
今天要关注的是人工智能领域的最新发展。
科技板块迎来重大利好，多家公司股价上涨。
国际形势方面，多国领导人举行重要会议。
```

运行：
```bash
python main.py --news custom_news.txt
```

### 使用自己的视频模板

1. 准备一个数字人视频（建议mp4格式）
2. 视频会自动循环以匹配音频长度
3. 放置到 `assets/video/template.mp4`

### 添加背景音乐

将音乐文件（mp3或wav格式）放入 `assets/audio/music/` 目录，系统会随机选择播放。

## 故障排除

### 推流失败

1. 检查网络连接
2. 确认推流密钥正确
3. 检查FFmpeg是否正确安装
4. 查看日志文件 `logs/livestream_*.log`

### TTS生成失败

1. 确认已安装Node.js和z-ai-web-dev-sdk
2. 或安装edge-tts作为备用: `pip install edge-tts`

### 视频生成失败

1. 确认FFmpeg已安装并在PATH中
2. 检查音频文件是否正确生成
3. 确认有足够的磁盘空间

## 注意事项

⚠️ **重要提示**

1. **直播内容合规**: 确保直播内容符合YouTube社区准则
2. **版权问题**: 使用的音乐和素材需确保有合法使用权
3. **API限制**: 部分新闻源可能有访问频率限制
4. **网络稳定**: 推流需要稳定的上传带宽

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
