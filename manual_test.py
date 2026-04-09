#!/usr/bin/env python
"""手动测试脚本 - 演示 Code-Sandbox 各项功能."""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import Context
from src.server import (
    mcp,
    execute_python,
    analyze_data,
    check_security,
    store_plot,
    get_plot,
)
from src.sandbox.cache import get_execution_cache


async def test_basic_execution():
    """测试基础代码执行."""
    print("\n" + "=" * 60)
    print("测试 1: 基础代码执行")
    print("=" * 60)

    ctx = Context(fastmcp=mcp)
    result = await execute_python(ctx, 'print("Hello from Code-Sandbox!")')
    print(result)


async def test_multiline_code():
    """测试多行代码执行."""
    print("\n" + "=" * 60)
    print("测试 2: 多行代码执行")
    print("=" * 60)

    ctx = Context(fastmcp=mcp)
    code = """
import math

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 打印前 10 个斐波那契数
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
"""
    result = await execute_python(ctx, code)
    print(result)


async def test_security_check():
    """测试安全检查."""
    print("\n" + "=" * 60)
    print("测试 3: 安全检查")
    print("=" * 60)

    ctx = Context(fastmcp=mcp)

    # 安全代码
    print("\n【安全代码测试】")
    result = await check_security(ctx, "import math; print(math.sqrt(16))")
    print(result)

    # 危险代码
    print("\n【危险代码测试】")
    result = await check_security(ctx, "import os; os.system('ls')")
    print(result)


async def test_timeout():
    """测试超时控制."""
    print("\n" + "=" * 60)
    print("测试 4: 超时控制")
    print("=" * 60)

    ctx = Context(fastmcp=mcp)

    # 快速代码
    print("\n【快速代码】")
    result = await execute_python(ctx, 'print("fast")', timeout=5)
    print(result)

    # 超时代码
    print("\n【超时代码】")
    result = await execute_python(ctx, "import time; time.sleep(10)", timeout=2)
    print(result)


async def test_error_handling():
    """测试错误处理."""
    print("\n" + "=" * 60)
    print("测试 5: 错误处理")
    print("=" * 60)

    ctx = Context(fastmcp=mcp)

    # 语法错误
    print("\n【语法错误】")
    result = await execute_python(ctx, 'print("unclosed')
    print(result)

    # 运行时错误
    print("\n【运行时错误】")
    result = await execute_python(ctx, "print(1 / 0)")
    print(result)


async def test_caching():
    """测试缓存功能."""
    print("\n" + "=" * 60)
    print("测试 6: 缓存功能")
    print("=" * 60)

    from src.sandbox.engine import ExecutionEngine
    from src.sandbox.types import SandboxConfig

    engine = ExecutionEngine(SandboxConfig(timeout_seconds=5), use_cache=True)

    code = 'print("cached result")'

    # 第一次执行（缓存未命中）
    print("\n【第一次执行 - 缓存未命中】")
    result1 = await engine.execute(code, use_cache=True)
    print(result1)

    # 第二次执行（缓存命中）
    print("\n【第二次执行 - 缓存命中】")
    result2 = await engine.execute(code, use_cache=True)
    print(result2)

    # 查看缓存统计
    cache = get_execution_cache()
    stats = cache.get_stats()
    print(f"\n【缓存统计】{stats}")


async def test_plot_storage():
    """测试图片存储."""
    print("\n" + "=" * 60)
    print("测试 7: 图片存储")
    print("=" * 60)

    import base64

    ctx = Context(fastmcp=mcp)

    # 创建假图片数据
    image_bytes = b"\x89PNG\r\n\x1a\n" + b"fake_image_data"
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # 存储图片
    print("\n【存储图片】")
    result = await store_plot(ctx, image_base64)
    print(result)

    # 提取 plot ID
    plot_id = result.split("plot://")[1].strip()
    print(f"Plot ID: {plot_id}")

    # 检索图片
    print("\n【检索图片】")
    retrieved_bytes, mime_type = await get_plot(plot_id)
    print(f"MIME 类型：{mime_type}")
    print(f"图片大小：{len(retrieved_bytes)} bytes")
    print(f"数据匹配：{retrieved_bytes == image_bytes}")


async def test_concurrent_execution():
    """测试并发执行."""
    print("\n" + "=" * 60)
    print("测试 8: 并发执行")
    print("=" * 60)

    import time
    from src.sandbox.engine import ExecutionEngine

    engine = ExecutionEngine()

    async def run_task(task_id: int):
        start = time.perf_counter()
        result = await engine.execute(f'print("Task {task_id}")')
        elapsed = time.perf_counter() - start
        return task_id, elapsed

    # 并发执行 5 个任务
    print("\n【并发执行 5 个任务】")
    start = time.perf_counter()
    results = await asyncio.gather(*[run_task(i) for i in range(5)])
    total_time = time.perf_counter() - start

    for task_id, elapsed in results:
        print(f"任务 {task_id}: {elapsed * 1000:.2f}ms")

    print(f"\n总耗时：{total_time * 1000:.2f}ms")


async def main():
    """运行所有测试."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "Code-Sandbox 手动测试" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")

    tests = [
        test_basic_execution,
        test_multiline_code,
        test_security_check,
        test_timeout,
        test_error_handling,
        test_caching,
        test_plot_storage,
        test_concurrent_execution,
    ]

    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"\n❌ 测试失败：{e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
