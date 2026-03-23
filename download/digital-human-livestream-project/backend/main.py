#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Digital Human YouTube Livestream - Main Program
数字人YouTube无人值守直播主程序

功能：
1. 定时抓取热点新闻
2. 生成TTS语音
3. 合成数字人视频
4. 推流到YouTube
5. 循环播放新闻，中间插入音乐
"""

import os
import sys
import time
import signal
import argparse
import schedule
from pathlib import Path
from datetime import datetime
from typing import Optional

from loguru import logger

from config import (
    NEWS_UPDATE_INTERVAL, NEWS_LOOP_COUNT,
    OUTPUT_DIR, LOGS_DIR, LOG_LEVEL, LOG_FORMAT,
    BG_MUSIC_DIR
)
from news_fetcher import NewsFetcher, NewsItem
from tts_generator import TTSGenerator
from video_composer import VideoComposer
from streamer import StreamManager


class DigitalHumanLivestream:
    """数字人直播主控制器"""
    
    def __init__(self):
        # 初始化日志
        self._setup_logging()
        
        # 初始化各模块
        self.news_fetcher = NewsFetcher()
        self.tts_generator = TTSGenerator()
        self.video_composer = VideoComposer()
        self.stream_manager = StreamManager()
        
        # 状态变量
        self.is_running = False
        self.current_news_items = []
        self.current_video_path: Optional[str] = None
        self.loop_count = 0
        
        logger.info("=" * 60)
        logger.info("数字人YouTube直播系统初始化完成")
        logger.info("=" * 60)
    
    def _setup_logging(self):
        """设置日志"""
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台输出
        logger.add(sys.stdout, level=LOG_LEVEL, format=LOG_FORMAT)
        
        # 添加文件输出
        log_file = LOGS_DIR / "livestream_{time:YYYY-MM-DD}.log"
        logger.add(log_file, level="DEBUG", format=LOG_FORMAT, rotation="00:00")
    
    def fetch_and_process_news(self) -> bool:
        """
        抓取并处理新闻
        
        Returns:
            是否成功
        """
        logger.info("开始抓取新闻...")
        
        try:
            # 抓取新闻
            news_items = self.news_fetcher.fetch_all_sources()
            
            if not news_items:
                logger.warning("未获取到新闻，使用缓存")
                news_items = self.news_fetcher.get_cached_news()
            
            if not news_items:
                logger.error("没有可用的新闻内容")
                return False
            
            logger.info(f"获取到 {len(news_items)} 条新闻")
            
            # 生成TTS语音
            logger.info("开始生成TTS语音...")
            news_audio_items = self.tts_generator.generate_for_news(news_items)
            
            if not news_audio_items:
                logger.error("没有成功生成任何语音")
                return False
            
            # 创建视频
            logger.info("开始合成视频...")
            output_video = str(OUTPUT_DIR / "news_broadcast.mp4")
            
            video_path = self.video_composer.create_news_video(
                news_audio_items, output_video
            )
            
            if not video_path:
                logger.error("视频合成失败")
                return False
            
            self.current_news_items = news_audio_items
            self.current_video_path = video_path
            
            logger.info(f"新闻处理完成，视频: {video_path}")
            return True
            
        except Exception as e:
            logger.error(f"新闻处理失败: {e}")
            return False
    
    def start_livestream(self, loop: bool = True) -> bool:
        """
        开始直播
        
        Args:
            loop: 是否循环播放
        
        Returns:
            是否成功
        """
        if not self.current_video_path:
            logger.error("没有可用的视频，请先处理新闻")
            return False
        
        logger.info("开始推流到YouTube...")
        
        success = self.stream_manager.start(self.current_video_path, loop)
        
        if success:
            self.is_running = True
            logger.info("直播已启动")
        
        return success
    
    def stop_livestream(self):
        """停止直播"""
        logger.info("正在停止直播...")
        
        self.stream_manager.stop()
        self.is_running = False
        
        logger.info("直播已停止")
    
    def run_full_cycle(self):
        """运行完整周期：抓取新闻 -> 生成视频 -> 推流"""
        logger.info("=" * 40)
        logger.info(f"开始新的直播周期 - {datetime.now()}")
        logger.info("=" * 40)
        
        # 停止当前推流
        if self.is_running:
            self.stop_livestream()
            time.sleep(2)
        
        # 处理新闻
        if not self.fetch_and_process_news():
            logger.error("新闻处理失败，使用上一次的视频")
            if not self.current_video_path:
                logger.error("没有可用的视频，等待下次尝试")
                return
        
        # 开始推流
        self.start_livestream(loop=True)
        
        self.loop_count += 1
        logger.info(f"已完成 {self.loop_count} 个直播周期")
    
    def run_daemon(self):
        """
        以守护进程模式运行
        定时更新新闻并切换视频
        """
        logger.info("启动守护进程模式")
        logger.info(f"新闻更新间隔: {NEWS_UPDATE_INTERVAL} 秒")
        
        # 首次运行
        self.run_full_cycle()
        
        # 设置定时任务
        schedule.every(NEWS_UPDATE_INTERVAL).seconds.do(self.run_full_cycle)
        
        # 主循环
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
                # 打印状态
                status = self.stream_manager.streamer.get_status()
                if status["is_streaming"]:
                    logger.debug(f"直播进行中... (周期: {self.loop_count})")
                    
            except KeyboardInterrupt:
                logger.info("收到中断信号")
                break
            except Exception as e:
                logger.error(f"运行错误: {e}")
                time.sleep(10)
        
        # 清理
        self.stop_livestream()
    
    def run_once(self):
        """单次运行模式"""
        logger.info("单次运行模式")
        
        # 处理新闻
        if not self.fetch_and_process_news():
            logger.error("处理失败，退出")
            return False
        
        # 开始推流
        if not self.start_livestream(loop=True):
            logger.error("推流失败，退出")
            return False
        
        logger.info("直播已启动，按 Ctrl+C 停止")
        
        try:
            while self.is_running:
                time.sleep(60)
                status = self.stream_manager.streamer.get_status()
                logger.info(f"直播状态: {'运行中' if status['is_streaming'] else '已停止'}")
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        
        self.stop_livestream()
        return True
    
    def run_with_custom_news(self, news_file: str):
        """
        使用自定义新闻文件运行
        
        Args:
            news_file: 新闻文本文件路径（每行一条新闻）
        """
        logger.info(f"使用自定义新闻文件: {news_file}")
        
        try:
            with open(news_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            news_items = []
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    item = NewsItem(
                        title=f"新闻 {i+1}",
                        content=line,
                        source="自定义",
                        url="",
                        pub_date=datetime.now().strftime("%Y-%m-%d")
                    )
                    news_items.append(item)
            
            if not news_items:
                logger.error("新闻文件为空")
                return False
            
            # 生成语音
            news_audio_items = self.tts_generator.generate_for_news(news_items)
            
            # 创建视频
            output_video = str(OUTPUT_DIR / "custom_news.mp4")
            video_path = self.video_composer.create_news_video(
                news_audio_items, output_video
            )
            
            if video_path:
                self.current_video_path = video_path
                return self.start_livestream(loop=True)
            
            return False
            
        except Exception as e:
            logger.error(f"读取新闻文件失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数字人YouTube无人值守直播系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                      # 守护进程模式（定时更新新闻）
  python main.py --once               # 单次运行模式
  python main.py --news custom.txt    # 使用自定义新闻文件
  python main.py --test               # 测试模式（不推流）

环境要求:
  1. 安装依赖: pip install -r requirements.txt
  2. 安装FFmpeg: 确保ffmpeg命令可用
  3. 可选: 添加背景音乐到 assets/audio/music/
  4. 可选: 添加数字人视频模板到 assets/video/template.mp4
        """
    )
    
    parser.add_argument(
        '--once', '-o',
        action='store_true',
        help='单次运行模式（不会自动更新新闻）'
    )
    
    parser.add_argument(
        '--news', '-n',
        type=str,
        help='使用自定义新闻文件（每行一条新闻）'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='测试模式（只生成视频，不推流）'
    )
    
    parser.add_argument(
        '--video', '-v',
        type=str,
        help='直接推流指定的视频文件'
    )
    
    args = parser.parse_args()
    
    # 创建应用实例
    app = DigitalHumanLivestream()
    
    try:
        if args.test:
            # 测试模式
            logger.info("测试模式：只生成视频，不推流")
            success = app.fetch_and_process_news()
            if success:
                logger.info(f"测试视频已生成: {app.current_video_path}")
            else:
                logger.error("测试失败")
            return 0 if success else 1
        
        elif args.video:
            # 直接推流指定视频
            logger.info(f"直接推流视频: {args.video}")
            if Path(args.video).exists():
                app.current_video_path = args.video
                app.start_livestream(loop=True)
                
                try:
                    while app.is_running:
                        time.sleep(60)
                except KeyboardInterrupt:
                    pass
                
                app.stop_livestream()
                return 0
            else:
                logger.error(f"视频文件不存在: {args.video}")
                return 1
        
        elif args.news:
            # 使用自定义新闻
            success = app.run_with_custom_news(args.news)
            return 0 if success else 1
        
        elif args.once:
            # 单次运行模式
            success = app.run_once()
            return 0 if success else 1
        
        else:
            # 守护进程模式
            app.run_daemon()
            return 0
            
    except KeyboardInterrupt:
        logger.info("程序被中断")
        app.stop_livestream()
        return 0
    except Exception as e:
        logger.error(f"程序异常: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
