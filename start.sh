#!/bin/bash

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT/backend"

echo "启动地热流体资源建模系统..."

# 检查端口是否被占用
if ss -lptn 'sport = :5000' 2>/dev/null | grep -q LISTEN; then
    echo "警告: 端口 5000 已被占用"
    echo "如需重启，请先运行: ./stop.sh"
    exit 1
fi

# 后台启动
nohup python main.py > /app/work/logs/bypass/backend.log 2>&1 &

sleep 3

if ss -lptn 'sport = :5000' 2>/dev/null | grep -q LISTEN; then
    echo "✓ 服务启动成功"
    echo "  访问地址: http://localhost:5000"
    echo "  日志文件: /app/work/logs/bypass/backend.log"
else
    echo "✗ 服务启动失败，请查看日志"
    tail -20 /app/work/logs/bypass/backend.log
fi
