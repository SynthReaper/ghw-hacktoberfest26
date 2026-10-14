# syntax=docker/dockerfile:1
# Multi-stage production Dockerfile for Open-Switch

# Stage 1: Build & Dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY openswitch ./openswitch

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install .

# Stage 2: Minimal Production Runtime
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    OPENSWITCH_MODE=hosted \
    DEMO_MODE=true \
    DATA_DIR=/var/data \
    DATABASE_URL=sqlite+aiosqlite:////var/data/openswitch.db

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create persistent storage dir and non-root app user
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -s /bin/bash appuser && \
    mkdir -p /var/data /app/data && \
    chown -R appuser:appgroup /var/data /app

# Copy installed dependencies and package from builder
COPY --from=builder /install /usr/local

# Copy application files
COPY --chown=appuser:appgroup specs ./specs
COPY --chown=appuser:appgroup templates ./templates
COPY --chown=appuser:appgroup data ./data
COPY --chown=appuser:appgroup openswitch ./openswitch
COPY --chown=appuser:appgroup pyproject.toml README.md ./

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn openswitch.web.app:app --host 0.0.0.0 --port ${PORT}"]
