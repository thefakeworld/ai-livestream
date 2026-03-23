#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playlist Streamer - 播放列表推流
将新闻视频和音乐整合推流到YouTube
"""

import subprocess
import os
from pathlib import Path
from typing import List, Optional
import random

from config import RTMP_PUSH_URL


class PlaylistStreamer:
    """播放列表推流器"""
    
    def __init__(self, project_dir: str = None):
        if project_dir is None:
            project_dir = Path(__file__).parent
        self.project_dir = Path(project_dir)
        self.output_dir = self.project_dir / "output"
        self.music_dir = self.project_dir / "music"
        self.process: Optional[subprocess.Popen] = None
        
    def get_music_files(self) -> List[Path]:
        """获取所有音乐文件"""
        files = list(self.music_dir.glob("*.mp3"))
        random.shuffle(files)
        return files
    
    def create_playlist(self, news_video: Path, music_files: List[Path],
                        repeat_count: int = 5) -> Path:
        """
        创建播放列表文件
        
        Args:
            news_video: 新闻视频路径
            music_files: 音乐文件列表
            repeat_count: 新闻重复次数
        
        Returns:
            播放列表文件路径
        """
        playlist_path = self.output_dir / "stream_playlist.txt"
        
        with open(playlist_path, 'w') as f:
            music_idx = 0
            for i in range(repeat_count):
                # 添加新闻视频
                if news_video.exists():
                    f.write(f"file '{news_video.absolute()}'\n")
                
                # 每次新闻后添加2首音乐
                for j in range(2):
                    if music_idx < len(music_files):
                        f.write(f"file '{music_files[music_idx].absolute()}'\n")
                        music_idx += 1
                    else:
                        # 循环音乐列表
                        music_idx = 0
                        f.write(f"file '{music_files[music_idx].absolute()}'\n")
                        music_idx += 1
        
        print(f"播放列表创建完成: {playlist_path}")
        print(f"  - 新闻重复: {repeat_count} 次")
        print(f"  - 音乐数量: {len(music_files)} 首")
        
        return playlist_path
    
    def start_stream(self, playlist_path: Path, loop: bool = True) -> bool:
        """
        开始推流
        
        Args:
            playlist_path: 播放列表文件路径
            loop: 是否循环播放
        """
        if not playlist_path.exists():
            print(f"播放列表不存在: {playlist_path}")
            return False
        
        # 构建FFmpeg命令
        cmd = [
            "ffmpeg",
            "-re",  # 实时读取
        ]
        
        if loop:
            cmd.extend(["-stream_loop", "-1"])  # 无限循环
        
        cmd.extend([
            "-f", "concat",
            "-safe", "0",
            "-i", str(playlist_path),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-b:v", "2500k",
            "-maxrate", "2500k",
            "-bufsize", "5000k",
            "-pix_fmt", "yuv420p",
            "-g", "60",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-f", "flv",
            "-flvflags", "no_duration_filesize",
            RTMP_PUSH_URL
        ])
        
        print("启动推流...")
        print(f"推流地址: {RTMP_PUSH_URL[:40]}...")
        
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return True
    
    def stop_stream(self):
        """停止推流"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("推流已停止")
    
    def get_pid(self) -> Optional[int]:
        """获取进程ID"""
        if self.process:
            return self.process.pid
        return None


def main():
    """主函数：创建播放列表并开始推流"""
    streamer = PlaylistStreamer()
    
    # 获取新闻视频
    news_video = streamer.output_dir / "news_broadcast.mp4"
    if not news_video.exists():
        print(f"新闻视频不存在: {news_video}")
        return
    
    # 获取音乐文件
    music_files = streamer.get_music_files()
    print(f"找到 {len(music_files)} 首音乐")
    
    if len(music_files) == 0:
        print("没有找到音乐文件")
        return
    
    # 创建播放列表
    playlist = streamer.create_playlist(news_video, music_files, repeat_count=5)
    
    # 停止现有推流
    streamer.stop_stream()
    
    # 开始推流
    if streamer.start_stream(playlist):
        print(f"推流已启动，PID: {streamer.get_pid()}")
        print("按 Ctrl+C 停止推流")
        
        try:
            # 保持运行
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            streamer.stop_stream()
    else:
        print("推流启动失败")


if __name__ == "__main__":
    main()
