#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intelligent Director System - 智能导播系统
支持动态切换播放内容、AI控制、实时状态显示
"""

import subprocess
import threading
import time
import os
import sys
import json
import signal
import random
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
import fcntl

from multi_platform_config import get_config, PlatformStatus

# 设置时区
os.environ['TZ'] = 'Asia/Shanghai'
time.tzset()

# ==================== 配置 ====================
BASE_DIR = Path(__file__).parent.absolute()
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# YouTube 配置
RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"
STREAM_KEY = "hdb0-bxcg-ua45-hg30-78r0"
RTMP_PUSH_URL = f"{RTMP_URL}/{STREAM_KEY}"

# 目录配置
VIDEO_DIR = BASE_DIR / "output"
MUSIC_DIR = BASE_DIR / "music"
NEWS_DIR = BASE_DIR / "assets" / "news"

# 状态文件
STATE_FILE = LOGS_DIR / "director_state.json"
LOG_FILE = LOGS_DIR / "director.log"
PID_FILE = LOGS_DIR / "director.pid"

# 视频配置
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_BITRATE = "2500k"
AUDIO_BITRATE = "128k"


class ContentType(Enum):
    NEWS = "news"
    MUSIC = "music"
    VIDEO = "video"
    IDLE = "idle"


@dataclass
class ContentItem:
    """播放内容项"""
    type: ContentType
    name: str
    path: str
    duration: float = 0.0
    artist: str = ""
    title: str = ""
    is_playing: bool = False
    started_at: Optional[str] = None
    position: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典，处理枚举类型"""
        data = asdict(self)
        data['type'] = self.type.value
        return data


@dataclass
class DirectorState:
    """导播状态"""
    is_streaming: bool = False
    current_content: Optional[ContentItem] = None
    playlist: List[Dict[str, Any]] = None
    ffmpeg_pid: Optional[int] = None
    uptime: int = 0
    mode: str = "auto"  # auto, manual, ai
    last_update: str = ""

    def __post_init__(self):
        if self.playlist is None:
            self.playlist = []

    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.current_content:
            data['current_content'] = self.current_content.to_dict()
        return data


