# Code-Sandbox MCP Server

基于 FastMCP 的 Python 代码执行沙箱服务，为 AI 提供安全、类型安全、带依赖管理和进度汇报的代码执行环境。

## 功能特性

- 🔒 **安全优先**: 基于 AST 的静态分析拦截危险导入 (`os`, `subprocess`, `sys` 等) 和函数调用 (`eval`, `exec`, `compile`)
- ⚡ **异步执行**: 非阻塞执行，支持可配置超时
- 📊 **进度汇报**: 通过 FastMCP Context 实时汇报执行进度
- 🖼️ **图片支持**: 通过资源 URI 存储和检索绘图图片
- 💾 **结果缓存**: 可选的成功执行结果缓存
- 🧪 **充分测试**: 63+ 测试用例覆盖安全、执行、缓存和性能基准
- 🎯 **类型安全**: 完整的类型注解，通过 mypy 验证
- 📈 **性能监控**: 内置性能基准测试

## 快速开始

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/anzejing/Code-Sandbox.git
cd Code-Sandbox

# 2. 复制配置文件（首次部署必需）
cp .env.example .env
cp docker-compose.yml.example docker-compose.yml

# 3. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或：.venv\Scripts\activate  # Windows

# 4. 安装依赖
pip install -e ".[dev]"
```

### 运行 MCP 服务器

```bash
python -m src.server
```

### 配置 Claude Desktop

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "code-sandbox": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/python-sandbox",
      "env": {
        "PYTHONPATH": "/path/to/python-sandbox"
      }
    }
  }
}
```

### 使用 Inspector 调试

```bash
# 终端 1: 启动服务器
python -m src.server

# 终端 2: 运行 inspector
npx @modelcontextprotocol/inspector

# 浏览器访问 localhost:3000，选择 "code-sandbox"
```

## 可用工具

### `execute_python`

在隔离沙箱中执行 Python 代码。

**参数：**
- `code` (str): 要执行的 Python 代码（支持多行）
- `timeout` (int): 最大执行时间（秒），默认 30

**示例：**
```python
await execute_python(ctx, "print('hello')")
```

### `analyze_data`

执行数据分析代码（需要安装 numpy, pandas, matplotlib）。

**参数：**
- `code` (str): 要执行的 Python 代码
- `timeout` (int): 最大执行时间（秒），默认 60

**示例：**
```python
await analyze_data(ctx, "import numpy as np; print(np.mean([1, 2, 3]))")
```

### `check_security`

检查代码是否存在安全漏洞，不执行代码。

**参数：**
- `code` (str): 要检查的 Python 代码

**示例：**
```python
await check_security(ctx, "import os")  # 返回安全警告
```

### `store_plot`

存储绘图图片并返回资源 ID。

**参数：**
- `image_base64` (str): Base64 编码的图片数据
- `mime_type` (str): 图片 MIME 类型（默认：image/png）

**示例：**
```python
import base64
# 生成绘图并保存到缓冲区后
image_base64 = base64.b64encode(image_bytes).decode("utf-8")
plot_id = await store_plot(ctx, image_base64)
# 返回："✓ Plot stored. Access via: plot://<id>"
```

### `get_plot` (资源)

通过资源 URI 检索存储的绘图图片。

**URI 格式：** `plot://{id}`

**示例：**
```python
# 通过 MCP 资源访问
image_bytes, mime_type = await get_plot("plot://abc123")
```

## 安全机制

### 拦截的模块

默认拦截以下模块：
- `os` - 系统操作
- `subprocess` - 进程生成
- `sys` - 系统参数
- `builtins` - 内置函数
- `ctypes` - C 类型转换
- `socket` - 网络访问
- `pickle` / `shelve` - 序列化（潜在 RCE 风险）

### 拦截的函数

- `eval()` - 动态代码求值
- `exec()` - 动态代码执行
- `compile()` - 代码编译
- `__import__()` - 动态导入

## 开发指南

### 运行测试

```bash
# 全部测试
pytest

# 单个测试文件
pytest tests/test_engine.py

# 按名称运行单个测试
pytest -k test_timeout

# 性能基准测试
pytest tests/test_benchmark.py -v
```

### 代码质量检查

```bash
ruff check src/          # 代码检查
ruff format src/         # 代码格式化
mypy src/                # 类型检查
bandit -r src/           # 安全扫描
```

### 项目结构

