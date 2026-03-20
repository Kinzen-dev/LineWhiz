# LineWhiz — Deployment Guide

**Version**: 1.0
**Last Updated**: March 2026

This guide covers every step to deploy LineWhiz from a local development setup through production hosting.

---

## Prerequisites

Before starting, ensure you have the following accounts and tools ready.

### Accounts Required

1. **LINE Developers Console** — https://developers.line.biz/
   - Create a Provider and a Messaging API Channel
   - Note your **Channel Access Token** and **Channel Secret**
   - Ensure your LINE OA has the Messaging API enabled

2. **GitHub** — Private repo for the LineWhiz codebase

3. **Hosting Platform** (choose one):
   - Railway.app (recommended for MVP)
   - Fly.io
   - Docker-compatible VPS

4. **Stripe** (optional, for billing in v1.1+)

### Local Tools Required

- Python 3.11+
- `uv` (Python package manager) — install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker + Docker Compose
- Git

---

## Step 1: Local Development Setup

### 1.1 Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/linewhiz.git
cd linewhiz
uv sync
```

### 1.2 Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# LINE API credentials (from LINE Developers Console)
LINE_CHANNEL_ACCESS_TOKEN=your_long_lived_token_here
LINE_CHANNEL_SECRET=your_channel_secret_here

# LineWhiz configuration
LINEWHIZ_TIER=pro                              # MVP: hardcoded tier (free/pro/business)
LINEWHIZ_DATABASE_URL=sqlite:///linewhiz.db    # Local SQLite database
LINEWHIZ_LOG_LEVEL=INFO                        # DEBUG for development
```

### 1.3 Initialize Database

```bash
# The database auto-initializes on first run.
# To manually create it from the schema:
sqlite3 linewhiz.db < docs/DATABASE-SCHEMA.sql
```

### 1.4 Run Locally

```bash
# Run the MCP server
uv run server.py

# Or test with MCP Inspector
mcp dev server.py
```

### 1.5 Run Tests

```bash
uv run pytest
uv run mypy src/ --strict
uv run ruff check .
```

---

## Step 2: Configure MCP Client

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "linewhiz": {
      "command": "uv",
      "args": ["run", "server.py"],
      "cwd": "/path/to/linewhiz",
      "env": {
        "LINE_CHANNEL_ACCESS_TOKEN": "your_token_here",
        "LINE_CHANNEL_SECRET": "your_secret_here",
        "LINEWHIZ_TIER": "pro"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

### Cursor

Add to Cursor's MCP configuration (Settings > MCP Servers):

```json
{
  "linewhiz": {
    "command": "uv",
    "args": ["run", "server.py"],
    "cwd": "/path/to/linewhiz",
    "env": {
      "LINE_CHANNEL_ACCESS_TOKEN": "your_token_here",
      "LINE_CHANNEL_SECRET": "your_secret_here"
    }
  }
}
```

### Via PyPI (after publishing)

```json
{
  "mcpServers": {
    "linewhiz": {
      "command": "uvx",
      "args": ["linewhiz"],
      "env": {
        "LINE_CHANNEL_ACCESS_TOKEN": "your_token_here",
        "LINE_CHANNEL_SECRET": "your_secret_here"
      }
    }
  }
}
```

---

## Step 3: Dockerize

### 3.1 Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (cache layer)
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Entry point
CMD ["uv", "run", "server.py"]
```

### 3.2 Create docker-compose.yml

```yaml
version: "3.8"

services:
  linewhiz:
    build: .
    container_name: linewhiz-server
    restart: unless-stopped
    environment:
      - LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN}
      - LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET}
      - LINEWHIZ_TIER=${LINEWHIZ_TIER:-pro}
      - LINEWHIZ_DATABASE_URL=sqlite:///data/linewhiz.db
      - LINEWHIZ_LOG_LEVEL=${LINEWHIZ_LOG_LEVEL:-INFO}
    volumes:
      - linewhiz-data:/app/data
    ports:
      - "8000:8000"   # Only needed for HTTP/SSE transport (v1.1+)

volumes:
  linewhiz-data:
