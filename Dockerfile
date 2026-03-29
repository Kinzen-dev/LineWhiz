# ============================================
# LineWhiz MCP Server — Dockerfile
# ============================================
# Multi-stage build: Python 3.11 + uv
# Deploy target: Railway.app (SSE transport)
# ============================================

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies (production only)
RUN uv sync --no-dev --no-editable

# ─── Production stage ────────────────────────────────────────────────────────

FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LINEWHIZ_TRANSPORT=sse \
    LINEWHIZ_DATABASE_URL=sqlite:///data/linewhiz.db

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages and project from build stage
COPY --from=base /app /app

# Create non-root user + data directory
RUN useradd --create-home --shell /bin/bash linewhiz \
    && mkdir -p /app/data \
    && chown -R linewhiz:linewhiz /app/data

USER linewhiz

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "linewhiz"]
