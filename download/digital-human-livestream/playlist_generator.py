#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playlist Generator - 播放列表生成器
生成包含新闻播报和音乐的播放列表
"""

import os
import subprocess
import random
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from loguru import logger


class PlaylistGenerator:
    """播放列表生成器 - 生成包含新闻和音乐的播放列表"""
    
    def __init__(self, output_dir: str = "output", music_dir: str = "music"):
        self.output_dir = Path(output_dir)
        self.music_dir = Path(music_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def get_music_files(self) -> List[Path]:
        """获取所有音乐文件"""
        music_files = list(self.music_dir.glob("*.mp3"))
        random.shuffle(music_files)  # 随机打乱顺序
        return music_files
    
    def create_playlist_file(self, news_video: str, music_files: List[Path], 
                             output_name: str = "livestream_playlist.txt") -> Path:
        """
        创建FFmpeg播放列表文件
        
        Args:
            news_video: 新闻视频路径
            music_files: 音乐文件列表
            output_name: 输出文件名
        
        Returns:
            播放列表文件路径
        """
        playlist_path = self.output_dir / output_name
        
        with open(playlist_path, 'w') as f:
            # 先写入新闻视频
            if Path(news_video).exists():
                f.write(f"file '{Path(news_video).absolute()}'\n")
            
            # 写入音乐文件
            for music in music_files:
                f.write(f"file '{music.absolute()}'\n")
        
        logger.info(f"创建播放列表: {playlist_path}")
        return playlist_path
    
    def create_combined_video(self, news_video: str, music_files: List[Path],
                              output_name: str = "combined_livestream.mp4",
                              news_repeat: int = 3,
                              music_per_news: int = 2) -> Optional[Path]:
        """
        创建组合视频（新闻+音乐交替）
        
        Args:
            news_video: 新闻视频路径
            music_files: 音乐文件列表
            output_name: 输出文件名
            news_repeat: 新闻视频重复次数
            music_per_news: 每次新闻后插入的音乐数量
        
        Returns:
            输出视频路径
        """
        output_path = self.output_dir / output_name
        concat_list_path = self.output_dir / "concat_list.txt"
        
        # 构建concat列表
        concat_entries = []
        
        music_index = 0
        for i in range(news_repeat):
            # 添加新闻视频
            concat_entries.append(f"file '{Path(news_video).absolute()}'")
            
            # 添加音乐
            for j in range(music_per_news):
                if music_index < len(music_files):
                    concat_entries.append(f"file '{music_files[music_index].absolute()}'")
                    music_index += 1
        
        # 写入concat文件
        with open(concat_list_path, 'w') as f:
            f.write('\n'.join(concat_entries))
        
        logger.info(f"创建concat列表: {concat_list_path}")
        logger.info(f"包含 {news_repeat} 次新闻, {music_index} 首音乐")
        
        # 使用FFmpeg合并
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_path),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-b:v", "2500k",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        
        try:
            logger.info("开始合并视频...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                logger.info(f"视频合并完成: {output_path}")
                
                # 获取视频时长
                duration = self._get_video_duration(output_path)
                logger.info(f"视频时长: {duration}")
                
                return output_path
            else:
                logger.error(f"合并失败: {result.stderr[:500]}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("合并超时")
            return None
        except Exception as e:
            logger.error(f"合并错误: {e}")
            return None
    
    def _get_video_duration(self, video_path: Path) -> str:
        """获取视频时长"""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "unknown"
    
    def create_music_video_playlist(self, output_name: str = "music_playlist.txt") -> Path:
        """
        创建纯音乐播放列表（用于新闻播报间隔）
        """
        music_files = self.get_music_files()
        playlist_path = self.output_dir / output_name
        
        with open(playlist_path, 'w') as f:
            for music in music_files:
                f.write(f"file '{music.absolute()}'\n")
        
        logger.info(f"创建音乐播放列表: {playlist_path} ({len(music_files)} 首)")
        return playlist_path


def create_livestream_playlist():
    """创建直播播放列表"""
    # 路径设置
    project_dir = Path(__file__).parent
    output_dir = project_dir / "output"
    music_dir = project_dir / "music"
    news_video = output_dir / "news_broadcast.mp4"
    
    generator = PlaylistGenerator(str(output_dir), str(music_dir))
    
    # 获取音乐文件
    music_files = generator.get_music_files()
    print(f"找到 {len(music_files)} 首音乐")
    
    if not news_video.exists():
        print(f"新闻视频不存在: {news_video}")
        return None
    
    # 创建组合视频
    combined = generator.create_combined_video(
        str(news_video),
        music_files,
        news_repeat=3,
        music_per_news=2
    )
    
    if combined:
        print(f"\n✅ 组合视频创建成功!")
        print(f"   文件: {combined}")
        print(f"   大小: {combined.stat().st_size / (1024*1024):.1f} MB")
        return combined
    else:
        print("❌ 组合视频创建失败")
        return None


if __name__ == "__main__":
    create_livestream_playlist()
