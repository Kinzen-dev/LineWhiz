# LineWhiz

> Premium MCP server that lets AI agents manage LINE Official Accounts.

Users type natural language in **Claude / ChatGPT / Cursor** → LineWhiz calls the LINE Messaging API.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-v1.2%2B-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

| Tool | Tier | Description |
|------|------|-------------|
| `get_account_info` | Free | Get LINE OA info: name, plan, picture |
| `get_friend_count` | Free | Get follower count on a specific date |
| `get_message_quota` | Free | Get remaining message quota this month |
| `send_broadcast` | Pro | Send message to ALL friends |
| `send_push_message` | Pro | Send DM to a specific user |
| `send_multicast` | Pro | Send message to multiple users (max 500) |
| `get_message_delivery_stats` | Pro | Get delivery stats for a date |
| `get_user_profile` | Pro | Get user's display name, picture, etc. |
| `list_rich_menus` | Pro | List all rich menus for this LINE OA |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- LINE Messaging API channel ([create one here](https://developers.line.biz/))

### Setup

```bash
# Clone and install
cd linewhiz && uv sync

# Configure environment
cp .env.example .env
# Edit .env → fill in LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET

# Run the server
uv run src/server.py

# Test with MCP Inspector
mcp dev src/server.py

# Run tests
uv run pytest
```

### MCP Client Configuration

Add to your MCP client config (e.g., Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "linewhiz": {
      "command": "uv",
      "args": ["run", "src/server.py"],
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

## Project Structure

```
linewhiz/
├── CLAUDE.md              # AI coding spec (single source of truth)
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── src/
│   ├── server.py          # MCP entry point + tool registration
│   ├── config.py          # Env config via pydantic Settings
│   ├── auth/
│   │   ├── api_keys.py    # Key validation (SHA-256)
│   │   └── tiers.py       # Free/Pro/Business gating + rate limits
│   ├── tools/
│   │   ├── account.py     # get_account_info, get_friend_count, get_message_quota
│   │   ├── messaging.py   # send_broadcast, send_push, send_multicast
│   │   ├── richmenu.py    # list/create/set/link rich menus
│   │   ├── insights.py    # get_message_stats, get_user_profile
│   │   ├── automation.py  # [future] auto-reply
│   │   └── reporting.py   # [future] weekly report
│   ├── services/
│   │   ├── line_api.py    # Async LINE API wrapper
│   │   └── flex_builder.py
│   ├── models/
│   │   ├── user.py        # API key + tier models
│   │   └── usage.py       # Usage log model
│   └── db/
│       └── database.py    # SQLite async init + migrations
├── tests/
│   ├── conftest.py
│   ├── test_account.py
│   ├── test_messaging.py
│   ├── test_richmenu.py
│   └── test_auth.py
└── docs/
```

## Tier System

| Tier | Price | Daily Calls | Tools |
|------|-------|-------------|-------|
| **Free** | $0/mo | 100 | Account info, friend count, quota |
| **Pro** | $15/mo | 5,000 | + Messaging, rich menus, insights |
| **Business** | $45/mo | Unlimited | All tools |

## Docker

```bash
# Build and run
docker compose up --build

# Or build manually
docker build -t linewhiz .
docker run --env-file .env linewhiz
```

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/

# Test
uv run pytest -v
```

## License

MIT
