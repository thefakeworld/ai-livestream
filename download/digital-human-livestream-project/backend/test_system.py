#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试脚本 - 验证各模块是否正常工作
"""

import sys
import subprocess
from pathlib import Path

def check_ffmpeg():
    """检查FFmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg 已安装")
            return True
    except FileNotFoundError:
        pass
    print("❌ FFmpeg 未安装")
    return False

def check_python_deps():
    """检查Python依赖"""
    required = ['requests', 'feedparser', 'bs4', 'pydub', 'PIL', 'cv2', 'loguru', 'numpy']
    missing = []
    
    for module in required:
        try:
            __import__(module)
            print(f"✅ {module} 已安装")
        except ImportError:
            print(f"❌ {module} 未安装")
            missing.append(module)
    
    return len(missing) == 0

def check_nodejs():
    """检查Node.js"""
    try:
        result = subprocess.run(['node', '-v'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js 已安装 ({result.stdout.strip()})")
            return True
    except FileNotFoundError:
        pass
    print("⚠️ Node.js 未安装（将使用edge-tts作为备用TTS引擎）")
    return False

def check_edge_tts():
    """检查edge-tts"""
    try:
        import edge_tts
        print("✅ edge-tts 已安装")
        return True
    except ImportError:
        print("⚠️ edge-tts 未安装")
        return False

def check_directories():
    """检查目录结构"""
    dirs = [
        'assets/video',
        'assets/audio/music',
        'assets/news',
        'output/tts',
        'logs'
    ]
    
    all_exist = True
    for d in dirs:
        if Path(d).exists():
            print(f"✅ 目录 {d} 存在")
        else:
            print(f"⚠️ 目录 {d} 不存在，将自动创建")
            Path(d).mkdir(parents=True, exist_ok=True)
            all_exist = False
    
    return all_exist

def test_news_fetcher():
    """测试新闻抓取"""
    print("\n--- 测试新闻抓取 ---")
    try:
        from news_fetcher import NewsFetcher
        fetcher = NewsFetcher()
        news = fetcher.fetch_all_sources()
        if news:
            print(f"✅ 成功获取 {len(news)} 条新闻")
            print(f"   示例: {news[0].title[:50]}...")
            return True
        else:
            print("❌ 未能获取新闻")
            return False
    except Exception as e:
        print(f"❌ 新闻抓取测试失败: {e}")
        return False

def test_tts():
    """测试TTS"""
    print("\n--- 测试TTS ---")
    try:
        from tts_generator import TTSGenerator
        generator = TTSGenerator()
        result = generator.generate_sync("这是一条测试语音", "./output/tts/test.wav")
        if result:
            print(f"✅ TTS生成成功: {result}")
            return True
        else:
            print("❌ TTS生成失败")
            return False
    except Exception as e:
        print(f"❌ TTS测试失败: {e}")
        return False

def test_video_composer():
    """测试视频合成"""
    print("\n--- 测试视频合成 ---")
    try:
        from video_composer import VideoComposer
        composer = VideoComposer()
        frame = composer.create_static_video_frame("测试新闻标题")
        if frame is not None:
            print(f"✅ 视频帧创建成功，尺寸: {frame.shape}")
            return True
        else:
            print("❌ 视频帧创建失败")
            return False
    except Exception as e:
        print(f"❌ 视频合成测试失败: {e}")
        return False

def main():
    print("=" * 50)
    print("  数字人直播系统 - 环境检测")
    print("=" * 50)
    
    print("\n--- 基础环境检测 ---")
    results = {
        "FFmpeg": check_ffmpeg(),
        "Python依赖": check_python_deps(),
        "Node.js": check_nodejs(),
        "edge-tts": check_edge_tts(),
    }
    
    print("\n--- 目录结构检测 ---")
    results["目录结构"] = check_directories()
    
    # 可选的功能测试
    print("\n" + "=" * 50)
    print("  功能测试")
    print("=" * 50)
    
    run_functional = input("\n是否运行功能测试? (y/n): ").lower() == 'y'
    
    if run_functional:
        results["新闻抓取"] = test_news_fetcher()
        results["TTS"] = test_tts()
        results["视频合成"] = test_video_composer()
    
    # 总结
    print("\n" + "=" * 50)
    print("  检测结果总结")
    print("=" * 50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\n总计: {passed}/{total} 项通过")
    
    if results.get("FFmpeg") and results.get("Python依赖"):
        print("\n🎉 基础环境已就绪，可以开始使用！")
        print("\n快速开始:")
        print("  python main.py --test     # 测试模式")
        print("  python main.py --once     # 单次运行")
        print("  python main.py            # 守护进程模式")
    else:
        print("\n⚠️ 请先安装缺少的依赖")
        print("  pip install -r requirements.txt")

if __name__ == "__main__":
    main()