```

### 3.3 Build and Test Locally

```bash
docker compose build
docker compose up -d
docker compose logs -f linewhiz
```

---

## Step 4: Deploy to Railway.app (Recommended)

Railway provides the simplest deployment path with automatic Docker builds.

### 4.1 Connect Repository

1. Go to https://railway.app and sign in with GitHub
2. Click "New Project" > "Deploy from GitHub Repo"
3. Select your `linewhiz` repository
4. Railway auto-detects the Dockerfile

### 4.2 Set Environment Variables

In the Railway dashboard, go to your service > Variables:

```
LINE_CHANNEL_ACCESS_TOKEN = your_token_here
LINE_CHANNEL_SECRET = your_secret_here
LINEWHIZ_TIER = pro
LINEWHIZ_DATABASE_URL = sqlite:///data/linewhiz.db
LINEWHIZ_LOG_LEVEL = INFO
```

### 4.3 Configure Persistent Storage

1. In Railway dashboard, click "Add Volume"
2. Mount path: `/app/data`
3. This persists the SQLite database across deployments

### 4.4 Set Up Custom Domain (Optional)

1. Go to Settings > Networking
2. Click "Generate Domain" for a `*.up.railway.app` URL
3. Or add a custom domain (e.g., `api.linewhiz.dev`)

### 4.5 Deploy

Railway auto-deploys on every push to `main`. To trigger manually:

```bash
# Push to deploy
git push origin main
```

Monitor deployment in the Railway dashboard under "Deployments".

### 4.6 Verify Deployment

```bash
# Check health (HTTP/SSE transport, v1.1+)
curl https://your-app.up.railway.app/health

# Check logs in Railway dashboard
```

**Estimated Cost**: $5–10/month (Railway Hobby plan, usage-based)

---

## Step 5: Deploy to Fly.io (Alternative)

### 5.1 Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

### 5.2 Create fly.toml

```toml
app = "linewhiz"
primary_region = "nrt"  # Tokyo (closest to LINE's servers)

[build]
  dockerfile = "Dockerfile"

[env]
  LINEWHIZ_LOG_LEVEL = "INFO"
  LINEWHIZ_DATABASE_URL = "sqlite:///data/linewhiz.db"

[mounts]
  source = "linewhiz_data"
  destination = "/app/data"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.http_checks]]
    interval = 30000
    timeout = 5000
    path = "/health"
```

### 5.3 Set Secrets

```bash
fly secrets set LINE_CHANNEL_ACCESS_TOKEN="your_token_here"
fly secrets set LINE_CHANNEL_SECRET="your_secret_here"
fly secrets set LINEWHIZ_TIER="pro"
```

### 5.4 Create Volume and Deploy

```bash
fly volumes create linewhiz_data --region nrt --size 1
fly deploy
```

### 5.5 Verify

```bash
fly status
fly logs
```

**Estimated Cost**: $5–15/month (Fly.io pay-as-you-go)

---

## Step 6: Publish to Package Registries

### 6.1 Publish to PyPI

```bash
# Build the package
uv build

# Upload to PyPI (requires PyPI API token)
uv publish --token YOUR_PYPI_TOKEN
```

Users can then install with:
```bash
uvx linewhiz
# or
pip install linewhiz
```

### 6.2 Publish to npm (TypeScript port, future)

```bash
npm publish
```

Users install with:
```bash
npx linewhiz
```

---

## Step 7: List on MCP Marketplaces

### 7.1 Apify Store

1. Go to https://apify.com/mcp/developers
2. Submit your MCP server listing
3. Configure pay-per-event pricing model
4. Apify handles billing (takes 15–25% commission)

### 7.2 MCPize

1. Go to https://mcpize.com/developers
2. Submit listing with subscription pricing tiers
3. MCPize handles user management (85% revenue share)

### 7.3 MCP.so

1. Submit at https://mcp.so
2. Free listing for visibility (18K+ servers indexed)
3. Drives organic discovery

### 7.4 LobeHub

1. Submit at https://lobehub.com/mcp
2. Growing community marketplace

---

## Step 8: HTTP/SSE Remote Transport (v1.1+)

For remote hosting, add HTTP/SSE transport alongside STDIO.

### 8.1 Add HTTP Server

The server needs an additional HTTP endpoint for remote MCP connections:

```python
# In server.py, add HTTP/SSE transport option
import os

TRANSPORT = os.environ.get("LINEWHIZ_TRANSPORT", "stdio")

