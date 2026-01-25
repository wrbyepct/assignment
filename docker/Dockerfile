# ==================== Stage 1: Builder ====================
FROM python:3.12.6-slim-bookworm AS builder

# 安裝系統依賴（編譯 psycopg2 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# 設定工作目錄
WORKDIR /build

# 複製依賴定義檔
COPY pyproject.toml poetry.lock ./

# 安裝 Python 依賴到 /build/venv
RUN poetry config virtualenvs.in-project true && \
    poetry install --only main --no-root --no-interaction

# ==================== Stage 2: Runtime ====================
FROM python:3.12.6-slim-bookworm AS runtime

# 安裝執行時必要的系統套件（psycopg2 需要 libpq）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 建立 non-root user（安全性最佳實踐）
RUN groupadd -r django && useradd -r -g django django

# 設定工作目錄
WORKDIR /app

# 從 builder stage 複製虛擬環境
COPY --from=builder /build/.venv /app/.venv


# 複製專案程式碼
COPY core/ /app/core/
COPY run /app/run
COPY docker/start /app/start


# 確保 run 腳本可執行
RUN chmod +x /app/run /app/start

RUN chown -R django:django /app
USER django

# 設定 PATH（讓虛擬環境的 python 可用）
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Healthcheck（確認 Django 可以啟動）
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import django; django.setup()" || exit 1

# 預設執行指令（可被 docker-compose 或 ECS 覆寫）
ENTRYPOINT ["/app/start"]
