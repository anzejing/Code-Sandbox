#!/usr/bin/env python
"""Inspector 使用指南 - 测试 Code-Sandbox 功能."""

print("""
╔════════════════════════════════════════════════════════════════╗
║           MCP Inspector 使用指南                               ║
╚════════════════════════════════════════════════════════════════╝

📍 访问地址:
   http://localhost:6274

🔑 认证 Token:
   576602ab34c5bec35e1b59a57dfb43c921411fcd1b23dbba417227b46aa58d3b

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Inspector 界面测试步骤:

1. 【连接服务器】
   - 点击 "Connect" 或 "Add Server"
   - 选择 "stdio" 传输方式
   - 配置命令:
     Command: /data/1files/python-sandbox/.venv/bin/python
     Args: -m src.server
     Working Dir: /data/1files/python-sandbox

2. 【查看工具列表】
   - 连接成功后，点击 "Tools" 标签
   - 应该看到 5 个工具:
     ✓ execute_python
     ✓ analyze_data
     ✓ check_security
     ✓ store_plot
     ✓ get_plot

3. 【测试 execute_python】
   - 点击 "execute_python"
   - 输入参数:
     {
       "code": "print('Hello from Inspector!')",
       "timeout": 30
     }
   - 点击 "Run"
   - 查看返回结果

4. 【测试 check_security】
   - 点击 "check_security"
   - 输入参数:
     {
       "code": "import os"
     }
   - 点击 "Run"
   - 应该看到安全警告

5. 【测试 store_plot】
   - 点击 "store_plot"
   - 输入参数:
     {
       "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
       "mime_type": "image/png"
     }
   - 点击 "Run"
   - 返回 plot://<id>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧪 或者使用命令行快速测试:

# 测试 1: 基础执行
.venv/bin/python quick_test.py 'print("测试成功!")'

# 测试 2: 安全检查
.venv/bin/python quick_test.py 'import os'

# 测试 3: 完整演示
.venv/bin/python manual_test.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Inspector 界面说明:

┌────────────────────────────────────────────────────────────┐
│  Tools                  │  Resources         │  Logs       │
├────────────────────────────────────────────────────────────┤
│  - execute_python       │  - plot://{id}     │  实时日志   │
│  - analyze_data         │                    │  输出       │
│  - check_security       │                    │             │
│  - store_plot           │                    │             │
│  - get_plot             │                    │             │
└────────────────────────────────────────────────────────────┘

- Tools: 点击工具 → 输入 JSON 参数 → Run → 查看结果
- Resources: 通过 URI 访问资源 (如 plot://xxx)
- Logs: 查看服务器实时日志输出

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

按任意键继续测试...
""")

input()

# 运行快速测试
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import Context
from src.server import execute_python, check_security, mcp


async def interactive_test():
    """交互式测试."""
    ctx = Context(fastmcp=mcp)

    print("\n" + "=" * 60)
    print("测试 1: 执行 Python 代码")
    print("=" * 60)
    result = await execute_python(ctx, 'print("Hello from Code-Sandbox!")')
    print(result)

    print("\n" + "=" * 60)
    print("测试 2: 安全检查 (安全代码)")
    print("=" * 60)
    result = await check_security(ctx, "import math; print(math.sqrt(16))")
    print(result)

    print("\n" + "=" * 60)
    print("测试 3: 安全检查 (危险代码)")
    print("=" * 60)
    result = await check_security(ctx, "import os")
    print(result)

    print("\n" + "=" * 60)
    print("测试 4: 多行代码执行")
    print("=" * 60)
    code = """
for i in range(5):
    print(f"计数：{i + 1}")
print("完成!")
"""
    result = await execute_python(ctx, code)
    print(result)

    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    print("""
现在你可以:
1. 在 Inspector 网页中手动测试上述功能
2. 尝试其他代码
3. 查看 Logs 标签页的实时输出
""")


asyncio.run(interactive_test())
