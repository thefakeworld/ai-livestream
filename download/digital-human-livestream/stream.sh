#!/bin/bash
# 推流管理脚本

PROJECT_DIR="/home/z/my-project/download/digital-human-livestream"
MONITOR_SCRIPT="$PROJECT_DIR/stream_monitor.py"
PID_FILE="$PROJECT_DIR/logs/stream_monitor.pid"
LOG_FILE="$PROJECT_DIR/logs/stream_monitor.log"

case "$1" in
    start)
        echo "启动推流监控服务..."
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "监控服务已在运行 (PID: $PID)"
                exit 0
            fi
        fi
        cd "$PROJECT_DIR"
        nohup python3 "$MONITOR_SCRIPT" >> "$LOG_FILE" 2>&1 &
        sleep 2
        if [ -f "$PID_FILE" ]; then
            echo "✓ 监控服务已启动 (PID: $(cat $PID_FILE))"
        else
            echo "✗ 启动失败"
        fi
        ;;
    
    stop)
        echo "停止推流监控服务..."
        # 停止监控进程
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            kill $PID 2>/dev/null
            rm -f "$PID_FILE"
        fi
        # 停止所有FFmpeg推流
        pkill -f "ffmpeg.*concat.*rtmp" 2>/dev/null
        echo "✓ 已停止"
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        echo "========================================"
        echo "推流服务状态检查"
        echo "========================================"
        echo ""
        
        # 检查监控进程
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "✓ 监控进程运行中 (PID: $PID)"
            else
                echo "✗ 监控进程已停止"
            fi
        else
            echo "✗ 监控进程未运行"
        fi
        echo ""
        
        # 检查FFmpeg推流
        FFMPEG_PID=$(pgrep -f "ffmpeg.*concat.*rtmp" 2>/dev/null | head -1)
        if [ -n "$FFMPEG_PID" ]; then
            echo "✓ FFmpeg推流运行中 (PID: $FFMPEG_PID)"
            # 显示进程信息
            ps -p $FFMPEG_PID -o pid,etime,%cpu,%mem --no-headers 2>/dev/null
        else
            echo "✗ FFmpeg推流未运行"
        fi
        echo ""
        
        # 检查网络连接
        echo "检查YouTube RTMP连接..."
        if timeout 5 bash -c "echo > /dev/tcp/a.rtmp.youtube.com/1935" 2>/dev/null; then
            echo "✓ YouTube RTMP服务器可达"
        else
            echo "✗ YouTube RTMP服务器不可达"
        fi
        echo ""
        
        # 显示最近日志
        if [ -f "$LOG_FILE" ]; then
            echo "最近日志:"
            echo "----------------------------------------"
            tail -10 "$LOG_FILE"
        fi
        echo ""
        echo "========================================"
        ;;
    
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "日志文件不存在"
        fi
        ;;
    
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
