@echo off
chcp 65001 > nul
echo ========================================
echo   数字人YouTube无人值守直播系统
echo ========================================

:: 检查Python
python --version > nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

:: 检查FFmpeg
ffmpeg -version > nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到FFmpeg，请先安装FFmpeg
    echo   下载地址: https://ffmpeg.org/download.html
    pause
    exit /b 1
)

:: 创建虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 安装依赖
echo 检查依赖...
pip install -r requirements.txt --quiet

:: 创建目录
if not exist "assets\video" mkdir assets\video
if not exist "assets\audio\music" mkdir assets\audio\music
if not exist "assets\news" mkdir assets\news
if not exist "output\tts" mkdir output\tts
if not exist "logs" mkdir logs

echo.
echo ========================================
echo 环境准备完成，请选择运行模式：
echo   1. 守护进程模式（定时更新新闻）
echo   2. 单次运行模式
echo   3. 测试模式（只生成视频）
echo   4. 使用自定义新闻文件
echo ========================================
echo.

set /p choice="请输入选项 (1-4): "

if "%choice%"=="1" (
    echo 启动守护进程模式...
    python main.py
) else if "%choice%"=="2" (
    echo 启动单次运行模式...
    python main.py --once
) else if "%choice%"=="3" (
    echo 启动测试模式...
    python main.py --test
) else if "%choice%"=="4" (
    set /p news_file="请输入新闻文件路径: "
    echo 使用自定义新闻文件...
    python main.py --news "%news_file%"
) else (
    echo 无效选项，启动守护进程模式...
    python main.py
)

pause
