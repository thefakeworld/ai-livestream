#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple YouTube Livestream Streamer with Real-time Logging
简单YouTube直播推流器 - 实时日志输出
"""

import subprocess
import time
import os
import sys
import signal
from pathlib import Path
from datetime import datetime

# 配置
BASE_DIR = Path(__file__).parent.absolute()
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# YouTube 配置
RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"
STREAM_KEY = "hdb0-bxcg-ua45-hg30-78r0"
RTMP_PUSH_URL = f"{RTMP_URL}/{STREAM_KEY}"

# 日志文件
LOG_FILE = LOGS_DIR / "ffmpeg_realtime.log"
PID_FILE = LOGS_DIR / "stream.pid"

# 全局变量
ffmpeg_process = None

def log(msg: str):
    """写入日志并打印"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")

def start_stream():
    """启动推流"""
    global ffmpeg_process
    
    video_file = BASE_DIR / "output" / "news_broadcast.mp4"
    if not video_file.exists():
        log("错误: 视频文件不存在!")
        return False
    
    log("=" * 50)
    log("启动 YouTube 直播推流")
    log(f"视频文件: {video_file}")
    log(f"RTMP URL: {RTMP_URL}")
    log("=" * 50)
    
    # FFmpeg 命令
    cmd = [
        "ffmpeg",
        "-re",
        "-stream_loop", "-1",
        "-i", str(video_file),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2500k",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-pix_fmt", "yuv420p",
        "-g", "60",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv",
        "-flvflags", "no_duration_filesize",
        RTMP_PUSH_URL
    ]
    
    log(f"命令: ffmpeg -re -stream_loop -1 -i {video_file.name} ...")
    
    try:
        # 打开日志文件用于写入
        log_handle = open(LOG_FILE, "a")
        
        # 启动 FFmpeg
        ffmpeg_process = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            bufsize=0  # 无缓冲
        )
        
        # 写入 PID 文件
        with open(PID_FILE, "w") as f:
            f.write(str(ffmpeg_process.pid))
        
        log(f"FFmpeg 已启动 (PID: {ffmpeg_process.pid})")
        log("推流已开始!")
        return True
        
    except Exception as e:
        log(f"启动失败: {e}")
        return False

def stop_stream():
    """停止推流"""
    global ffmpeg_process
    
    if ffmpeg_process:
        log("正在停止推流...")
        ffmpeg_process.terminate()
        try:
            ffmpeg_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ffmpeg_process.kill()
        ffmpeg_process = None
        log("推流已停止")
    
    # 清理 PID 文件
    if PID_FILE.exists():
        PID_FILE.unlink()

def signal_handler(signum, frame):
    """信号处理"""
    log(f"收到信号 {signum}")
    stop_stream()
    sys.exit(0)

def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 清理旧日志
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    
    # 启动推流
    if not start_stream():
        sys.exit(1)
    
    # 监控循环
    try:
        while True:
            if ffmpeg_process:
                poll = ffmpeg_process.poll()
                if poll is not None:
                    log(f"FFmpeg 已退出 (代码: {poll})")
                    log("正在重启推流...")
                    if not start_stream():
                        time.sleep(10)  # 等待后重试
            time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        stop_stream()

if __name__ == "__main__":
    main()
