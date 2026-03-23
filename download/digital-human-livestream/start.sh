#!/bin/bash
# 数字人YouTube直播启动脚本

echo "========================================"
echo "  数字人YouTube无人值守直播系统"
echo "========================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python"
    exit 1
fi

# 检查FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "错误: 未找到FFmpeg，请先安装FFmpeg"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: choco install ffmpeg"
    exit 1
fi

# 检查Node.js（用于TTS）
if ! command -v node &> /dev/null; then
    echo "警告: 未找到Node.js，将使用edge-tts作为备用TTS引擎"
    echo "  建议安装Node.js以获得更好的TTS效果"
fi

# 安装Python依赖
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo "检查依赖..."
pip install -r requirements.txt --quiet

# 安装Node.js依赖
if command -v node &> /dev/null; then
    if [ ! -d "node_modules" ]; then
        echo "安装Node.js依赖..."
        npm install z-ai-web-dev-sdk
    fi
fi

# 创建必要的目录
mkdir -p assets/video assets/audio/music assets/news output/tts logs

echo ""
echo "========================================"
echo "环境准备完成，请选择运行模式："
echo "  1. 守护进程模式（定时更新新闻）"
echo "  2. 单次运行模式"
echo "  3. 测试模式（只生成视频）"
echo "  4. 使用自定义新闻文件"
echo "========================================"
echo ""

read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo "启动守护进程模式..."
        python3 main.py
        ;;
    2)
        echo "启动单次运行模式..."
        python3 main.py --once
        ;;
    3)
        echo "启动测试模式..."
        python3 main.py --test
        ;;
    4)
        read -p "请输入新闻文件路径: " news_file
        echo "使用自定义新闻文件..."
        python3 main.py --news "$news_file"
        ;;
    *)
        echo "无效选项，启动守护进程模式..."
        python3 main.py
        ;;
esac
