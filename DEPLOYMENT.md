# Code-Sandbox 生产环境部署指南

## 快速部署（5 分钟）

### 1. 构建并启动

```bash
# 进入项目目录
cd /path/to/code-sandbox

# 构建镜像（首次约 5-10 分钟，包含 numpy/pandas/matplotlib）
docker-compose build

# 启动服务
docker-compose up -d

# 查看状态（应该显示 Up (healthy)）
docker-compose ps

# 查看日志
docker-compose logs -f
```

**重要配置说明：**

`docker-compose.yml` 中必须包含以下配置以保持容器稳定运行：

```yaml
services:
  code-sandbox:
    stdin_open: true  # 保持 stdin 打开（FastMCP stdio 模式必需）
    tty: true         # 分配伪终端
    restart: unless-stopped
```

缺少 `stdin_open` 和 `tty` 会导致容器不断重启。

### 2. 验证环境

```bash
# 运行验证脚本
docker-compose run --rm verify

# 或手动验证
docker exec code-sandbox-mcp python /app/docker_verify.py
```

预期输出：
```
✓ Python 版本：3.11.x
✓ FastMCP: 3.2.2
✓ MCP: OK
✓ src.sandbox: 0.1.0
✓ src.server: OK
✓ 执行测试：success
```

### 3. 测试执行

```bash
# 进入容器测试
docker exec code-sandbox-mcp python -c "
import asyncio
from src.sandbox.engine import ExecutionEngine

async def test():
    engine = ExecutionEngine()
    
    # 测试 1: 基础执行
    result = await engine.execute('print(\"Hello from Docker!\")')
    print(f'测试 1: {result.stdout.strip()}')
    
    # 测试 2: 安全拦截
    result = await engine.execute('import os')
    print(f'测试 2: {result.status.value}')

asyncio.run(test())
"

# 预期输出：
# 测试 1: Hello from Docker!
# 测试 2: security_violation
```

---

## 配置到 LLM 平台

### 方式一：本地 LLM（Claude Desktop / Cursor）

LLM 和 Docker 在**同一台机器**上：

#### Claude Desktop

编辑配置文件：

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "code-sandbox": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "code-sandbox-mcp",
        "python",
        "-m",
        "src.server"
      ]
    }
  }
}
```

#### Cursor IDE

1. 打开 **Settings** → **MCP**
2. 点击 **Add Server**
3. 配置：
   - **Name:** `code-sandbox`
   - **Type:** `stdio`
   - **Command:** `docker exec -i code-sandbox-mcp python -m src.server`

#### Cline (VS Code)

```json
{
  "mcpServers": [
    {
      "name": "code-sandbox",
      "command": "docker",
      "args": ["exec", "-i", "code-sandbox-mcp", "python", "-m", "src.server"]
    }
  ]
}
```

---

### 方式二：远程服务器部署

LLM 在本地，Docker 在**远程服务器**上：

#### 步骤 1: 服务器配置

```bash
# 在服务器上
ssh user@your-server.com

# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 克隆项目
git clone <repository-url> /opt/code-sandbox
cd /opt/code-sandbox

# 启动服务
docker-compose up -d

# 设置开机自启
docker-compose restart
```

#### 步骤 2: 配置 SSH 免密登录

```bash
# 本地生成 SSH 密钥（如果没有）
ssh-keygen -t ed25519 -C "code-sandbox"

# 复制到服务器
ssh-copy-id user@your-server.com

# 测试连接
ssh user@your-server.com "docker ps"
```

#### 步骤 3: LLM 配置

**Claude Desktop:**

```json
{
  "mcpServers": {
    "code-sandbox": {
      "command": "ssh",
      "args": [
        "-i", "/Users/yourname/.ssh/id_ed25519",
        "user@your-server.com",
        "PYTHONPATH=/opt/code-sandbox /opt/code-sandbox/.venv/bin/python -m src.server"
      ]
    }
  }
}
```

**或使用 Docker 远程执行:**

```json
{
  "mcpServers": {
    "code-sandbox": {
      "command": "ssh",
      "args": [
        "-i", "/Users/yourname/.ssh/id_ed25519",
        "user@your-server.com",
        "docker exec -i code-sandbox-mcp python -m src.server"
      ]
    }
  }
}
```

---

### 方式三：HTTP/SSE 模式（远程访问）

通过 HTTP 暴露 MCP 服务，支持远程 LLM 连接。

#### 步骤 1: 配置环境变量

**方法 A: 使用 .env 文件**

```bash
# 编辑 .env 文件
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8080
```

**方法 B: 修改 docker-compose.yml**

```yaml
services:
  code-sandbox:
    environment:
      - MCP_TRANSPORT=http  # 切换为 HTTP 模式
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8765  # 使用不常用端口，避免冲突
    # 开放端口
    ports:
      - "8765:8765"
```

#### 步骤 2: 重启服务

```bash
# 应用配置
docker-compose down
docker-compose up -d

# 查看日志确认 HTTP 模式启动
docker-compose logs | grep "HTTP mode"
# 应显示：Starting MCP server in HTTP mode on 0.0.0.0:8080
```

#### 步骤 3: LLM 配置

```json
{
  "mcpServers": {
    "code-sandbox": {
      "url": "http://your-server-ip:8765/sse",
      "transport": "sse"
    }
  }
}
```

#### 步骤 4: 测试连接

```bash
# 测试 HTTP 端点
curl http://localhost:8765/sse

# 应返回 SSE 连接信息
```

---

## 安全配置

### 1. 防火墙

```bash
# 只允许特定 IP 访问 SSH
sudo ufw allow from 192.168.1.0/24 to any port 22

