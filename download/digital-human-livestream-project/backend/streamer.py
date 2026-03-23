#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamer Module - 推流模块
使用FFmpeg推流到YouTube
"""

import subprocess
import time
import signal
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from loguru import logger

from config import (
    RTMP_PUSH_URL,
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, VIDEO_BITRATE,
    AUDIO_BITRATE, AUDIO_SAMPLE_RATE,
    FFMPEG_PRESET, FFMPEG_THREADS
)


class YouTubeStreamer:
    """YouTube推流器"""
    
    def __init__(self):
        self.rtmp_url = RTMP_PUSH_URL
        self.process: Optional[subprocess.Popen] = None
        self.is_streaming = False
        
        logger.info(f"YouTube推流器初始化")
        logger.info(f"推流地址: {RTMP_PUSH_URL[:50]}...")  # 隐藏完整密钥
    
    def start_stream_from_file(self, video_path: str, loop: bool = True) -> bool:
        """
        从视频文件开始推流
        
        Args:
            video_path: 视频文件路径
            loop: 是否循环播放
        
        Returns:
            是否成功启动
        """
        if not Path(video_path).exists():
            logger.error(f"视频文件不存在: {video_path}")
            return False
        
        if self.is_streaming:
            logger.warning("已有推流正在进行，请先停止")
            return False
        
        try:
            # 构建FFmpeg命令
            if loop:
                # 循环推流
                cmd = self._build_loop_stream_cmd(video_path)
            else:
                # 单次推流
                cmd = self._build_single_stream_cmd(video_path)
            
            logger.info(f"启动推流: {video_path}")
            
            # 启动FFmpeg进程
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.is_streaming = True
            
            # 启动监控线程
            self._start_monitor()
            
            logger.info("推流已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动推流失败: {e}")
            return False
    
    def _build_single_stream_cmd(self, video_path: str) -> List[str]:
        """构建单次推流命令"""
        return [
            'ffmpeg',
            '-re',  # 以实际帧率读取
            '-i', video_path,
            '-c:v', 'libx264',
            '-preset', FFMPEG_PRESET,
            '-b:v', VIDEO_BITRATE,
            '-maxrate', VIDEO_BITRATE,
            '-bufsize', f"{int(VIDEO_BITRATE[:-1]) * 2}k",
            '-pix_fmt', 'yuv420p',
            '-g', str(VIDEO_FPS * 2),  # GOP大小
            '-c:a', 'aac',
            '-b:a', AUDIO_BITRATE,
            '-ar', str(AUDIO_SAMPLE_RATE),
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            self.rtmp_url
        ]
    
    def _build_loop_stream_cmd(self, video_path: str) -> List[str]:
        """构建循环推流命令"""
        return [
            'ffmpeg',
            '-re',
            '-stream_loop', '-1',  # 无限循环
            '-i', video_path,
            '-c:v', 'libx264',
            '-preset', FFMPEG_PRESET,
            '-b:v', VIDEO_BITRATE,
            '-maxrate', VIDEO_BITRATE,
            '-bufsize', f"{int(VIDEO_BITRATE[:-1]) * 2}k",
            '-pix_fmt', 'yuv420p',
            '-g', str(VIDEO_FPS * 2),
            '-c:a', 'aac',
            '-b:a', AUDIO_BITRATE,
            '-ar', str(AUDIO_SAMPLE_RATE),
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            self.rtmp_url
        ]
    
    def _start_monitor(self):
        """启动进程监控"""
        import threading
        
        def monitor():
            while self.is_streaming and self.process:
                ret = self.process.poll()
                if ret is not None:
                    logger.warning(f"FFmpeg进程已退出，返回码: {ret}")
                    self.is_streaming = False
                    break
                time.sleep(5)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def stop_stream(self):
        """停止推流"""
        if not self.is_streaming or not self.process:
            return
        
        try:
            logger.info("正在停止推流...")
            
            # 发送 'q' 命令优雅退出
            try:
                self.process.stdin.write(b'q')
                self.process.stdin.flush()
            except:
                pass
            
            # 等待进程结束
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 强制终止
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            
            self.is_streaming = False
            self.process = None
            logger.info("推流已停止")
            
        except Exception as e:
            logger.error(f"停止推流失败: {e}")
            self.is_streaming = False
            self.process = None
    
    def stream_playlist(self, video_files: List[str], loop: bool = True) -> bool:
        """
        推流播放列表（多个视频顺序播放）
        
        Args:
            video_files: 视频文件列表
            loop: 是否循环播放整个列表
        
        Returns:
            是否成功启动
        """
        if not video_files:
            logger.error("视频列表为空")
            return False
        
        # 验证所有文件存在
        valid_files = [f for f in video_files if Path(f).exists()]
        if not valid_files:
            logger.error("没有有效的视频文件")
            return False
        
        try:
            # 创建临时播放列表文件
            playlist_path = Path("temp_playlist.txt")
            with open(playlist_path, 'w') as f:
                for video in valid_files:
                    f.write(f"file '{video}'\n")
            
            # 构建FFmpeg命令
            cmd = [
                'ffmpeg',
                '-re',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(playlist_path),
            ]
            
            if loop:
                cmd.extend(['-stream_loop', '-1'])
            
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', FFMPEG_PRESET,
                '-b:v', VIDEO_BITRATE,
                '-maxrate', VIDEO_BITRATE,
                '-bufsize', f"{int(VIDEO_BITRATE[:-1]) * 2}k",
                '-pix_fmt', 'yuv420p',
                '-g', str(VIDEO_FPS * 2),
                '-c:a', 'aac',
                '-b:a', AUDIO_BITRATE,
                '-ar', str(AUDIO_SAMPLE_RATE),
                '-f', 'flv',
                '-flvflags', 'no_duration_filesize',
                self.rtmp_url
            ])
            
            logger.info(f"启动播放列表推流，共 {len(valid_files)} 个视频")
            
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.is_streaming = True
            self._start_monitor()
            
            return True
            
        except Exception as e:
            logger.error(f"播放列表推流失败: {e}")
            return False
    
    def get_status(self) -> dict:
        """获取推流状态"""
        return {
            "is_streaming": self.is_streaming,
            "process_running": self.process is not None and self.process.poll() is None,
            "rtmp_url": RTMP_PUSH_URL[:30] + "...",
            "timestamp": datetime.now().isoformat()
        }


class StreamManager:
    """推流管理器 - 管理直播生命周期"""
    
    def __init__(self):
        self.streamer = YouTubeStreamer()
        self.current_video: Optional[str] = None
        self.stats = {
            "start_time": None,
            "videos_streamed": 0,
            "total_duration": 0
        }
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在退出...")
        self.stop()
        sys.exit(0)
    
    def start(self, video_path: str, loop: bool = True) -> bool:
        """开始直播"""
        self.stats["start_time"] = datetime.now()
        self.current_video = video_path
        
        success = self.streamer.start_stream_from_file(video_path, loop)
        
        if success:
            logger.info(f"直播已开始: {video_path}")
        
        return success
    
    def stop(self):
        """停止直播"""
        self.streamer.stop_stream()
        self.stats["videos_streamed"] += 1
        
        logger.info(f"直播已停止，运行时长: {self._get_uptime()}")
    
    def _get_uptime(self) -> str:
        """获取运行时长"""
        if self.stats["start_time"]:
            delta = datetime.now() - self.stats["start_time"]
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}h {minutes}m {seconds}s"
        return "0s"
    
    def switch_video(self, new_video_path: str) -> bool:
        """切换视频源"""
        logger.info(f"切换视频源: {new_video_path}")
        
        self.stop()
        time.sleep(2)  # 短暂等待
        
        return self.start(new_video_path)


if __name__ == "__main__":
    # 测试推流
    streamer = YouTubeStreamer()
    
    # 检查推流地址
    print(f"推流地址: {RTMP_PUSH_URL[:30]}...")
    
    # 如果有测试视频，可以测试推流
    test_video = "output/test_video.mp4"
    if Path(test_video).exists():
        print(f"找到测试视频: {test_video}")
        print("启动测试推流（5秒后自动停止）...")
        
        if streamer.start_stream_from_file(test_video):
            time.sleep(5)
            streamer.stop_stream()
            print("测试完成")
    else:
        print("未找到测试视频，跳过推流测试")
