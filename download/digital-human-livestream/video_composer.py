#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Composer Module - 视频合成模块
合成数字人视频和音频，准备推流
"""

import os
import subprocess
import random
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment
from loguru import logger

from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    VIDEO_TEMPLATE_PATH, DIGITAL_HUMAN_IMAGE,
    BG_MUSIC_DIR, MUSIC_INTERVAL_SECONDS,
    OUTPUT_DIR, MAX_NEWS_DURATION
)


class VideoComposer:
    """视频合成器"""
    
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查视频模板
        self.has_video_template = VIDEO_TEMPLATE_PATH.exists()
        self.has_static_image = DIGITAL_HUMAN_IMAGE.exists()
        
        # 背景音乐列表
        self.bg_music_files = list(BG_MUSIC_DIR.glob("*.mp3")) + list(BG_MUSIC_DIR.glob("*.wav"))
        
        logger.info(f"视频合成器初始化: 模板={self.has_video_template}, 静态图={self.has_static_image}")
        logger.info(f"背景音乐: {len(self.bg_music_files)} 首")
    
    def create_static_video_frame(self, text: str = "", output_path: Optional[str] = None) -> np.ndarray:
        """
        创建静态视频帧（数字人背景+文字）
        
        Args:
            text: 要显示的文字（如新闻标题）
            output_path: 可选，保存帧为图片
        
        Returns:
            OpenCV图像数组
        """
        # 创建基础背景
        if self.has_static_image:
            # 加载数字人图片
            bg = Image.open(DIGITAL_HUMAN_IMAGE).convert('RGB')
            bg = bg.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.LANCZOS)
        else:
            # 创建渐变背景
            bg = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), (20, 30, 50))
            draw = ImageDraw.Draw(bg)
            
            # 添加渐变效果
            for y in range(VIDEO_HEIGHT):
                ratio = y / VIDEO_HEIGHT
                r = int(20 + 30 * ratio)
                g = int(30 + 40 * ratio)
                b = int(50 + 60 * ratio)
                draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b))
        
        # 添加文字
        if text:
            draw = ImageDraw.Draw(bg)
            
            # 尝试加载中文字体
            try:
                # macOS/Linux字体路径
                font_paths = [
                    "/System/Library/Fonts/PingFang.ttc",
                    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                    "C:\\Windows\\Fonts\\msyh.ttc",  # Windows
                ]
                
                font = None
                for font_path in font_paths:
                    if Path(font_path).exists():
                        font = ImageFont.truetype(font_path, 32)
                        break
                
                if font is None:
                    font = ImageFont.load_default()
                
            except Exception:
                font = ImageFont.load_default()
            
            # 文字换行处理
            max_chars_per_line = 40
            lines = []
            current_line = ""
            for char in text:
                current_line += char
                if len(current_line) >= max_chars_per_line:
                    lines.append(current_line)
                    current_line = ""
            if current_line:
                lines.append(current_line)
            
            # 绘制文字（带阴影效果）
            y_offset = VIDEO_HEIGHT - 150 - len(lines) * 40
            for line in lines:
                # 阴影
                draw.text((22, y_offset + 2), line, font=font, fill=(0, 0, 0))
                # 文字
                draw.text((20, y_offset), line, font=font, fill=(255, 255, 255))
                y_offset += 40
        
        # 添加时间戳
        draw = ImageDraw.Draw(bg)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 20), f"Live: {timestamp}", fill=(200, 200, 200))
        
        # 转换为OpenCV格式
        frame = cv2.cvtColor(np.array(bg), cv2.COLOR_RGB2BGR)
        
        if output_path:
            cv2.imwrite(output_path, frame)
        
        return frame
    
    def create_video_from_image(self, audio_path: str, output_path: str, 
                                text: str = "") -> Optional[str]:
        """
        从静态图片创建视频（带音频）
        
        Args:
            audio_path: 音频文件路径
            output_path: 输出视频路径
            text: 显示的文字
        
        Returns:
            输出视频路径
        """
        try:
            # 获取音频时长
            audio = AudioSegment.from_wav(audio_path)
            duration = len(audio) / 1000.0  # 转换为秒
            
            # 限制最大时长
            if duration > MAX_NEWS_DURATION:
                duration = MAX_NEWS_DURATION
            
            # 创建临时图片
            temp_frame_path = str(self.output_dir / "temp_frame.png")
            self.create_static_video_frame(text, temp_frame_path)
            
            # 使用FFmpeg创建视频
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', temp_frame_path,
                '-i', audio_path,
                '-c:v', 'libx264',
                '-tune', 'stillimage',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                '-shortest',
                '-r', str(VIDEO_FPS),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_path).exists():
                logger.info(f"视频创建成功: {output_path}, 时长: {duration:.1f}秒")
                
                # 清理临时文件
                if Path(temp_frame_path).exists():
                    Path(temp_frame_path).unlink()
                
                return output_path
            else:
                logger.error(f"FFmpeg视频创建失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"创建视频失败: {e}")
            return None
    
    def merge_video_audio(self, video_path: str, audio_path: str, 
                          output_path: str) -> Optional[str]:
        """
        合并视频和音频
        
        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            output_path: 输出文件路径
        
        Returns:
            输出文件路径
        """
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_path).exists():
                logger.info(f"音视频合并成功: {output_path}")
                return output_path
            else:
                logger.error(f"音视频合并失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"合并音视频失败: {e}")
            return None
    
    def get_random_bg_music(self) -> Optional[str]:
        """获取随机背景音乐"""
        if self.bg_music_files:
            return str(random.choice(self.bg_music_files))
        return None
    
    def create_news_video(self, news_audio_items: List[dict], 
                          output_path: str) -> Optional[str]:
        """
        创建新闻播报视频（多个新闻片段+音乐间隔）
        
        Args:
            news_audio_items: 新闻音频列表，每个包含 news, audio_path, duration
            output_path: 输出视频路径
        
        Returns:
            输出视频路径
        """
        if not news_audio_items:
            logger.warning("没有新闻音频，无法创建视频")
            return None
        
        try:
            # 创建视频片段列表
            video_segments = []
            temp_dir = self.output_dir / "temp_segments"
            temp_dir.mkdir(exist_ok=True)
            
            for i, item in enumerate(news_audio_items):
                news_title = item['news']['title']
                audio_path = item['audio_path']
                
                # 为每条新闻创建视频片段
                segment_path = str(temp_dir / f"segment_{i}.mp4")
                
                if self.has_video_template:
                    # 使用视频模板
                    segment_path = self.create_video_from_template(
                        audio_path, segment_path, news_title
                    )
                else:
                    # 使用静态图片
                    segment_path = self.create_video_from_image(
                        audio_path, segment_path, news_title
                    )
                
                if segment_path:
                    video_segments.append(segment_path)
                    
                    # 添加音乐间隔
                    if i < len(news_audio_items) - 1:
                        music_segment = self.create_music_segment(MUSIC_INTERVAL_SECONDS)
                        if music_segment:
                            video_segments.append(music_segment)
            
            if not video_segments:
                logger.error("没有成功创建视频片段")
                return None
            
            # 合并所有片段
            concat_list = temp_dir / "concat_list.txt"
            with open(concat_list, 'w') as f:
                for seg in video_segments:
                    f.write(f"file '{seg}'\n")
            
            # 使用FFmpeg合并
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_list),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-c:a', 'aac',
                '-b:a', '192k',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_path).exists():
                logger.info(f"新闻视频创建成功: {output_path}")
                
                # 清理临时文件
                for seg in video_segments:
                    if Path(seg).exists():
                        Path(seg).unlink()
                concat_list.unlink()
                
                return output_path
            else:
                logger.error(f"视频合并失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"创建新闻视频失败: {e}")
            return None
    
    def create_video_from_template(self, audio_path: str, output_path: str,
                                   text: str = "") -> Optional[str]:
        """使用视频模板创建视频"""
        if not self.has_video_template:
            return self.create_video_from_image(audio_path, output_path, text)
        
        try:
            # 获取音频时长
            audio = AudioSegment.from_wav(audio_path)
            duration = len(audio) / 1000.0
            
            # 循环视频模板以匹配音频时长
            cmd = [
                'ffmpeg', '-y',
                '-stream_loop', '-1',  # 无限循环视频
                '-i', str(VIDEO_TEMPLATE_PATH),
                '-i', audio_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-t', str(duration),
                '-shortest',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_path).exists():
                logger.info(f"模板视频创建成功: {output_path}")
                return output_path
            else:
                logger.warning(f"模板视频创建失败，使用静态图片: {result.stderr}")
                return self.create_video_from_image(audio_path, output_path, text)
                
        except Exception as e:
            logger.error(f"模板视频创建失败: {e}")
            return self.create_video_from_image(audio_path, output_path, text)
    
    def create_music_segment(self, duration: float) -> Optional[str]:
        """
        创建音乐间隔片段
        
        Args:
            duration: 时长（秒）
        
        Returns:
            视频片段路径
        """
        bg_music = self.get_random_bg_music()
        if not bg_music:
            logger.warning("没有背景音乐，跳过音乐间隔")
            return None
        
        try:
            temp_dir = self.output_dir / "temp_segments"
            temp_dir.mkdir(exist_ok=True)
            
            output_path = str(temp_dir / f"music_{datetime.now().strftime('%H%M%S')}.mp4")
            
            # 创建静态帧
            frame_path = str(temp_dir / "music_frame.png")
            self.create_static_video_frame("🎵 休息一下...", frame_path)
            
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', frame_path,
                '-i', bg_music,
                '-c:v', 'libx264',
                '-tune', 'stillimage',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-t', str(duration),
                '-shortest',
                '-r', str(VIDEO_FPS),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_path).exists():
                logger.info(f"音乐片段创建成功: {output_path}")
                Path(frame_path).unlink()
                return output_path
            else:
                logger.error(f"音乐片段创建失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"创建音乐片段失败: {e}")
            return None


if __name__ == "__main__":
    # 测试视频合成器
    composer = VideoComposer()
    
    # 创建测试帧
    frame = composer.create_static_video_frame("测试新闻标题：人工智能技术取得重大突破")
    print(f"测试帧创建成功，尺寸: {frame.shape}")
