# 视频生成与音乐下载文档

## 目录
- [音乐下载模块](#音乐下载模块)
- [视频合成模块](#视频合成模块)
- [使用示例](#使用示例)

---

## 音乐下载模块

### 文件位置
`music_downloader.py`

### 功能说明
从 SoundCloud 自动下载热门全球歌曲作为直播背景音乐。

### 依赖要求
```bash
# 安装 yt-dlp (必需)
pip install yt-dlp

# 或使用 Homebrew (macOS)
brew install yt-dlp
```

### 预设歌曲列表
内置 20 首热门全球歌曲：
| 序号 | 歌曲名 | 艺术家 |
|------|--------|--------|
| 1 | Blinding Lights | The Weeknd |
| 2 | Shape of You | Ed Sheeran |
| 3 | Dance Monkey | Tones and I |
| 4 | Uptown Funk | Bruno Mars |
| 5 | Someone You Loved | Lewis Capaldi |
| 6 | Bad Guy | Billie Eilish |
| 7 | Sunflower | Post Malone |
| 8 | Señorita | Shawn Mendes, Camila Cabello |
| 9 | Perfect | Ed Sheeran |
| 10 | Havana | Camila Cabello |
| 11 | Rockabye | Clean Bandit |
| 12 | Closer | Chainsmokers |
| 13 | Love Me Like You Do | Ellie Goulding |
| 14 | See You Again | Wiz Khalifa |
| 15 | Sorry | Justin Bieber |
| 16 | Faded | Alan Walker |
| 17 | Despacito | Luis Fonsi |
| 18 | Old Town Road | Lil Nas X |
| 19 | Levitating | Dua Lipa |
| 20 | Watermelon Sugar | Harry Styles |

### 使用方法

#### 1. 下载所有预设歌曲
```bash
python music_downloader.py
```

**输出：**
```
============================================================
Music Downloader - Downloading 20 Popular Global Songs
Source: SoundCloud
============================================================
Output directory: /path/to/music

[1/20] Downloading: Blinding Lights The Weeknd
  ✓ Downloaded successfully
[2/20] Downloading: Shape of You Ed Sheeran
  ✓ Downloaded successfully
...
============================================================
Download complete: 20/20 songs downloaded
Music files saved to: /path/to/music
============================================================
```

#### 2. 下载单个歌曲
```python
from music_downloader import download_song, MUSIC_DIR

# 下载单首歌曲
download_song("Blinding Lights The Weeknd", MUSIC_DIR, 1)
```

#### 3. 获取已下载音乐列表
```python
from music_downloader import get_music_playlist

playlist = get_music_playlist()
print(f"共有 {len(playlist)} 首音乐")
for song in playlist:
    print(song)
```

#### 4. 添加自定义歌曲
修改 `POPULAR_SONGS` 列表：
```python
POPULAR_SONGS = [
    "Blinding Lights The Weeknd",
    # 添加你的歌曲
    "你的歌曲名 艺术家名",
    # ...
]
```

### 配置参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--audio-quality` | 0 | 音频质量 (0=最佳) |
| `--max-filesize` | 30M | 单文件最大大小 |
| 输出格式 | mp3 | 输出音频格式 |
| 输出目录 | `music/` | 音乐保存目录 |

### 文件命名规则
```
song_{序号:02d}_{标题}.mp3
```
示例：`song_01_Blinding_Lights.mp3`

---

## 视频合成模块

### 文件位置
`video_composer.py`

### 功能说明
合成数字人视频和音频，生成适合直播推流的视频文件。

### 依赖要求
```bash
# Python 依赖
pip install opencv-python numpy pillow pydub loguru

# 系统依赖
# FFmpeg (必需)
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS

# 音频处理
sudo apt install ffmpeg  # pydub 需要 ffmpeg
```

### 核心类：VideoComposer

#### 初始化
```python
from video_composer import VideoComposer

composer = VideoComposer()
```

初始化时会自动检查：
- 视频模板文件 (`assets/video/template.mp4`)
- 数字人静态图片 (`assets/video/digital_human.png`)
- 背景音乐目录 (`assets/audio/music/`)

### 主要方法

#### 1. 创建静态视频帧
```python
frame = composer.create_static_video_frame(
    text="今日新闻：人工智能技术取得重大突破",
    output_path="frame.png"  # 可选，保存为图片
)
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `text` | str | 显示的文字内容 |
| `output_path` | str | 可选，保存帧为图片 |

**返回：** OpenCV 图像数组 (numpy.ndarray)

#### 2. 从静态图片创建视频
```python
video_path = composer.create_video_from_image(
    audio_path="news.wav",
    output_path="output.mp4",
    text="新闻标题"
)
```

**功能：** 使用静态图片 + 音频生成视频

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `audio_path` | str | 音频文件路径 (WAV格式) |
| `output_path` | str | 输出视频路径 |
| `text` | str | 显示的文字 |

**返回：** 成功返回输出路径，失败返回 None

#### 3. 使用视频模板创建视频
```python
video_path = composer.create_video_from_template(
    audio_path="news.wav",
    output_path="output.mp4",
    text="新闻标题"
)
```

**功能：** 使用视频模板循环匹配音频长度

**说明：** 如果没有视频模板，会自动回退到静态图片模式

#### 4. 创建新闻播报视频
```python
news_items = [
    {
        'news': {'title': '新闻标题1'},
        'audio_path': 'news1.wav',
        'duration': 30
    },
    {
        'news': {'title': '新闻标题2'},
        'audio_path': 'news2.wav',
        'duration': 25
    }
]

video_path = composer.create_news_video(
    news_audio_items=news_items,
    output_path="news_broadcast.mp4"
)
```

**功能：** 创建完整的新闻播报视频，包含：
- 多个新闻片段
- 新闻间自动插入背景音乐间隔
- 自动合并所有片段

#### 5. 创建音乐间隔片段
```python
music_segment = composer.create_music_segment(duration=30)
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `duration` | float | 时长（秒） |

**返回：** 视频片段路径

#### 6. 合并视频和音频
```python
result = composer.merge_video_audio(
    video_path="video.mp4",
    audio_path="audio.wav",
    output_path="output.mp4"
)
```

#### 7. 获取随机背景音乐
```python
bg_music = composer.get_random_bg_music()
print(f"背景音乐: {bg_music}")
```

### 配置参数 (config.py)
```python
# 视频配置
VIDEO_WIDTH = 1280       # 视频宽度
VIDEO_HEIGHT = 720       # 视频高度
VIDEO_FPS = 30           # 帧率
VIDEO_BITRATE = "2500k"  # 码率

# 资源路径
VIDEO_TEMPLATE_PATH = "assets/video/template.mp4"
DIGITAL_HUMAN_IMAGE = "assets/video/digital_human.png"
BG_MUSIC_DIR = "assets/audio/music/"

# 其他配置
MUSIC_INTERVAL_SECONDS = 30  # 音乐间隔时长
MAX_NEWS_DURATION = 300      # 单条新闻最大时长
```

### 视频模板要求
- 格式：MP4
- 编码：H.264
- 分辨率：建议 1280x720 或 1920x1080
- 内容：数字人说话动作（会循环播放）

---

## 使用示例

### 示例 1：下载音乐并创建新闻视频
```python
#!/usr/bin/env python3
"""完整示例：下载音乐 -> 生成TTS -> 创建视频"""

# 1. 下载背景音乐
from music_downloader import download_all_songs, get_music_playlist

print("下载背景音乐...")
download_all_songs()

# 2. 生成新闻语音
from tts_generator import TTSGenerator

tts = TTSGenerator()
news_items = [
    "人工智能技术取得重大突破",
    "全球科技股普遍上涨",
    "国际会议顺利召开"
]

audio_files = []
for i, news in enumerate(news_items):
    audio_path = tts.generate_speech(news, f"news_{i}.wav")
    audio_files.append({
        'news': {'title': news},
        'audio_path': audio_path
    })

# 3. 创建视频
from video_composer import VideoComposer

composer = VideoComposer()
video_path = composer.create_news_video(
    news_audio_items=audio_files,
    output_path="news_broadcast.mp4"
)

print(f"视频已生成: {video_path}")
```

### 示例 2：只创建单个视频片段
```python
from video_composer import VideoComposer
from tts_generator import TTSGenerator

# 生成语音
tts = TTSGenerator()
audio_path = tts.generate_speech("测试新闻内容", "test.wav")

# 创建视频
composer = VideoComposer()
video_path = composer.create_video_from_image(
    audio_path=audio_path,
    output_path="test.mp4",
    text="测试新闻"
)

print(f"视频路径: {video_path}")
```

### 示例 3：批量下载自定义歌曲
```python
from music_downloader import download_song, MUSIC_DIR
from pathlib import Path

# 自定义歌曲列表
custom_songs = [
    "夜曲 周杰伦",
    "晴天 周杰伦",
    "稻香 周杰伦",
]

for i, song in enumerate(custom_songs, 1):
    download_song(song, MUSIC_DIR, i)
```

---

## 故障排除

### 音乐下载失败
1. **检查 yt-dlp 安装**
   ```bash
   yt-dlp --version
   ```

2. **网络问题** - 使用代理
   ```bash
   export https_proxy=http://127.0.0.1:7890
   python music_downloader.py
   ```

3. **歌曲找不到** - 修改搜索关键词
   ```python
   # 尝试不同的关键词格式
   "歌曲名 艺术家"  # 推荐
   "艺术家 - 歌曲名"  # 备选
   ```

### 视频生成失败
1. **FFmpeg 未安装**
   ```bash
   ffmpeg -version
   ```

2. **音频格式错误** - 转换为 WAV
   ```python
   from pydub import AudioSegment
   audio = AudioSegment.from_mp3("input.mp3")
   audio.export("output.wav", format="wav")
   ```

3. **字体问题** - 安装中文字体
   ```bash
   # Ubuntu/Debian
   sudo apt install fonts-noto-cjk

   # macOS (通常自带)
   # Windows (通常自带微软雅黑)
   ```

4. **内存不足** - 降低分辨率
   ```python
   # config.py
   VIDEO_WIDTH = 854   # 480p
   VIDEO_HEIGHT = 480
   ```

---

## 文件结构
```
digital-human-livestream/
├── assets/
│   ├── video/
│   │   ├── template.mp4        # 视频模板（可选）
│   │   └── digital_human.png   # 数字人静态图
│   └── audio/
│       └── music/              # 背景音乐目录
├── output/
│   ├── news_broadcast.mp4      # 生成的视频
│   └── tts/                    # TTS 音频
├── music_downloader.py         # 音乐下载模块
├── video_composer.py           # 视频合成模块
├── tts_generator.py            # TTS 生成模块
└── config.py                   # 配置文件
```
