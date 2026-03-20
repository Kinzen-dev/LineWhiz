# ============================================
# LineWhiz MCP Server — Dockerfile
# ============================================
# Multi-stage build: Python 3.11 + uv
# Deploy target: Railway.app
# ============================================

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --no-dev --no-editable

# ─── Production stage ────────────────────────────────────────────────────────

FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed packages and project from build stage
COPY --from=base /app /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash linewhiz
USER linewhiz

# Default command — run MCP server via STDIO
CMD ["uv", "run", "python", "-m", "src.server"]
