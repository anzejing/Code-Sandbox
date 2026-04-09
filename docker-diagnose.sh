#!/bin/bash
# Docker 部署诊断脚本

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          Code-Sandbox Docker 诊断工具                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "✗ Docker 未安装"
    exit 1
fi
echo "✓ Docker: $(docker --version)"

# 检查 docker-compose
if command -v docker-compose &> /dev/null; then
    echo "✓ Docker Compose: $(docker-compose --version)"
elif docker compose version &> /dev/null; then
    echo "✓ Docker Compose: $(docker compose version)"
else
    echo "✗ Docker Compose 未安装"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. 容器状态检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CONTAINER_STATUS=$(docker ps -a --filter "name=code-sandbox-mcp" --format "{{.Status}}" 2>/dev/null || echo "")

if [ -z "$CONTAINER_STATUS" ]; then
    echo "✗ 容器未运行"
    echo ""
    echo "建议操作:"
    echo "  docker-compose up -d"
else
    echo "✓ 容器状态：$CONTAINER_STATUS"
    
    # 检查是否健康
    if [[ "$CONTAINER_STATUS" == *"healthy"* ]]; then
        echo "✓ 健康检查通过"
    elif [[ "$CONTAINER_STATUS" == *"unhealthy"* ]]; then
        echo "⚠ 健康检查失败"
    elif [[ "$CONTAINER_STATUS" == *"Restarting"* ]]; then
        echo "⚠ 容器正在重启 - 可能缺少 stdin_open 和 tty 配置"
        echo ""
        echo "建议操作:"
        echo "  1. 检查 docker-compose.yml 是否包含:"
        echo "     stdin_open: true"
        echo "     tty: true"
        echo "  2. 重启容器:"
        echo "     docker-compose down && docker-compose up -d"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. 配置检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "docker-compose.yml" ]; then
    echo "✓ docker-compose.yml 存在"
    
    # 检查 stdin_open
    if grep -q "stdin_open" docker-compose.yml; then
        echo "✓ stdin_open: 已配置"
    else
        echo "✗ stdin_open: 未配置（可能导致重启）"
    fi
    
    # 检查 tty
    if grep -q "tty" docker-compose.yml; then
        echo "✓ tty: 已配置"
    else
        echo "✗ tty: 未配置（可能导致重启）"
    fi
    
    # 检查 PYTHONPATH
    if grep -q "PYTHONPATH" docker-compose.yml; then
        echo "✓ PYTHONPATH: 已配置"
    else
        echo "⚠ PYTHONPATH: 未配置"
    fi
else
    echo "✗ docker-compose.yml 不存在"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. 镜像检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

IMAGE_EXISTS=$(docker images --format "{{.Repository}}" | grep -c "code-sandbox" || echo "0")

if [ "$IMAGE_EXISTS" -gt 0 ]; then
    echo "✓ 镜像已构建"
    docker images | grep code-sandbox
else
    echo "✗ 镜像未构建"
    echo ""
    echo "建议操作:"
    echo "  docker-compose build"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. 日志检查（最近 10 行）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$CONTAINER_STATUS" ]; then
    docker logs code-sandbox-mcp --tail 10 2>&1 | head -10
else
    echo "容器未运行，无法查看日志"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. 功能测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "$CONTAINER_STATUS" == *"Up"* ]]; then
    echo "运行功能测试..."
    
    # 测试导入
    RESULT=$(docker exec code-sandbox-mcp python -c "from src.server import mcp; print('OK')" 2>&1 || echo "FAILED")
    if [ "$RESULT" == "OK" ]; then
        echo "✓ 模块导入：正常"
    else
        echo "✗ 模块导入：失败"
        echo "  错误：$RESULT"
    fi
    
    # 测试执行
    RESULT=$(docker exec code-sandbox-mcp python -c "
import asyncio
from src.sandbox.engine import ExecutionEngine
async def test():
    engine = ExecutionEngine()
    result = await engine.execute('print(\"test\")')
    return 'OK' if result.status.value == 'success' else 'FAILED'
print(asyncio.run(test()))
" 2>&1 || echo "FAILED")
    
    if [ "$RESULT" == "OK" ]; then
        echo "✓ 代码执行：正常"
    else
        echo "✗ 代码执行：失败"
        echo "  错误：$RESULT"
    fi
    
    # 运行完整验证
    echo ""
    echo "运行完整验证脚本..."
    docker exec code-sandbox-mcp python /app/docker_verify.py
else
    echo "容器未运行，跳过功能测试"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    诊断完成                              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "快速修复命令:"
echo "  # 重启容器"
echo "  docker-compose down && docker-compose up -d"
echo ""
echo "  # 查看实时日志"
echo "  docker-compose logs -f"
echo ""
echo "  # 重新构建镜像"
echo "  docker-compose build --no-cache"
echo ""