class IntelligentDirector:
    """智能导播系统"""
    
    def __init__(self):
        self.state = DirectorState()
        self.ffmpeg_process = None
        self.content_list: List[ContentItem] = []
        self.running = False
        self.lock = threading.Lock()
        
        # 加载已有内容
        self._scan_content()
        
        # 恢复状态
        self._load_state()
        
    def log(self, msg: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {msg}"
        print(log_line)
        try:
            with open(LOG_FILE, "a") as f:
                f.write(log_line + "\n")
        except:
            pass
    
    def _scan_content(self):
        """扫描可用内容"""
        self.content_list = []
        
        # 扫描新闻视频
        news_video = VIDEO_DIR / "news_broadcast.mp4"
        if news_video.exists():
            duration = self._get_duration(news_video)
            self.content_list.append(ContentItem(
                type=ContentType.NEWS,
                name="新闻播报",
                path=str(news_video),
                duration=duration,
                title="AI新闻播报",
                artist="数字人主播"
            ))
        
        # 扫描音乐文件
        if MUSIC_DIR.exists():
            for mp3 in sorted(MUSIC_DIR.glob("*.mp3")):
                name = mp3.stem
                # 尝试解析歌名和艺术家
                artist, title = self._parse_music_name(name)
                duration = self._get_duration(mp3)
                self.content_list.append(ContentItem(
                    type=ContentType.MUSIC,
                    name=name[:50],
                    path=str(mp3),
                    duration=duration,
                    artist=artist,
                    title=title
                ))
        
        self.log(f"扫描完成: {len(self.content_list)} 个内容项")
    
    def _parse_music_name(self, name: str) -> tuple:
        """解析音乐名称"""
        # 尝试匹配 "Artist - Title" 格式
        if " - " in name:
            parts = name.split(" - ", 1)
            return parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""
        # 尝试匹配 song_XX_ 格式
        match = re.match(r'song_\d+_(.+)', name)
        if match:
            return "", match.group(1)
        return "", name
    
    def _get_duration(self, file_path: Path) -> float:
        """获取媒体文件时长"""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)],
                capture_output=True, text=True, timeout=10
            )
            return float(result.stdout.strip())
        except:
            return 0.0
    
    def _load_state(self):
        """加载状态"""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                    # Reconstruct current_content as ContentItem if present
                    if data.get("current_content"):
                        cc = data["current_content"]
                        data["current_content"] = ContentItem(
                            type=ContentType(cc.get("type", "idle")),
                            name=cc.get("name", ""),
                            path=cc.get("path", ""),
                            duration=cc.get("duration", 0),
                            artist=cc.get("artist", ""),
                            title=cc.get("title", ""),
                            is_playing=cc.get("is_playing", False),
                            started_at=cc.get("started_at"),
                            position=cc.get("position", 0)
                        )
                    self.state = DirectorState(**data)
        except Exception as e:
            self.log(f"加载状态失败: {e}")
    
    def _save_state(self):
        """保存状态"""
        try:
            self.state.last_update = datetime.now().isoformat()
            with open(STATE_FILE, "w") as f:
                json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存状态失败: {e}", "ERROR")
    
    def get_playlist(self, mode: str = "mixed") -> List[ContentItem]:
        """生成播放列表"""
        playlist = []
        
        news_items = [c for c in self.content_list if c.type == ContentType.NEWS]
        music_items = [c for c in self.content_list if c.type == ContentType.MUSIC]
        
        if mode == "news_only":
            playlist = news_items * 10  # 循环新闻
        elif mode == "music_only":
            playlist = music_items.copy()
            random.shuffle(playlist)
        else:  # mixed
            # 新闻和音乐交替
            for i in range(max(len(news_items), len(music_items))):
                if i < len(news_items):
                    playlist.append(news_items[i])
                if i < len(music_items):
                    playlist.append(music_items[i])
        
        return playlist
    
    def build_ffmpeg_command(self, content: ContentItem, platforms: List = None) -> List[str]:
        """构建 FFmpeg 命令 - 支持多平台推流"""
        
        # 获取启用的平台
        if platforms is None:
            config = get_config()
            platforms = config.get_enabled_platforms()
        
        # 如果没有配置多平台，使用默认 YouTube
        if not platforms:
            platforms = [type('obj', (object,), {'full_url': RTMP_PUSH_URL, 'name': 'YouTube'})()]
        
        # 构建 RTMP 输出列表
        rtmp_outputs = []
        platform_names = []
        for p in platforms:
            if hasattr(p, 'full_url') and p.full_url:
                # 使用 onfail=ignore 确保一个平台失败不影响其他
                rtmp_outputs.append(f"[f=flv:onfail=ignore]{p.full_url}")
                platform_names.append(p.name if hasattr(p, 'name') else 'Unknown')
        
        # 如果只有一个平台，使用简单输出
        if len(rtmp_outputs) == 1:
            output_args = ["-f", "flv", "-flvflags", "no_duration_filesize", rtmp_outputs[0].replace("[f=flv:onfail=ignore]", "")]
        else:
            # 多平台使用 tee muxer
            tee_output = "|".join(rtmp_outputs)
            output_args = ["-f", "tee", "-map", "0:v", "-map", "0:a", tee_output]
        
        self.log(f"推流目标: {', '.join(platform_names)}")
        
        cmd = [
            "ffmpeg",
            "-re",  # 实时模式
            "-i", content.path,
            # 视频编码
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-b:v", VIDEO_BITRATE,
            "-maxrate", VIDEO_BITRATE,
            "-bufsize", "5000k",
            "-pix_fmt", "yuv420p",
            "-g", "60",
            "-r", "30",
            # 音频编码
            "-c:a", "aac",
            "-b:a", AUDIO_BITRATE,
            "-ar", "44100",
        ]
        
        # 添加输出参数
        cmd.extend(output_args)
        
        # 如果是音频文件，添加静态视频
        if content.type == ContentType.MUSIC:
            news_video = VIDEO_DIR / "news_broadcast.mp4"
            if news_video.exists():
                if len(rtmp_outputs) == 1:
                    output_args = ["-f", "flv", "-flvflags", "no_duration_filesize", rtmp_outputs[0].replace("[f=flv:onfail=ignore]", "")]
                else:
                    output_args = ["-f", "tee", "-map", "0:v", "-map", "1:a", tee_output]
                
                cmd = [
                    "ffmpeg",
                    "-re",
                    "-stream_loop", "-1",  # 视频循环
                    "-i", str(news_video),
                    "-i", content.path,
                    "-map", "0:v",  # 视频来自新闻视频
                    "-map", "1:a",  # 音频来自音乐
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-b:v", VIDEO_BITRATE,
                    "-c:a", "aac",
                    "-b:a", AUDIO_BITRATE,
                    "-shortest",
                ]
                cmd.extend(output_args)
        
        return cmd
    
    def get_active_platforms(self) -> List[Dict]:
        """获取当前活跃的平台"""
        config = get_config()
        enabled = config.get_enabled_platforms()
        result = []
        
        for p in enabled:
            result.append({
                "name": p.name,
                "status": p.status.value,
                "enabled": p.enabled
            })
        
        # 如果没有配置多平台，返回默认 YouTube
        if not result:
            result.append({
                "name": "YouTube",
                "status": "active" if self.state.is_streaming else "inactive",
                "enabled": True
            })
        
        return result
    
    def start_stream(self, content: Optional[ContentItem] = None):
        """开始推流"""
        if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
            self.log("推流已在运行中")
            return False
        
        # 选择内容
        if content is None:
            playlist = self.get_playlist()
            if not playlist:
                self.log("没有可用内容!", "ERROR")
                return False
            content = playlist[0]
        
        self.log(f"开始推流: [{content.type.value}] {content.title or content.name}")
        
        cmd = self.build_ffmpeg_command(content)
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            content.is_playing = True
            content.started_at = datetime.now().isoformat()
            
            self.state.is_streaming = True
            self.state.current_content = content
            self.state.ffmpeg_pid = self.ffmpeg_process.pid
            
            with open(PID_FILE, "w") as f:
                f.write(str(self.ffmpeg_process.pid))
            
            self._save_state()
            self.log(f"推流已启动 (PID: {self.ffmpeg_process.pid})")
            return True
            
        except Exception as e:
            self.log(f"启动推流失败: {e}", "ERROR")
            return False
    
    def stop_stream(self):
        """停止推流"""
        if self.ffmpeg_process:
            self.log("正在停止推流...")
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
            
            self.ffmpeg_process = None
            self.state.is_streaming = False
            self.state.ffmpeg_pid = None
            
            if self.state.current_content:
                self.state.current_content.is_playing = False
            
            self._save_state()
            self.log("推流已停止")
    
    def switch_content(self, content: ContentItem):
        """切换播放内容"""
        self.log(f"切换内容: {content.title or content.name}")
        
        # 停止当前推流
        self.stop_stream()
        time.sleep(1)
        
        # 开始新推流
        return self.start_stream(content)
    
    def play_next(self):
        """播放下一个内容"""
        playlist = self.get_playlist()
        
        if not playlist:
            self.log("播放列表为空", "WARNING")
            return False
        
        # 找到当前内容的索引
        current_idx = 0
        if self.state.current_content:
            for i, item in enumerate(playlist):
                if item.path == self.state.current_content.path:
                    current_idx = i
                    break
        
        # 下一个
        next_idx = (current_idx + 1) % len(playlist)
        return self.switch_content(playlist[next_idx])
    
    def get_status(self) -> Dict:
        """获取状态"""
        uptime = 0
        if self.state.current_content and self.state.current_content.started_at:
            try:
                start = datetime.fromisoformat(self.state.current_content.started_at)
                uptime = int((datetime.now() - start).total_seconds())
            except:
                pass
        
        config = get_config()
        
        return {
            "is_streaming": self.state.is_streaming,
            "ffmpeg_pid": self.state.ffmpeg_pid,
            "uptime": uptime,
            "mode": self.state.mode,
            "current_content": self.state.current_content.to_dict() if self.state.current_content else None,
            "content_count": len(self.content_list),
            "news_count": len([c for c in self.content_list if c.type == ContentType.NEWS]),
            "music_count": len([c for c in self.content_list if c.type == ContentType.MUSIC]),
            "rtmp_url": RTMP_URL,
            "timestamp": datetime.now().isoformat(),
            "platforms": self.get_active_platforms(),
            "platform_config": config.to_dict()
        }
    
    def _monitor_thread(self):
        """监控线程"""
        while self.running:
            try:
                # 检查 FFmpeg 进程
                if self.ffmpeg_process:
                    poll = self.ffmpeg_process.poll()
                    if poll is not None:
                        self.log(f"FFmpeg 已退出 (代码: {poll})")
                        self.state.is_streaming = False
                        
                        # 自动模式下重新推流
                        if self.state.mode == "auto":
                            self.log("自动重连...")
                            time.sleep(2)
                            self.play_next()
                
                # 更新播放位置
                if self.state.current_content and self.state.current_content.started_at:
                    try:
                        start = datetime.fromisoformat(self.state.current_content.started_at)
                        self.state.current_content.position = (datetime.now() - start).total_seconds()
                    except:
                        pass
                
                self._save_state()
                
            except Exception as e:
                self.log(f"监控错误: {e}", "ERROR")
            
            time.sleep(5)
    
    def run(self):
        """运行导播系统"""
        self.running = True
        self.log("=" * 50)
        self.log("智能导播系统启动")
        self.log(f"可用内容: {len(self.content_list)} 项")
        self.log("=" * 50)
        
        # 启动监控线程
        monitor = threading.Thread(target=self._monitor_thread, daemon=True)
        monitor.start()
        
        # 开始推流
        self.start_stream()
        
        # 主循环
        try:
            while self.running:
                time.sleep(10)
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.stop_stream()
            self.log("导播系统已停止")


