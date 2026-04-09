#!/usr/bin/env python
"""快速测试单个功能."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import Context
from src.server import execute_python, mcp


async def quick_test(code: str):
    """快速执行代码并打印结果."""
    ctx = Context(fastmcp=mcp)
    result = await execute_python(ctx, code)
    print(result)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        code = " ".join(sys.argv[1:])
    else:
        code = 'print("Hello!")'

    asyncio.run(quick_test(code))
