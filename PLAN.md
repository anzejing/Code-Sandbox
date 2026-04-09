# Code-Sandbox 开发计划

## 项目目标
构建基于 FastMCP 的 Python 执行沙箱服务，为 AI 提供安全、类型安全、带依赖管理的代码执行环境。

---

## 项目结构

```
python-sandbox/
├── pyproject.toml              # 项目配置 + 依赖声明
├── AGENTS.md                   # 开发者指南
├── PLAN.md                     # 本计划文件
├── README.md                   # 项目说明
├── tests/
│   ├── __init__.py
│   ├── test_security.py        # 安全扫描测试
│   ├── test_engine.py          # 执行引擎测试
│   └── test_server.py          # MCP 工具测试
└── src/
    ├── __init__.py
    ├── server.py               # FastMCP 入口 + 工具注册
    ├── sandbox/
    │   ├── __init__.py
    │   ├── types.py            # 数据类型定义
    │   ├── security.py         # 安全验证层
    │   └── engine.py           # 核心执行引擎
    └── utils/
        ├── __init__.py
        └── logging.py          # 日志配置
```

---

## 开发阶段

### Phase 1: 基础框架 (P0 - 必须) ✅ 完成

| 序号 | 任务 | 文件 | 预计行数 | 依赖 | 状态 |
|------|------|------|----------|------|------|
| 1.1 | 项目初始化 | `pyproject.toml` | 40 | - | ✅ |
| 1.2 | 类型定义 | `src/sandbox/types.py` | 50 | - | ✅ |
| 1.3 | 安全扫描 | `src/sandbox/security.py` | 80 | types.py | ✅ |
| 1.4 | 执行引擎 | `src/sandbox/engine.py` | 120 | types.py, security.py | ✅ |
| 1.5 | MCP 注册 | `src/server.py` | 80 | engine.py | ✅ |
| 1.6 | 基础测试 | `tests/test_*.py` | 150 | 以上全部 | ✅ |

**交付物**: 可执行的基础沙箱，支持代码执行 + 超时 + 导入拦截

**验证结果**:
- ✅ 34 个测试全部通过
- ✅ ruff lint 检查通过
- ✅ mypy 类型检查通过
- ✅ 服务器可启动

---

### Phase 2: 增强功能 (P1 - 重要) ✅ 完成

| 序号 | 任务 | 文件 | 预计行数 | 依赖 | 状态 |
|------|------|------|----------|------|------|
| 2.1 | 进度汇报 | `src/server.py` (增强) | +30 | Phase 1 | ✅ |
| 2.2 | 依赖管理 | `src/server.py` (增强) | +20 | Phase 1 | ✅ |
| 2.3 | 图片资源 | `src/server.py` + `src/sandbox/plots.py` | 60 | Phase 1 | ✅ |
| 2.4 | 日志系统 | `src/utils/logging.py` | 40 | - | ✅ |
| 2.5 | 集成测试 | `tests/test_plots.py` + `tests/test_server.py` | 100 | Phase 2 | ✅ |

**交付物**: 完整功能沙箱，支持进度/依赖/图片

**验证结果**:
- ✅ 46 个测试全部通过
- ✅ ruff lint 检查通过
- ✅ mypy 类型检查通过
- ✅ 新增 plot 缓存和资源处理功能

---

### Phase 3: 完善优化 (P2 - 可选) ✅ 完成

| 序号 | 任务 | 文件 | 预计行数 | 依赖 | 状态 |
|------|------|------|----------|------|------|
| 3.1 | 内存限制 | `src/sandbox/engine.py` (增强) | +40 | Phase 1 | ✅ |
| 3.2 | 缓存机制 | `src/sandbox/cache.py` | 80 | Phase 1 | ✅ |
| 3.3 | 性能测试 | `tests/test_benchmark.py` + `tests/test_cache.py` | 150 | Phase 2 | ✅ |
| 3.4 | 文档完善 | `README.md` (更新) | - | Phase 2 | ✅ |

