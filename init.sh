#!/bin/bash

echo "=========================================="
echo "   地热流体资源建模系统 - 项目初始化"
echo "=========================================="

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "[1/4] 安装后端依赖..."
cd backend
pip install -r requirements.txt -q
echo "     ✓ 后端依赖安装完成"

echo ""
echo "[2/4] 初始化数据库..."
python init_db.py
echo "     ✓ 数据库初始化完成"

echo ""
echo "[3/4] 安装前端依赖..."
cd ../frontend
pnpm install --silent
echo "     ✓ 前端依赖安装完成"

echo ""
echo "[4/4] 构建前端..."
pnpm build
echo "     ✓ 前端构建完成"

echo ""
echo "=========================================="
echo "   初始化完成！"
echo "=========================================="
echo ""
echo "启动服务："
echo "  cd backend && python main.py"
echo ""
echo "访问地址："
echo "  http://localhost:5000"
echo ""
