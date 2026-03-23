#!/bin/bash
# API 接口验证脚本 - 检查前后端接口一致性

set -e

API_BASE="http://localhost:8000/api/v1"
FRONTEND_BASE="http://localhost:3000"

echo "🔍 API 接口一致性验证"
echo "========================"

# 定义所有接口
declare -A ENDPOINTS=(
    ["director_get"]="GET /director"
    ["director_status"]="GET /director/status"
    ["director_start"]="POST /director/start"
    ["director_stop"]="POST /director/stop"
    ["director_queue"]="GET /director/queue"
    ["platform_list"]="GET /platform/list"
    ["platform_available"]="GET /platform/available"
    ["stream_status"]="GET /stream/status"
)

# 测试后端
echo ""
echo "📦 测试后端接口..."
for key in "${!ENDPOINTS[@]}"; do
    IFS=' ' read -r method path <<< "${ENDPOINTS[$key]}"
    
    if [ "$method" == "GET" ]; then
        code=$(curl -s -o /dev/null -w "%{http_code}" "${API_BASE}${path}")
    else
        code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_BASE}${path}")
    fi
    
    if [ "$code" == "200" ] || [ "$code" == "422" ]; then
        echo "  ✅ [BE] $method $path → $code"
    else
        echo "  ❌ [BE] $method $path → $code"
    fi
done

# 测试前端代理
echo ""
echo "📦 测试前端代理..."
for key in "${!ENDPOINTS[@]}"; do
    IFS=' ' read -r method path <<< "${ENDPOINTS[$key]}"
    
    if [ "$method" == "GET" ]; then
        code=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_BASE}/api${path}")
        code_v1=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_BASE}/api/v1${path}")
    else
        code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${FRONTEND_BASE}/api${path}")
        code_v1=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${FRONTEND_BASE}/api/v1${path}")
    fi
    
    if [ "$code" == "200" ] || [ "$code" == "422" ]; then
        echo "  ✅ [FE] $method /api$path → $code"
    else
        echo "  ❌ [FE] $method /api$path → $code"
    fi
    
    if [ "$code_v1" == "200" ] || [ "$code_v1" == "422" ]; then
        echo "  ✅ [FE] $method /api/v1$path → $code_v1"
    else
        echo "  ❌ [FE] $method /api/v1$path → $code_v1"
    fi
done

echo ""
echo "✅ 验证完成"