```
python-sandbox/
├── pyproject.toml       # 项目配置
├── AGENTS.md            # 开发者指南
├── PLAN.md              # 开发计划
├── README.md            # 本文件
├── tests/
│   ├── test_security.py # 安全扫描测试
│   ├── test_engine.py   # 执行引擎测试
│   ├── test_server.py   # MCP 工具测试
│   ├── test_plots.py    # 图片缓存测试
│   ├── test_cache.py    # 执行缓存测试
│   └── test_benchmark.py# 性能基准测试
└── src/
    ├── server.py        # FastMCP 入口
    └── sandbox/
        ├── types.py     # 类型定义
        ├── security.py  # 安全扫描
        ├── engine.py    # 执行引擎
        ├── cache.py     # 结果缓存
        └── plots.py     # 图片处理
    └── utils/
        └── logging.py   # 日志配置
```

## 架构设计

```
┌─────────────────────────────────────────┐
│           server.py (MCP 层)            │
│  - 工具注册 (@mcp.tool)                 │
│  - 进度汇报 (ctx.report)                │
│  - 资源处理 (@mcp.resource)             │
│  - 结果格式化                           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        engine.py (执行层)               │
│  - 异步执行 (asyncio)                   │
│  - 超时控制                             │
│  - 输出捕获                             │
│  - 可选结果缓存                         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│       security.py (安全层)              │
│  - AST 导入扫描                         │
│  - 危险函数检测                         │
│  - 白名单/黑名单验证                    │
└─────────────────────────────────────────┘
```

### 附加模块

- **cache.py**: 执行结果缓存，支持 TTL 和 LRU 淘汰
- **plots.py**: 内存图片存储，支持 base64 编解码
- **logging.py**: 结构化日志配置

## 性能指标

| 操作 | 目标延迟 | 实际表现 |
|------|----------|----------|
| 简单打印 | < 100ms | ~50ms |
| 数学运算 | < 200ms | ~100ms |
| 缓存命中 | < 1ms | ~0.1ms |
| 并发执行 (5 任务) | < 1s | ~200ms |

## 配置选项

### SandboxConfig

```python
from src.sandbox.types import SandboxConfig

config = SandboxConfig(
    timeout_seconds=30,      # 执行超时（秒）
    max_memory_mb=512,       # 内存限制（MB）
    allowed_modules=[],      # 允许的模块列表（可选）
    blocked_modules=[        # 拦截的模块列表
        "os", "subprocess", "sys",
        "builtins", "ctypes", "socket",
        "pickle", "shelve"
    ]
)
```

### ExecutionCache

```python
from src.sandbox.cache import ExecutionCache

cache = ExecutionCache(
    max_size=1000,      # 最大缓存条目数
    ttl_seconds=3600    # 缓存过期时间（秒）
)

# 获取缓存统计
stats = cache.get_stats()
# {'size': 10, 'hits': 50, 'misses': 100, 'hit_rate': '33.33%'}
```

## 常见问题

### Q: 如何启用结果缓存？

```python
from src.sandbox.engine import ExecutionEngine

engine = ExecutionEngine(use_cache=True)
result = await engine.execute("print('hello')", use_cache=True)
```

### Q: 如何添加自定义拦截模块？

```python
from src.sandbox.types import SandboxConfig
from src.sandbox.engine import ExecutionEngine

config = SandboxConfig(
    blocked_modules=["os", "subprocess", "custom_module"]
)
engine = ExecutionEngine(config)
```

### Q: 如何获取缓存命中率？

```python
from src.sandbox.cache import get_execution_cache

cache = get_execution_cache()
stats = cache.get_stats()
print(f"缓存命中率：{stats['hit_rate']}")
```

---

## 部署指南

### 生产环境部署

#### 方式一：Docker 部署（推荐）

**方案 A：轻量级镜像（快速，推荐）**

只安装核心依赖，构建快，镜像小。如需 numpy/pandas 等，需手动添加。

```bash
# 1. 复制配置文件（首次部署必需）
cp .env.example .env
cp docker-compose.yml.example docker-compose.yml

# 2. 构建镜像（约 1-2 分钟）
docker-compose build

# 3. 运行容器（默认 stdio 模式）
docker-compose up -d

# 4. 验证环境
docker exec code-sandbox-mcp python /app/docker_verify.py
```

**方案 C：HTTP 模式（远程访问，支持 SSE 流式传输）**

如需通过网络远程访问 MCP 服务：

