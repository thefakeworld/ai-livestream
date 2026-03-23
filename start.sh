#!/bin/bash
# AI Livestream 启动脚本
# 解决权限问题并启动所有服务

set -e

PROJECT_DIR="/home/z/my-project/ai-livestream"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              AI Livestream 启动脚本                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# 检查依赖
check_dependencies() {
    echo "🔍 检查依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 未安装"
        exit 1
    fi
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js 未安装"
        exit 1
    fi
    
    # 检查 FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        echo "⚠️  FFmpeg 未安装，部分功能可能受限"
    fi
    
    echo "✅ 依赖检查通过"
}

# 修复文件权限
fix_permissions() {
    echo "🔧 修复文件权限..."
    
    cd "$FRONTEND_DIR"
    
    # 修复 root 创建的文件
    for file in tsconfig.json next.config.ts tailwind.config.ts postcss.config.mjs package.json; do
        if [ -f "$file" ]; then
            # 获取文件内容并重新创建
            content=$(cat "$file" 2>/dev/null)
            if [ -n "$content" ]; then
                echo "$content" > "$file"
            fi
        fi
    done
    
    echo "✅ 权限修复完成"
}

# 启动后端
start_backend() {
    echo "🚀 启动后端服务..."
    
    # 停止旧进程
    pkill -f "uvicorn api.main:app" 2>/dev/null || true
    sleep 1
    
    cd "$BACKEND_DIR"
    
    # 检查是否需要安装依赖
    if ! python3 -c "import fastapi" 2>/dev/null; then
        echo "📦 安装后端依赖..."
        pip install -r requirements.txt --break-system-packages -q 2>/dev/null || true
    fi
    
    # 启动后端
    PYTHONPATH="$BACKEND_DIR" /home/z/.local/bin/uvicorn api.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        > /tmp/backend.log 2>&1 &
    
    BACKEND_PID=$!
    echo "   Backend PID: $BACKEND_PID"
    
    # 等待启动
    sleep 3
    
    # 健康检查
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 后端启动成功: http://localhost:8000"
    else
        echo "❌ 后端启动失败，请检查日志: /tmp/backend.log"
        tail -20 /tmp/backend.log
    fi
}

# 启动前端
start_frontend() {
    echo "🚀 启动前端服务..."
    
    # 停止旧进程
    pkill -f "next dev" 2>/dev/null || true
    sleep 1
    
    cd "$FRONTEND_DIR"
    
    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        echo "📦 安装前端依赖..."
        npm install --silent 2>/dev/null
    fi
    
    # 启动前端
    npm run dev > /tmp/frontend.log 2>&1 &
    
    FRONTEND_PID=$!
    echo "   Frontend PID: $FRONTEND_PID"
    
    # 等待启动
    sleep 5
    
    # 健康检查
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ 前端启动成功: http://localhost:3000"
    else
        echo "❌ 前端启动失败，请检查日志: /tmp/frontend.log"
        tail -20 /tmp/frontend.log
    fi
}

# 显示状态
show_status() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    服务状态                                  ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    
    # 后端状态
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "║  ✅ 后端 API: http://localhost:8000                          ║"
        echo "║     文档: http://localhost:8000/docs                         ║"
    else
        echo "║  ❌ 后端 API: 未运行                                         ║"
    fi
    
    # 前端状态
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "║  ✅ 前端: http://localhost:3000                              ║"
    else
        echo "║  ❌ 前端: 未运行                                             ║"
    fi
    
    echo "╚══════════════════════════════════════════════════════════════╝"
}

# 主流程
main() {
    check_dependencies
    fix_permissions
    start_backend
    start_frontend
    show_status
}

# 执行
main "$@"
