#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stream Monitor - 推流监控守护进程
监控FFmpeg推流状态，自动重启失败的服务
"""

import subprocess
import time
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

# 配置
PROJECT_DIR = Path(__file__).parent
PLAYLIST_FILE = PROJECT_DIR / "output" / "stream_playlist.txt"
LOG_FILE = PROJECT_DIR / "logs" / "stream_monitor.log"
PID_FILE = PROJECT_DIR / "logs" / "stream_monitor.pid"

# RTMP配置
RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"
STREAM_KEY = "hdb0-bxcg-ua45-hg30-78r0"

# 监控配置
CHECK_INTERVAL = 30  # 检查间隔(秒)
MAX_RESTART_COUNT = 5  # 最大重启次数
RESTART_COOLDOWN = 300  # 重启冷却时间(秒)


class StreamMonitor:
    """推流监控器"""
    
    def __init__(self):
        self.running = True
        self.restart_count = 0
        self.last_restart_time = 0
        self.ffmpeg_process = None
        self.start_time = None
        
        # 创建日志目录
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # 注册信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.log(f"收到信号 {signum}，正在停止...")
        self.running = False
        self.stop_stream()
        sys.exit(0)
    
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except:
            pass
    
    def check_existing_stream(self) -> bool:
        """检查是否有正在运行的推流进程"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "ffmpeg.*concat.*rtmp"],
                capture_output=True, text=True
            )
            pids = result.stdout.strip().split('\n')
            valid_pids = [p for p in pids if p.isdigit()]
            
            if valid_pids:
                self.log(f"发现运行中的推流进程: PID {valid_pids[0]}")
                return True
            return False
        except Exception as e:
            self.log(f"检查进程失败: {e}")
            return False
    
    def check_network_connection(self) -> bool:
        """检查网络连接"""
        try:
            # 测试YouTube RTMP服务器连接
            result = subprocess.run(
                ["timeout", "5", "nc", "-zv", "a.rtmp.youtube.com", "1935"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def check_playlist_exists(self) -> bool:
        """检查播放列表文件是否存在"""
        if not PLAYLIST_FILE.exists():
            self.log(f"播放列表不存在: {PLAYLIST_FILE}")
            return False
        
        # 检查播放列表是否有内容
        with open(PLAYLIST_FILE, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        
        if len(lines) == 0:
            self.log("播放列表为空")
            return False
        
        # 检查文件是否存在
        for line in lines:
            if line.startswith("file '"):
                file_path = line[6:-1]
                if not Path(file_path).exists():
                    self.log(f"播放列表中的文件不存在: {file_path}")
                    return False
        
        self.log(f"播放列表有效，包含 {len(lines)} 个文件")
        return True
    
    def start_stream(self) -> bool:
        """启动推流"""
        if not self.check_playlist_exists():
            self.log("无法启动推流：播放列表无效")
            return False
        
        # 检查网络连接
        if not self.check_network_connection():
            self.log("警告：网络连接异常，但仍尝试推流")
        
        try:
            # 构建FFmpeg命令
            cmd = [
                "ffmpeg",
                "-re",  # 实时读取
                "-stream_loop", "-1",  # 无限循环
                "-f", "concat",
                "-safe", "0",
                "-i", str(PLAYLIST_FILE),
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
                f"{RTMP_URL}/{STREAM_KEY}"
            ]
            
            self.log("启动推流...")
            self.log(f"命令: {' '.join(cmd[:10])}...")
            
            # 启动FFmpeg进程
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            self.start_time = datetime.now()
            self.log(f"推流已启动，PID: {self.ffmpeg_process.pid}")
            
            # 等待几秒确认进程稳定
            time.sleep(5)
            
            if self.ffmpeg_process.poll() is None:
                self.log("推流进程运行正常")
                return True
            else:
                self.log(f"推流进程启动后立即退出，返回码: {self.ffmpeg_process.poll()}")
                return False
                
        except Exception as e:
            self.log(f"启动推流失败: {e}")
            return False
    
    def stop_stream(self):
        """停止推流"""
        if self.ffmpeg_process:
            try:
                self.log("停止推流进程...")
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            except:
                try:
                    self.ffmpeg_process.kill()
                except:
                    pass
            self.ffmpeg_process = None
        
        # 终止所有相关进程
        try:
            subprocess.run(["pkill", "-f", "ffmpeg.*concat.*rtmp"], 
                          capture_output=True, timeout=5)
        except:
            pass
    
    def restart_stream(self) -> bool:
        """重启推流"""
        current_time = time.time()
        
        # 检查重启冷却
        if current_time - self.last_restart_time < RESTART_COOLDOWN:
            wait_time = int(RESTART_COOLDOWN - (current_time - self.last_restart_time))
            self.log(f"重启冷却中，等待 {wait_time} 秒...")
            time.sleep(wait_time)
        
        # 检查重启次数
        if self.restart_count >= MAX_RESTART_COUNT:
            self.log("达到最大重启次数，停止监控")
            return False
        
        self.log(f"重启推流 (第 {self.restart_count + 1} 次)...")
        self.stop_stream()
        
        if self.start_stream():
            self.restart_count += 1
            self.last_restart_time = current_time
            return True
        
        return False
    
    def get_status(self) -> dict:
        """获取状态"""
        uptime = ""
        if self.start_time:
            delta = datetime.now() - self.start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        return {
            "is_streaming": self.ffmpeg_process is not None and self.ffmpeg_process.poll() is None,
            "pid": self.ffmpeg_process.pid if self.ffmpeg_process else None,
            "uptime": uptime,
            "restart_count": self.restart_count,
            "start_time": self.start_time.isoformat() if self.start_time else None
        }
    
    def run(self):
        """运行监控"""
        self.log("=" * 60)
        self.log("推流监控守护进程启动")
        self.log(f"检查间隔: {CHECK_INTERVAL}秒")
        self.log(f"最大重启次数: {MAX_RESTART_COUNT}")
        self.log("=" * 60)
        
        # 保存PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        # 检查是否已有推流进程
        if self.check_existing_stream():
            self.log("使用现有推流进程")
        else:
            # 启动推流
            if not self.start_stream():
                self.log("初始启动失败，退出")
                return
        
        # 监控循环
        while self.running:
            try:
                time.sleep(CHECK_INTERVAL)
                
                # 检查推流进程
                if self.ffmpeg_process:
                    ret = self.ffmpeg_process.poll()
                    if ret is not None:
                        self.log(f"推流进程已退出，返回码: {ret}")
                        if not self.restart_stream():
                            break
                else:
                    # 检查系统中是否有其他推流进程
                    if not self.check_existing_stream():
                        self.log("未发现推流进程，尝试启动...")
                        if not self.start_stream():
                            if not self.restart_stream():
                                break
                
                # 记录状态
                status = self.get_status()
                if status["is_streaming"]:
                    self.log(f"推流正常 - PID: {status['pid']}, 运行时间: {status['uptime']}")
                
            except Exception as e:
                self.log(f"监控异常: {e}")
                time.sleep(10)
        
        self.log("监控守护进程停止")
        if PID_FILE.exists():
            PID_FILE.unlink()


def main():
    """主函数"""
    monitor = StreamMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