**交付物**: 生产就绪沙箱，支持缓存/性能基准/完整文档

**验证结果**:
- ✅ 63 个测试全部通过
- ✅ ruff lint 检查通过
- ✅ mypy 类型检查通过
- ✅ 新增执行缓存和性能基准测试

## 详细实现规范

### 1.1 pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "code-sandbox-mcp"
version = "0.1.0"
description = "FastMCP-based Python execution sandbox"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=0.1.0",
    "mcp>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-mock>=3.10",
    "ruff>=0.1.0",
    "mypy>=1.0",
    "bandit>=1.7",
]

[tool.setuptools.packages.find]
where = ["src"]
```

### 1.2 types.py 接口定义
```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

class ExecutionStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SECURITY_VIOLATION = "security_violation"

@dataclass
class ExecutionResult:
    status: ExecutionStatus
    stdout: str
    stderr: str
    returncode: Optional[int]
    execution_time_ms: float
    error_message: Optional[str] = None

@dataclass
class SandboxConfig:
    timeout_seconds: int = 30
    max_memory_mb: int = 512
    allowed_modules: List[str] = field(default_factory=list)
    blocked_modules: List[str] = field(default_factory=lambda: [
        "os", "subprocess", "sys", "builtins", "ctypes"
    ])

@dataclass
class PlotResource:
    id: str
    image_bytes: bytes
    mime_type: str = "image/png"
    created_at: float = field(default_factory=time.time)
```

### 1.3 security.py 接口定义
```python
import ast
from typing import List, Set
from .types import SandboxConfig

class SecurityScanner:
    def __init__(self, config: SandboxConfig):
        self.config = config
        self._blocked = set(config.blocked_modules)
        self._allowed = set(config.allowed_modules) if config.allowed_modules else None
    
    def scan_imports(self, code: str) -> List[str]:
        """返回违规导入列表"""
        ...
    
    def scan_dangerous_calls(self, code: str) -> List[str]:
        """返回危险函数调用列表 (eval, exec, compile)"""
        ...
    
    def validate(self, code: str) -> None:
        """验证代码，抛出 SandboxSecurityError"""
        ...

class SandboxSecurityError(Exception):
    def __init__(self, message: str, violations: List[str]):
        self.violations = violations
        super().__init__(message)
```

### 1.4 engine.py 接口定义
```python
import asyncio
from .types import ExecutionResult, SandboxConfig
from .security import SecurityScanner

class ExecutionEngine:
    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()
        self.scanner = SecurityScanner(self.config)
    
    async def execute(self, code: str) -> ExecutionResult:
        """执行代码，返回 ExecutionResult"""
        # 1. 安全验证
        self.scanner.validate(code)
        
        # 2. 超时执行
        try:
            return await asyncio.wait_for(
                self._run(code),
                timeout=self.config.timeout_seconds
            )
        except asyncio.TimeoutError:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stdout="", stderr="", returncode=-1,
                execution_time_ms=self.config.timeout_seconds * 1000,
                error_message="Execution timeout"
            )
    
    async def _run(self, code: str) -> ExecutionResult:
        """实际执行逻辑 (subprocess)"""
        ...
```

### 1.5 server.py 接口定义
```python
from fastmcp import FastMCP, Context
from .sandbox.engine import ExecutionEngine
from .sandbox.types import ExecutionResult, SandboxConfig

mcp = FastMCP("Code-Sandbox")
engine = ExecutionEngine(SandboxConfig(timeout_seconds=30))