# API 接口
director = None

def get_director() -> IntelligentDirector:
    """获取导播实例"""
    global director
    if director is None:
        director = IntelligentDirector()
    return director


def handle_command(cmd: str, data: Dict = None) -> Dict:
    """处理命令"""
    d = get_director()
    config = get_config()
    
    if cmd == "status":
        return {"success": True, "data": d.get_status()}
    
    elif cmd == "start":
        content = None
        if data and "path" in data:
            for c in d.content_list:
                if c.path == data["path"]:
                    content = c
                    break
        return {"success": d.start_stream(content)}
    
    elif cmd == "stop":
        d.stop_stream()
        return {"success": True}
    
    elif cmd == "next":
        return {"success": d.play_next()}
    
    elif cmd == "switch":
        if not data or "index" not in data:
            return {"success": False, "error": "缺少 index 参数"}
        playlist = d.get_playlist()
        if 0 <= data["index"] < len(playlist):
            return {"success": d.switch_content(playlist[data["index"]])}
        return {"success": False, "error": "索引超出范围"}
    
    elif cmd == "list":
        return {
            "success": True,
            "data": [c.to_dict() for c in d.content_list]
        }
    
    elif cmd == "playlist":
        mode = data.get("mode", "mixed") if data else "mixed"
        return {
            "success": True,
            "data": [c.to_dict() for c in d.get_playlist(mode)]
        }
    
    # ========== 多平台管理命令 ==========
    
    elif cmd == "platforms":
        """获取所有平台列表"""
        return {
            "success": True,
            "data": config.list_platforms()
        }
    
    elif cmd == "enable_platform":
        """启用平台"""
        if not data or "platform" not in data:
            return {"success": False, "error": "缺少 platform 参数"}
        stream_key = data.get("stream_key", "")
        config.enable_platform(data["platform"], stream_key)
        return {"success": True, "message": f"平台 {data['platform']} 已启用"}
    
    elif cmd == "disable_platform":
        """禁用平台"""
        if not data or "platform" not in data:
            return {"success": False, "error": "缺少 platform 参数"}
        config.disable_platform(data["platform"])
        return {"success": True, "message": f"平台 {data['platform']} 已禁用"}
    
    elif cmd == "set_stream_key":
        """设置推流密钥"""
        if not data or "platform" not in data or "stream_key" not in data:
            return {"success": False, "error": "缺少参数"}
        config.set_stream_key(data["platform"], data["stream_key"])
        return {"success": True, "message": f"平台 {data['platform']} 密钥已更新"}
    
    else:
        return {"success": False, "error": f"未知命令: {cmd}"}


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 命令行模式
        cmd = sys.argv[1]
        data = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
        result = handle_command(cmd, data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 服务模式
        d = IntelligentDirector()
        d.run()