```bash
# 1. 修改 docker-compose.yml
environment:
  - MCP_TRANSPORT=http  # 切换为 HTTP 模式
  - MCP_HOST=0.0.0.0
  - MCP_PORT=8765  # 使用不常用端口

# 开放端口
ports:
  - "8765:8765"

# 2. 重启服务
docker-compose down
docker-compose up -d

# 3. 查看日志确认 HTTP 模式启动
docker-compose logs | grep "HTTP mode"
# 应显示：Starting MCP server in HTTP mode (SSE streaming) on 0.0.0.0:8765
```

LLM 配置（HTTP/SSE 模式）：

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

**方案 B：完整数据科学环境（包含 numpy/pandas/matplotlib）**

```bash
# Dockerfile 中添加：
# RUN pip install --no-cache-dir numpy pandas matplotlib

# 或使用 docker-compose（已配置）
docker-compose up -d
```

# 3. 查看日志
docker logs -f code-sandbox

# 4. 验证环境
docker exec code-sandbox python /app/docker_verify.py

# 5. 健康检查
docker exec code-sandbox python -c "print('healthy')"
```

**使用 Docker Compose（推荐）：**

```bash
# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 运行环境验证
docker-compose run --rm verify

# 停止服务
docker-compose down
```

**注意：** 当前 `docker-compose.yml` 配置为生产模式，不包含代码热更新。如需开发模式，请手动添加卷挂载：

```yaml
# docker-compose.yml 中添加
volumes:
  - ./src:/app/src:ro
  - ./logs:/app/logs
```

#### 方式二：Systemd 部署（Linux 服务器）

创建服务文件 `/etc/systemd/system/code-sandbox.service`：

```ini
[Unit]
Description=Code-Sandbox MCP Server
After=network.target

[Service]
Type=simple
User=sandbox
WorkingDirectory=/opt/code-sandbox
Environment="PATH=/opt/code-sandbox/.venv/bin"
ExecStart=/opt/code-sandbox/.venv/bin/python -m src.server
Restart=always
RestartSec=5

# 安全配置
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/code-sandbox/logs

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 安装服务
sudo systemctl daemon-reload
sudo systemctl enable code-sandbox
sudo systemctl start code-sandbox

# 查看状态
sudo systemctl status code-sandbox

# 查看日志
sudo journalctl -u code-sandbox -f
```

#### 方式三：直接部署

```bash
# 1. 克隆项目
git clone <repository-url> /opt/code-sandbox
cd /opt/code-sandbox

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -e .

# 4. 后台运行（使用 nohup）
nohup .venv/bin/python -m src.server > logs/server.log 2>&1 &

# 5. 或使用 screen/tmux
screen -S code-sandbox
.venv/bin/python -m src.server
# Ctrl+A, D 退出会话
```

---

### LLM 平台配置

#### Claude Desktop

编辑 `claude_desktop_config.json`（位置：`~/Library/Application Support/Claude/` 或 `%APPDATA%\Claude\`）：

```json
{
  "mcpServers": {
    "code-sandbox": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/code-sandbox",
      "env": {
        "PYTHONPATH": "/path/to/code-sandbox"
      }
    }
  }
}
```

**远程服务器配置：**

```json
{
  "mcpServers": {
    "code-sandbox": {
      "command": "ssh",
      "args": [
        "-i", "/path/to/key",
        "user@server-ip",
        "PYTHONPATH=/opt/code-sandbox /opt/code-sandbox/.venv/bin/python -m src.server"
      ]
    }
  }
}
```

#### Cursor IDE

1. 打开 Cursor 设置
2. 进入 **MCP Servers** 标签
3. 点击 **Add Server**
4. 填写配置：
   - Name: `code-sandbox`
   - Type: `stdio`
   - Command: `python -m src.server`
   - Working Directory: `/path/to/code-sandbox`

#### Cline (VS Code 扩展)

在 Cline 设置中添加：

```json
{
  "mcpServers": [
    {
      "name": "code-sandbox",
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/code-sandbox"
    }
  ]
}
```

#### Windsurf

1. 打开 **Settings** → **MCP**
2. 点击 **Add MCP Server**
3. 选择 **Custom Server**
4. 配置：
   ```
   Name: code-sandbox
   Command: python -m src.server
   Directory: /path/to/code-sandbox
   ```

#### 远程 HTTP 部署（高级）

如需通过网络访问，使用 HTTP/SSE 模式：

```bash
# 修改 docker-compose.yml
environment:
  - MCP_TRANSPORT=http
  - MCP_PORT=8765
ports:
  - "8765:8765"

