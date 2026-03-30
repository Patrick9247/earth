#!/bin/bash

echo "停止地热流体资源建模系统..."

# 获取端口对应的进程 PID
PID=$(ss -lptn 'sport = :5000' 2>/dev/null | grep -oP 'pid=\K[0-9]+')

if [ -z "$PID" ]; then
    echo "服务未运行"
else
    kill $PID 2>/dev/null
    echo "✓ 服务已停止 (PID: $PID)"
fi