# 如果不使用 HTTP 模式，关闭其他端口
sudo ufw default deny incoming
sudo ufw enable
```

### 2. Docker 安全

```yaml
# docker-compose.yml 已配置
read_only: true        # 只读文件系统
tmpfs:                 # 临时目录
  - /tmp
  - /app/logs
deploy:
  resources:
    limits:
      cpus: '2.0'      # CPU 限制
      memory: 2G       # 内存限制
```

### 3. 网络隔离

```yaml
# 完全禁用网络（如果不需要 pip install）
network_mode: "none"

# 或创建隔离网络
networks:
  sandbox-net:
    driver: bridge
    internal: true  # 无法访问外网
```

---

## 诊断工具

### 自动诊断脚本

```bash
# 运行诊断
./docker-diagnose.sh

# 检查项目:
# ✓ Docker 和 Docker Compose 版本
# ✓ 容器状态（是否运行/健康）
# ✓ 配置检查（stdin_open, tty, PYTHONPATH）
# ✓ 镜像存在性
# ✓ 日志检查
# ✓ 功能测试（导入 + 执行）
```

### 手动诊断

```bash
# 1. 检查容器状态
docker-compose ps

# 2. 查看配置
docker-compose config

# 3. 测试模块导入
docker exec code-sandbox-mcp python -c "from src.server import mcp; print('OK')"

# 4. 运行完整验证
docker exec code-sandbox-mcp python /app/docker_verify.py

# 5. 测试代码执行
docker exec code-sandbox-mcp python -c "
import asyncio
from src.sandbox.engine import ExecutionEngine
async def test():
    engine = ExecutionEngine()
    result = await engine.execute('print(\"test\")')
    print(f'执行：{result.status.value}')
asyncio.run(test())
"
```

---

## 监控和维护

### 查看日志

```bash
# 实时日志
docker-compose logs -f

# 最近 100 行
docker-compose logs --tail=100

# 错误日志
docker-compose logs | grep ERROR
```

### 资源监控

```bash
# CPU/内存使用
docker stats code-sandbox-mcp

# 容器状态
docker inspect code-sandbox-mcp | grep -A 5 "State"
```

### 备份和恢复

```bash
# 备份配置
tar -czf code-sandbox-backup.tar.gz \
    docker-compose.yml \
    .env \
    src/

# 恢复
tar -xzf code-sandbox-backup.tar.gz
docker-compose up -d
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建
docker-compose build --no-cache

# 重启
docker-compose up -d
```

---

## 故障排查

### 问题 1: 容器不断重启

**症状：** `docker-compose ps` 显示 `Restarting` 状态

**原因：** FastMCP 的 stdio 模式需要保持 stdin 打开

**解决方案：**

```yaml
# docker-compose.yml 中添加
services:
  code-sandbox:
    stdin_open: true  # 必需
    tty: true         # 必需
```

然后重启：

```bash
docker-compose down
docker-compose up -d
```

### 问题 2: 容器启动失败

```bash
# 查看日志
docker-compose logs code-sandbox

# 检查配置
docker-compose config

# 手动测试
docker run --rm code-sandbox-mcp python --version
```

### 问题 3: LLM 连接失败

```bash
# 测试 Docker 命令
docker exec code-sandbox-mcp python -m src.server --help

# 测试 SSH（远程）
ssh -i ~/.ssh/id_ed25519 user@server "docker ps"

# 检查权限
ls -la ~/.ssh/id_ed25519  # 应该是 600
```

### 问题 4: 包导入失败

```bash
# 进入容器
docker exec -it code-sandbox-mcp bash

# 检查 Python 路径
python -c "import sys; print(sys.path)"

# 手动测试导入
python -c "import fastmcp; import src.server"
```

### 问题 5: 内存不足

```bash
# 调整 docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G  # 增加限制
```

---

## 性能优化

### 1. 启用缓存

```bash
# .env 文件
ENABLE_CACHE=true
CACHE_MAX_SIZE=1000
```

### 2. 调整超时

```bash
# .env 文件
SANDBOX_TIMEOUT=60  # 增加超时时间
```

### 3. 预加载常用包

```dockerfile
# Dockerfile 中添加
RUN pip install numpy pandas matplotlib scipy scikit-learn
```

---

## 完整示例

### 生产环境 docker-compose.yml

```yaml
version: '3.8'

services:
  code-sandbox:
    build: .
    container_name: code-sandbox-mcp
    restart: always
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
      - SANDBOX_TIMEOUT=30
      - MAX_MEMORY_MB=512
      - ENABLE_CACHE=true
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    healthcheck:
      test: ["CMD", "python", "/app/docker_verify.py"]
      interval: 30s
      timeout: 10s
      retries: 3
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
```

### 一键部署脚本

```bash
#!/bin/bash
set -e

echo "部署 Code-Sandbox MCP..."

# 克隆项目
git clone <repository-url> /opt/code-sandbox
cd /opt/code-sandbox

# 构建
docker-compose build

# 启动
docker-compose up -d

# 验证
docker-compose run --rm verify

echo "部署完成！"
echo "在 LLM 中配置："
echo "  command: docker"
echo "  args: ['exec', '-i', 'code-sandbox-mcp', 'python', '-m', 'src.server']"
```

---

## 联系支持

遇到问题？检查以下顺序：

1. `docker-compose ps` - 容器是否运行
2. `docker-compose logs` - 查看错误日志
3. `docker-compose run --rm verify` - 验证环境
4. 检查 LLM 配置文件语法
5. 测试 SSH 连接（远程部署）
