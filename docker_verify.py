# Docker 部署验证脚本
#!/usr/bin/env python
"""验证 Docker 环境中的包导入是否正常."""

import sys


def check_imports():
    """检查关键包导入."""
    packages = [
        ("Python 版本", "sys", lambda m: sys.version.split()[0]),
        ("FastMCP", "fastmcp", lambda m: m.__version__),
        ("MCP", "mcp", lambda m: "OK"),
        ("src.sandbox", "src.sandbox", lambda m: m.__version__),
        ("src.server", "src.server", lambda m: "OK"),
    ]

    print("=" * 60)
    print("Docker 环境包导入验证")
    print("=" * 60)

    all_ok = True
    for name, module_path, get_version in packages:
        try:
            module = __import__(module_path)
            result = get_version(module)
            if result == "OK":
                print(f"✓ {name}: OK")
            else:
                print(f"✓ {name}: {result}")
        except ImportError as e:
            print(f"✗ {name}: FAILED - {e}")
            all_ok = False
        except Exception as e:
            print(f"✗ {name}: ERROR - {e}")
            all_ok = False

    print("=" * 60)
    print(f"PYTHONPATH: {sys.path[:3]}...")  # 只显示前 3 个

    # 测试实际执行
    print("\n" + "=" * 60)
    print("执行测试")
    print("=" * 60)

    try:
        from src.sandbox.engine import ExecutionEngine
        from src.sandbox.types import SandboxConfig
        import asyncio

        async def test():
            engine = ExecutionEngine(SandboxConfig(timeout_seconds=5))
            result = await engine.execute('print("Docker 测试成功!")')
            return result

        result = asyncio.run(test())
        print(f"✓ 执行测试：{result.status.value}")
        print(f"  stdout: {result.stdout.strip()}")

    except Exception as e:
        print(f"✗ 执行测试：FAILED - {e}")
        all_ok = False

    print("=" * 60)
    return all_ok


if __name__ == "__main__":
    success = check_imports()
    sys.exit(0 if success else 1)
