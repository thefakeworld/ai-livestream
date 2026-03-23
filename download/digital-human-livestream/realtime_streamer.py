#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realtime YouTube Livestream Streamer with Log Output
实时YouTube直播推流器 - 支持实时日志输出
"""

import subprocess
import threading
import time
import os
import sys
import signal
from pathlib import Path
from datetime import datetime
from loguru import logger

# 配置
BASE_DIR = Path(__file__).parent.absolute()
LOGS_DIR = BASE_DIR / "logs"
FFMPEG_LOG_FILE = LOGS_DIR / "ffmpeg_realtime.log"

# YouTube 配置
RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"
STREAM_KEY = "hdb0-bxcg-ua45-hg30-78r0"
RTMP_PUSH_URL = f"{RTMP_URL}/{STREAM_KEY}"

# 播放列表
PLAYLIST_FILE = BASE_DIR / "output" / "stream_playlist.txt"

# 推流进程
ffmpeg_process = None
is_streaming = False
log_callbacks = []

def setup_logging():
    """配置日志"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")
    logger.add(FFMPEG_LOG_FILE, level="DEBUG", rotation="10 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {message}")

def log_message(msg: str, level: str = "INFO"):
    """记录日志并通知回调"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    
    if level == "ERROR":
        logger.error(msg)
    elif level == "WARNING":
        logger.warning(msg)
    else:
        logger.info(msg)
    
    # 通知所有回调
    for callback in log_callbacks:
        try:
            callback(log_line)
        except:
            pass

def get_video_files():
    """获取视频文件列表（转换为支持音频的格式）"""
    video_files = []
    
    # 使用新闻广播视频作为基础
    news_video = BASE_DIR / "output" / "news_broadcast.mp4"
    if news_video.exists():
        video_files.append(str(news_video))
    
    # 获取音乐文件
    music_dir = BASE_DIR / "music"
    if music_dir.exists():
        for f in sorted(music_dir.glob("*.mp3")):
            video_files.append(str(f))
    
    return video_files

def create_filter_complex(has_video: bool, has_audio: bool):
    """创建 FFmpeg filter_complex"""
    filters = []
    
    if not has_video:
        # 为纯音频生成视频（显示波形或静态图像）
        filters.append("[0:a]showwaves=s=1280x720:mode=line:colors=0x00ffff:rate=30[v]")
    
    return ";".join(filters) if filters else None

def build_ffmpeg_command_with_audio():
    """构建支持混合音视频的 FFmpeg 命令"""
    
    # 创建临时播放列表（只包含有效的视频文件或为音频生成视频）
    playlist_content = []
    music_dir = BASE_DIR / "music"
    news_video = BASE_DIR / "output" / "news_broadcast.mp4"
    
    # 收集所有内容
    items = []
    
    # 添加新闻视频
    if news_video.exists():
        items.append(("video", str(news_video)))
    
    # 添加音乐文件
    if music_dir.exists():
        for f in sorted(music_dir.glob("*.mp3"))[:10]:  # 限制前10首
            items.append(("audio", str(f)))
    
    # 交替添加新闻和音乐
    final_items = []
    music_idx = 0
    for _ in range(5):  # 5轮
        if news_video.exists():
            final_items.append(("video", str(news_video)))
        if music_idx < len(items):
            final_items.append(items[music_idx])
            music_idx += 1
    
    log_message(f"播放列表包含 {len(final_items)} 个项目")
    
    # 创建 FFmpeg 输入
    # 方法：使用循环输入 + filter_complex 处理混合内容
    
    cmd = [
        "ffmpeg",
        "-y",
        # 第一个输入：视频文件循环
        "-stream_loop", "-1",
        "-i", str(news_video),
        # 第二个输入：音频文件
        "-stream_loop", "-1",
        "-f", "concat",
        "-safe", "0",
        "-i", str(PLAYLIST_FILE),
        # 音频映射
        "-map", "0:v",  # 视频来自第一个输入
        "-map", "1:a",  # 音频来自第二个输入
        # 视频编码
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2500k",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-pix_fmt", "yuv420p",
        "-g", "60",
        "-r", "30",
        # 音频编码
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        # 输出格式
        "-f", "flv",
        "-flvflags", "no_duration_filesize",
        # 实时推流
        "-re",
        RTMP_PUSH_URL
    ]
    
    return cmd

def build_simple_ffmpeg_command():
    """构建简单的 FFmpeg 命令 - 只使用视频文件的音频"""
    
    news_video = BASE_DIR / "output" / "news_broadcast.mp4"
    
    if not news_video.exists():
        log_message("新闻视频不存在!", "ERROR")
        return None
    
    # 创建音乐播放列表文件
    music_playlist = BASE_DIR / "output" / "music_audio.txt"
    music_dir = BASE_DIR / "music"
    
    with open(music_playlist, "w") as f:
        if music_dir.exists():
            for mp3 in sorted(music_dir.glob("*.mp3"))[:10]:
                f.write(f"file '{mp3}'\n")
    
    # 简化命令：视频循环 + 音频混合
    cmd = [
        "ffmpeg",
        "-y",
        # 视频输入（循环）
        "-stream_loop", "-1",
        "-i", str(news_video),
        # 音频输入（音乐播放列表循环）
        "-stream_loop", "-1",
        "-f", "concat",
        "-safe", "0",
        "-i", str(music_playlist),
        # 只取视频流的视频
        "-map", "0:v",
        # 只取第二个输入的音频
        "-map", "1:a",
        # 视频编码
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2500k",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-pix_fmt", "yuv420p",
        "-g", "60",
        "-r", "30",
        # 音频编码
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        # 实时输出
        "-re",
        "-f", "flv",
        "-flvflags", "no_duration_filesize",
        RTMP_PUSH_URL
    ]
    
    return cmd

def read_ffmpeg_output(pipe, log_file):
    """读取 FFmpeg 输出并写入日志"""
    try:
        for line in iter(pipe.readline, b''):
            if line:
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    # 解析 FFmpeg 进度信息
                    if "frame=" in decoded:
                        log_message(decoded, "INFO")
                    elif decoded:
                        log_file.write(f"[{timestamp}] {decoded}\n")
                        log_file.flush()
    except Exception as e:
        log_message(f"读取 FFmpeg 输出错误: {e}", "ERROR")

def start_streaming():
    """启动推流"""
    global ffmpeg_process, is_streaming
    
    if is_streaming:
        log_message("推流已在运行中")
        return
    
    log_message("正在启动推流...")
    log_message(f"RTMP URL: {RTMP_URL}")
    log_message(f"Stream Key: {STREAM_KEY[:8]}...")
    
    # 使用简单命令
    cmd = build_simple_ffmpeg_command()
    if not cmd:
        log_message("无法构建 FFmpeg 命令", "ERROR")
        return
    
    log_message(f"命令: {' '.join(cmd[:10])}...")
    
    try:
        # 打开日志文件
        log_file = open(FFMPEG_LOG_FILE, "a")
        
        # 启动 FFmpeg
        ffmpeg_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1
        )
        is_streaming = True
        
        log_message(f"FFmpeg 进程已启动 (PID: {ffmpeg_process.pid})")
        
        # 启动日志读取线程
        stdout_thread = threading.Thread(
            target=read_ffmpeg_output,
            args=(ffmpeg_process.stdout, log_file),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=read_ffmpeg_output,
            args=(ffmpeg_process.stderr, log_file),
            daemon=True
        )
        stdout_thread.start()
        stderr_thread.start()
        
        # 写入 PID 文件
        pid_file = BASE_DIR / "logs" / "stream.pid"
        with open(pid_file, "w") as f:
            f.write(str(ffmpeg_process.pid))
        
        log_message("推流已成功启动!")
        
    except Exception as e:
        log_message(f"启动推流失败: {e}", "ERROR")
        is_streaming = False

def stop_streaming():
    """停止推流"""
    global ffmpeg_process, is_streaming
    
    if not is_streaming or not ffmpeg_process:
        log_message("推流未在运行")
        return
    
    log_message("正在停止推流...")
    
    try:
        ffmpeg_process.terminate()
        ffmpeg_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        ffmpeg_process.kill()
    except Exception as e:
        log_message(f"停止推流时出错: {e}", "WARNING")
    
    ffmpeg_process = None
    is_streaming = False
    log_message("推流已停止")

def check_streaming_status():
    """检查推流状态"""
    global ffmpeg_process, is_streaming
    
    if ffmpeg_process is None:
        return False, "未启动"
    
    poll = ffmpeg_process.poll()
    if poll is None:
        return True, f"运行中 (PID: {ffmpeg_process.pid})"
    else:
        is_streaming = False
        return False, f"已退出 (代码: {poll})"

def signal_handler(signum, frame):
    """信号处理"""
    log_message(f"收到信号 {signum}，正在停止...")
    stop_streaming()
    sys.exit(0)

def main():
    """主函数"""
    setup_logging()
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    log_message("=" * 50)
    log_message("YouTube 直播推流服务启动")
    log_message("=" * 50)
    
    # 启动推流
    start_streaming()
    
    # 监控循环
    try:
        while True:
            running, status = check_streaming_status()
            if not running:
                log_message(f"推流已停止: {status}")
                log_message("尝试重新启动推流...")
                start_streaming()
            time.sleep(30)
    except KeyboardInterrupt:
        log_message("收到中断信号")
    finally:
        stop_streaming()
        log_message("服务已退出")

if __name__ == "__main__":
    main()