async def main():
    if TRANSPORT == "http":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route
        import uvicorn

        sse = SseServerTransport("/messages")
        app = Starlette(routes=[
            Route("/sse", endpoint=sse.handle_sse),
            Route("/messages", endpoint=sse.handle_messages, methods=["POST"]),
            Route("/health", endpoint=lambda r: JSONResponse({"status": "ok"})),
        ])
        uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
    else:
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
```

### 8.2 Remote Client Configuration

Users connect to the remote server via URL:

```json
{
  "mcpServers": {
    "linewhiz": {
      "type": "url",
      "url": "https://linewhiz.up.railway.app/sse",
      "headers": {
        "Authorization": "Bearer YOUR_LINEWHIZ_API_KEY",
        "X-Line-Token": "YOUR_LINE_CHANNEL_ACCESS_TOKEN"
      }
    }
  }
}
```

---

## Step 9: Monitoring and Operations

### 9.1 Logging

All logs go to stderr (never stdout, which would break STDIO transport):

```python
import sys, logging

logging.basicConfig(
    stream=sys.stderr,
    level=os.environ.get("LINEWHIZ_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

### 9.2 Health Monitoring

Set up uptime monitoring with one of these free services:
- UptimeRobot (https://uptimerobot.com) — free 5-min checks
- Better Uptime (https://betteruptime.com) — free tier
- Fly.io / Railway built-in health checks

### 9.3 Error Alerting

For production, add error alerting:
- Sentry (https://sentry.io) — free tier for error tracking
- Railway/Fly.io dashboard alerts

### 9.4 Database Backups

For SQLite on persistent volumes:

```bash
# Manual backup (run periodically or via cron)
sqlite3 /app/data/linewhiz.db ".backup /app/data/backup-$(date +%Y%m%d).db"
```

For automated backups, consider Litestream (https://litestream.io) for continuous SQLite replication to S3.

---

## Step 10: Security Checklist

Before going live, verify each item:

- [ ] LINE tokens stored as environment variables only (never in code or DB)
- [ ] API keys stored as SHA-256 hashes in database
- [ ] Full API keys are never logged (only first 8 chars for debugging)
- [ ] All tool inputs validated with Pydantic before hitting LINE API
- [ ] HTTPS enforced for all remote transport
- [ ] Rate limiting active for all tiers
- [ ] Error messages never expose raw LINE API error bodies
- [ ] Docker runs as non-root user
- [ ] `.env` file is in `.gitignore`
- [ ] No secrets committed to Git history

---

## Cost Summary

| Item | MVP Cost | Scaled Cost |
|------|----------|-------------|
| Railway.app hosting | $5–10/mo | $10–20/mo |
| Domain (linewhiz.dev) | $12/year | $12/year |
| SQLite database | $0 (included) | — |
| PostgreSQL (future) | — | $15–30/mo |
| Sentry error tracking | $0 (free tier) | $26/mo |
| Uptime monitoring | $0 (free tier) | $0 |
| **Total** | **~$6–11/mo** | **~$30–60/mo** |

Target: keep hosting under $20/month until revenue covers it.

---

## Troubleshooting

### MCP server not showing in Claude Desktop

1. Verify the config file path is correct
2. Ensure the `command` and `cwd` paths are absolute
3. Restart Claude Desktop completely (quit and reopen)
4. Check server logs: `uv run server.py 2>&1`

### LINE API returning 401

1. Verify `LINE_CHANNEL_ACCESS_TOKEN` is set and valid
2. Token may have expired — generate a new long-lived token in LINE Developers Console
3. Ensure the Messaging API channel is active

### Database locked errors

1. SQLite can only handle one writer at a time
2. Enable WAL mode: `PRAGMA journal_mode = WAL;`
3. If persistent, consider migrating to PostgreSQL

### Railway deployment fails

1. Check build logs in Railway dashboard
2. Ensure `Dockerfile` is in the repo root
3. Verify all env vars are set in Railway Variables panel
4. Check that `pyproject.toml` lists all dependencies

### Rate limit exceeded

1. Check `LINEWHIZ_TIER` environment variable
2. Free tier: 100 calls/day, Pro: 5,000, Business: unlimited
3. Limits reset at midnight UTC
4. LINE API has its own rate limits (see API-SPEC.md)

---

*Document created: March 2026*
*Source of truth: CLAUDE.md, architecture.md, linewhiz-spec.md*
