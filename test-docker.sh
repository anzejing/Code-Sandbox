#!/bin/bash
# Docker 部署验证脚本

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          Code-Sandbox Docker 部署验证                    ║"
echo "╚══════════════════════════════════════════════════════════╝"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "✗ Docker 未安装"
    exit 1
fi
echo "✓ Docker 已安装：$(docker --version)"

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "✗ Docker Compose 未安装"
    exit 1
fi
echo "✓ Docker Compose 已就绪"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 1: 构建镜像"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker build -t code-sandbox-mcp . || {
    echo "✗ 镜像构建失败"
    exit 1
}
echo "✓ 镜像构建成功"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 2: 启动容器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 停止旧容器
docker stop code-sandbox-test 2>/dev/null || true
docker rm code-sandbox-test 2>/dev/null || true

# 启动新容器
docker run -d \
    --name code-sandbox-test \
    -e PYTHONPATH=/app:/opt/venv/lib/python3.11/site-packages \
    code-sandbox-mcp

echo "✓ 容器已启动"
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 3: 验证环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查容器状态
if ! docker ps | grep -q code-sandbox-test; then
    echo "✗ 容器未运行"
    docker logs code-sandbox-test
    exit 1
fi
echo "✓ 容器运行正常"

# 运行验证脚本
echo ""
echo "运行包导入验证..."
docker exec code-sandbox-test python /app/docker_verify.py || {
    echo "✗ 验证失败"
    docker logs code-sandbox-test
    exit 1
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 4: 清理"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker stop code-sandbox-test
docker rm code-sandbox-test
echo "✓ 测试容器已清理"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                   ✅ 所有验证通过！                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "现在可以部署生产环境："
echo "  docker-compose up -d"
echo ""