# 重启服务
docker-compose down
docker-compose up -d
```

客户端配置：

```json
{
  "mcpServers": {
    "code-sandbox": {
      "url": "http://server-ip:8765/sse",
      "transport": "sse"
    }
  }
}
```

---

### 安全配置

#### 防火墙配置

```bash
# 如果不需要网络访问，阻止外部连接
sudo ufw deny 8765

# 如果只允许特定 IP
sudo ufw allow from 192.168.1.0/24 to any port 8765
```

#### 权限配置

```bash
# 创建专用用户
sudo useradd -r -s /bin/false sandbox

# 设置目录权限
sudo chown -R sandbox:sandbox /opt/code-sandbox
sudo chmod -R 750 /opt/code-sandbox
```

#### 环境变量安全

```bash
# 创建 .env 文件（不要提交到版本控制）
cp .env.example .env

# 编辑敏感配置
vim .env
```

---

### 性能优化

#### 调整并发限制

```python
# server.py
import asyncio

# 设置信号量限制并发执行
semaphore = asyncio.Semaphore(10)  # 最多 10 个并发任务
```

#### 启用缓存

```bash
# 环境变量
export ENABLE_CACHE=true
export CACHE_MAX_SIZE=1000
export CACHE_TTL=3600
```

#### 资源限制

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

---

### 监控和日志

#### 日志配置

```python
# src/utils/logging.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler()
    ]
)
```

#### 健康检查端点

```bash
# 定期检查
curl http://localhost:8765/sse

# 或使用 docker
docker exec code-sandbox python -c "print('healthy')"
```

#### 性能监控

```bash
# 查看资源使用
docker stats code-sandbox

# 或使用 htop
htop -p $(pgrep -f "src.server")
```

---

### 诊断工具

#### 自动诊断脚本

```bash
# 运行完整诊断
./docker-diagnose.sh

# 输出包括:
# - 容器状态（Up/Restarting/healthy）
# - 配置检查（stdin_open, tty, PYTHONPATH）
# - 镜像检查
# - 日志分析
# - 功能测试
```

#### 快速诊断命令

```bash
# 检查容器状态
docker-compose ps

# 查看配置
docker-compose config

# 测试导入
docker exec code-sandbox-mcp python -c "from src.server import mcp; print('OK')"

# 运行验证
docker exec code-sandbox-mcp python /app/docker_verify.py
```

---

### 故障排查

#### Docker 部署问题排查

**问题 1: 包导入失败 (`ModuleNotFoundError`)**

```bash
# 检查 PYTHONPATH 是否正确
docker exec code-sandbox python -c "import sys; print(sys.path)"

# 应该包含 /app

# 解决方案：确保 docker-compose.yml 中设置了 PYTHONPATH
environment:
  - PYTHONPATH=/app
```

**问题 2: numpy/pandas 编译失败**

```bash
# 检查 Dockerfile 是否包含编译依赖
# 必须安装：build-essential, gfortran, libblas-dev, liblapack-dev

# 重新构建镜像
docker-compose build --no-cache
```

**问题 3: src 模块找不到**

```bash
# 检查容器内文件结构
docker exec code-sandbox ls -la /app/src/

# 应该看到：
# __init__.py  sandbox/  server.py

# 解决方案：确保 COPY 指令正确
COPY src/ ./src/
```

**问题 4: 权限错误**

```bash
# 检查文件所有者
docker exec code-sandbox ls -la /app/

# 应该是 sandbox 用户
# 解决方案：确保 Dockerfile 中在 COPY 后设置权限
RUN chown -R sandbox:sandbox /app
```

**问题 5: 验证容器环境**

```bash
# 运行验证脚本
docker-compose run --rm verify

# 或手动检查
docker exec code-sandbox python /app/docker_verify.py
```

#### 常见问题

**问题 1: 容器不断重启**

症状：`docker-compose ps` 显示 `Restarting` 状态

解决方案：
```yaml
# docker-compose.yml 确保包含
services:
  code-sandbox:
    stdin_open: true  # 必需 - 保持 stdin 打开
    tty: true         # 必需 - 分配伪终端
```

然后重启：
```bash
docker-compose down
docker-compose up -d
```

**其他问题：**

| 问题 | 解决方案 |
|------|----------|
| 连接失败 | 检查防火墙和端口 |
| 执行超时 | 增加 `SANDBOX_TIMEOUT` |
| 内存不足 | 调整 `MAX_MEMORY_MB` |
| 缓存命中率低 | 增加 `CACHE_MAX_SIZE` |
| Docker 包导入失败 | 检查 PYTHONPATH 和系统依赖 |

#### 查看日志

```bash
# Docker
docker logs -f code-sandbox