@mcp.tool()
async def execute_python(
    ctx: Context,
    code: str,
    timeout: int = 30
) -> str:
    """
    Execute Python code in isolated sandbox.
    
    Args:
        code: Python code to execute (multi-line supported)
        timeout: Maximum execution time in seconds (default: 30)
    
    Returns:
        Formatted string with stdout, stderr, and execution status
    
    Raises:
        SandboxSecurityError: If code contains blocked imports
    """
    await ctx.report_progress(0, 100, "Validating code...")
    
    engine.config.timeout_seconds = timeout
    result = await engine.execute(code)
    
    await ctx.report_progress(100, 100, "Complete")
    return _format_result(result)

@mcp.tool(dependencies=["numpy", "pandas", "matplotlib"])
async def analyze_data(ctx: Context, code: str) -> str:
    """Execute data analysis code with auto-installed dependencies."""
    return await execute_python(ctx, code)

@mcp.resource("plot://{id}")
async def get_plot(id: str) -> tuple[bytes, str]:
    """Return plot image by ID with MIME type."""
    # TODO: 实现图片缓存检索
    ...
```

---

## 测试计划

### 单元测试覆盖
| 模块 | 测试文件 | 关键用例 |
|------|----------|----------|
| security.py | test_security.py | 阻止 os/subprocess, 允许 numpy/pandas |
| engine.py | test_engine.py | 正常执行，超时，错误捕获 |
| server.py | test_server.py | 工具注册，进度汇报，依赖声明 |

### 安全测试用例
```python
# 必须阻止的导入
assert_blocked("import os")
assert_blocked("import subprocess")
assert_blocked("from sys import modules")
assert_blocked("import ctypes")

# 必须允许的导入
assert_allowed("import numpy as np")
assert_allowed("import pandas as pd")
assert_allowed("import matplotlib.pyplot as plt")

# 必须阻止的危险调用
assert_blocked("eval('1+1')")
assert_blocked("exec('print(1)')")
assert_blocked("__import__('os').system('ls')")
```

### 集成测试用例
```python
# 完整执行流程
async def test_full_execution():
    result = await execute_python(ctx, "print('hello')")
    assert "hello" in result

# 超时 enforcement
async def test_timeout():
    with pytest.raises(TimeoutError):
        await execute_python(ctx, "import time; time.sleep(60)", timeout=1)

# 依赖自动安装
async def test_numpy_available():
    result = await analyze_data(ctx, "import numpy; print(numpy.__version__)")
    assert result.returncode == 0
```

---

## 验收标准

### Phase 1 完成标志
- [ ] `python -m src.server` 可启动
- [ ] Inspector 可连接并显示工具列表
- [ ] `execute_python` 可执行简单代码
- [ ] 超时功能正常工作
- [ ] 危险导入被拦截
- [ ] 所有单元测试通过

### Phase 2 完成标志
- [ ] 进度汇报在 Inspector 可见
- [ ] `dependencies` 声明的库可自动使用
- [ ] 图片资源可通过 `plot://` URI 访问
- [ ] 日志输出结构化

### Phase 3 完成标志
- [ ] 内存限制生效
- [ ] 性能基准测试通过
- [ ] README 文档完整

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| FastMCP API 变更 | 高 | 锁定版本，关注更新日志 |
| subprocess 逃逸 | 严重 | 多层验证 + 最小权限原则 |
| 依赖安装失败 | 中 | 预安装常用库 + 错误提示 |
| 并发执行资源竞争 | 中 | 信号量限制 + 资源池 |

---

## 时间估算

| 阶段 | 开发 | 测试 | 调试 | 总计 |
|------|------|------|------|------|
| Phase 1 | 4h | 2h | 1h | 7h |
| Phase 2 | 3h | 2h | 1h | 6h |
| Phase 3 | 2h | 1h | 1h | 4h |
| **总计** | **9h** | **5h** | **3h** | **17h** |

---

## 下一步行动

1. 创建 `pyproject.toml`
2. 实现 `src/sandbox/types.py`
3. 实现 `src/sandbox/security.py`
4. 实现 `src/sandbox/engine.py`
5. 实现 `src/server.py`
6. 编写测试并验证

准备开始 Phase 1.1？
