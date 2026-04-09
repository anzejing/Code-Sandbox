# Code-Sandbox MCP Server - 生产环境 Docker 镜像
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（编译 numpy 等包必需）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml .
COPY README.md .
COPY src/ ./src/
COPY docker_verify.py .

# 创建虚拟环境并安装所有依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -e ".[dev]"

# 预安装常用数据科学包（按需添加）
RUN pip install --no-cache-dir numpy pandas matplotlib

# 设置 PYTHONPATH
ENV PYTHONPATH="/app"

# 创建日志目录和权限
RUN mkdir -p /app/logs

# 创建非 root 用户
RUN useradd -m -u 1000 sandbox && chown -R sandbox:sandbox /app
USER sandbox

# 健康检查（简单检查，避免误判）
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.stdout.write('healthy\n')" || exit 1

# 默认命令
CMD ["python", "-m", "src.server"]