# Systemd
journalctl -u code-sandbox -f

# 直接运行
tail -f logs/server.log
```

#### 重启服务

```bash
# Docker
docker restart code-sandbox

# Systemd
sudo systemctl restart code-sandbox

# 直接运行
pkill -f "src.server"
nohup .venv/bin/python -m src.server > logs/server.log 2>&1 &
```

---

## 开发工具与协作

### 依赖管理

本项目使用 Python 标准依赖管理：

```bash
# 安装所有依赖（包含开发工具）
pip install -e ".[dev]"

# 核心依赖
- fastmcp>=0.1.0  # MCP 框架
- mcp>=1.0.0      # MCP 协议

# 开发依赖
- pytest>=7.0         # 测试框架
- pytest-asyncio>=0.21 # 异步测试支持
- pytest-mock>=3.10    # Mock 支持
- ruff>=0.1.0          # 代码检查和格式化
- mypy>=1.0            # 类型检查
- bandit>=1.7          # 安全扫描
```

### AI 辅助开发工具

本项目使用以下 AI 工具辅助开发：

#### 1. OpenCode / Cursor

**配置方式：**

在项目根目录创建 `.cursor/rules/` 或使用默认配置。

**推荐配置：**

```json
// .cursor/settings.json
{
  "mcpServers": {
    "code-sandbox": {
      "command": "docker",
      "args": ["exec", "-i", "code-sandbox-mcp", "python", "-m", "src.server"]
    }
  }
}
```

**使用场景：**
- 代码补全和建议
- 重构和优化
- 测试生成
- 文档编写

#### 2. LLM 协作开发

**推荐的 LLM 工作流：**

1. **代码审查**
   ```bash
   # 使用 LLM 审查代码变更
   git diff | llm-review
   ```

2. **测试生成**
   ```bash
   # 让 LLM 为函数生成测试
   llm "为 src/sandbox/security.py 生成 pytest 测试"
   ```

3. **文档更新**
   ```bash
   # 自动更新文档
   llm "根据代码变更更新 README.md"
   ```

4. **问题排查**
   ```bash
   # 使用 code-sandbox 测试代码
   docker exec code-sandbox-mcp python -c "你的代码"
   ```

#### 3. 推荐的 LLM 提示词

**代码优化：**
```
请优化这段代码，要求：
1. 保持类型安全
2. 遵循 PEP 8 规范
3. 添加必要的错误处理
4. 保持异步友好
```

**测试生成：**
```
请为这个函数编写 pytest 测试：
- 覆盖正常情况
- 覆盖边界情况
- 覆盖错误情况
- 使用异步测试
```

**代码审查：**
```
请审查这段代码：
- 检查类型安全
- 检查潜在的安全问题
- 检查性能问题
- 提出改进建议
```

### 开发最佳实践

#### 1. 类型安全

```python
# ✅ 推荐：完整的类型注解
async def execute(code: str, timeout: int = 30) -> ExecutionResult:
    ...

# ❌ 避免：缺少类型注解
async def execute(code, timeout=30):
    ...
```

#### 2. 错误处理

```python
# ✅ 推荐：明确的异常处理
try:
    result = await engine.execute(code)
except TimeoutError as e:
    raise SandboxExecutionError("超时") from e

# ❌ 避免：裸 except
try:
    result = await engine.execute(code)
except:
    pass
```

#### 3. 异步编程

```python
# ✅ 推荐：使用 asyncio.gather 并发
results = await asyncio.gather(
    task1(),
    task2(),
    task3()
)

# ❌ 避免：顺序执行
result1 = await task1()
result2 = await task2()
result3 = await task3()
```

#### 4. 测试覆盖

```bash
# 运行所有测试
pytest

# 查看覆盖率
pytest --cov=src --cov-report=html

# 运行单个测试
pytest tests/test_engine.py::TestBasicExecution::test_print_statement
```

### 持续集成

**推荐的 CI/CD 流程：**

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest
      - name: Lint
        run: ruff check src/
      - name: Type check
        run: mypy src/
```

### 性能优化建议

1. **使用缓存**
   ```bash
   # 启用执行缓存
   ENABLE_CACHE=true
   CACHE_MAX_SIZE=1000
   ```

2. **调整并发**
   ```python
   # 限制并发执行数
   semaphore = asyncio.Semaphore(10)
   ```

3. **监控资源**
   ```bash
   # 查看容器资源使用
   docker stats code-sandbox-mcp
   ```

---

## 许可证

MIT License
