#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速状态检查脚本
"""

import subprocess
import sys
from datetime import datetime

def run_cmd(cmd):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except:
        return ""

def check_status():
    """检查推流状态"""
    print("=" * 60)
    print("  YouTube 直播推流状态检查")
    print("=" * 60)
    print()
    
    # 检查FFmpeg进程
    print("📡 推流进程状态:")
    ffmpeg_pid = run_cmd("pgrep -f 'ffmpeg.*(concat|rtmp|youtube)'")
    
    if ffmpeg_pid:
        # 获取进程信息
        pid = ffmpeg_pid.split('\n')[0]
        uptime = run_cmd(f"ps -p {pid} -o etime= --no-headers")
        cpu_mem = run_cmd(f"ps -p {pid} -o %cpu,%mem --no-headers")
        
        print(f"  ✅ 推流运行中")
        print(f"  PID: {pid}")
        print(f"  运行时间: {uptime}")
        if cpu_mem:
            parts = cpu_mem.split()
            print(f"  CPU: {parts[0]}%  内存: {parts[1]}%")
    else:
        print("  ❌ 推流未运行")
    
    print()
    
    # 检查监控服务
    print("🤖 监控服务状态:")
    monitor_pid = run_cmd("pgrep -f 'stream_monitor.py'")
    
    if monitor_pid:
        print(f"  ✅ 监控服务运行中 (PID: {monitor_pid})")
    else:
        print("  ❌ 监控服务未运行")
    
    print()
    
    # 检查YouTube连接
    print("🌐 网络连接状态:")
    youtube_check = run_cmd("timeout 5 bash -c 'echo > /dev/tcp/a.rtmp.youtube.com/1935' 2>&1 && echo 'ok'")
    
    if youtube_check == "ok":
        print("  ✅ YouTube RTMP 服务器可达")
    else:
        print("  ❌ YouTube RTMP 服务器不可达")
    
    print()
    
    # 检查播放列表
    print("📋 播放列表信息:")
    playlist_file = "/home/z/my-project/download/digital-human-livestream/output/stream_playlist.txt"
    
    try:
        with open(playlist_file, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        
        news_count = sum(1 for l in lines if 'news_broadcast' in l)
        music_count = sum(1 for l in lines if '.mp3' in l)
        
        print(f"  总条目: {len(lines)}")
        print(f"  新闻播报: {news_count} 次")
        print(f"  音乐文件: {music_count} 首")
        print(f"  预计时长: ~{news_count * 6 + music_count * 4} 分钟")
    except:
        print("  ⚠️ 无法读取播放列表")
    
    print()
    
    # 显示最近日志
    print("📜 最近日志:")
    log_file = "/home/z/my-project/download/digital-human-livestream/logs/stream_monitor.log"
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()[-5:]
        
        for line in lines:
            print(f"  {line.strip()}")
    except:
        print("  暂无日志")
    
    print()
    print("=" * 60)
    print(f"  检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    check_status()
