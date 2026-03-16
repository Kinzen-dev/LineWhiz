# CLAUDE.md — LineWhiz Project Instructions

> This file tells AI coding agents (Claude Code, Antigravity, Cursor)
> how to work on this project. Read this FIRST before writing any code.

## Project Overview

**LineWhiz** is a premium MCP (Model Context Protocol) server that lets
AI agents (Claude, ChatGPT, Cursor, Antigravity) manage LINE Official
Accounts through natural language commands.

Users type things like "broadcast โปรโมชั่นวันแม่ให้ลูกค้าผู้หญิง" and
the AI handles everything — composing the message, targeting the right
audience, and sending via LINE's Messaging API.

## Tech Stack

- **Language**: Python 3.11+
- **MCP SDK**: `mcp` (official, v1.2+)
- **LINE SDK**: `line-bot-sdk` (official Python SDK)
- **HTTP client**: `httpx` (async)
- **Data validation**: `pydantic`
- **Database**: SQLite (MVP) via `aiosqlite`
- **Testing**: `pytest` + `pytest-asyncio`
- **Linting**: `ruff`
- **Type checking**: `mypy`
- **Packaging**: `uv` (for dependency management)
- **Deployment**: Docker → Railway.app

## Project Structure

```
linewhiz/
├── CLAUDE.md              ← you are here
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
├── src/
│   ├── __init__.py
│   ├── server.py          # MCP server entry point
│   ├── config.py          # Environment config loader
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── api_keys.py    # API key generation + validation
│   │   └── tiers.py       # Free/Pro/Business feature gating
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── account.py     # get_account_info, get_friend_count, get_message_quota
│   │   ├── messaging.py   # send_broadcast, send_push, send_multicast, send_narrowcast
│   │   ├── richmenu.py    # list/create/set/link rich menus
│   │   ├── insights.py    # get_message_stats, get_audience_insights
│   │   ├── automation.py  # setup_auto_reply, create_flex_message
│   │   └── reporting.py   # generate_weekly_report
│   ├── services/
│   │   ├── __init__.py
│   │   ├── line_api.py    # Async LINE API client wrapper
│   │   └── flex_builder.py # Flex Message JSON generator
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py        # User + Subscription pydantic models
│   │   └── usage.py       # Usage tracking models
│   └── db/
│       ├── __init__.py
│       └── database.py    # SQLite async connection + migrations
├── tests/
│   ├── conftest.py        # Shared fixtures
│   ├── test_account.py
│   ├── test_messaging.py
│   ├── test_richmenu.py
│   ├── test_insights.py
│   └── test_auth.py
└── docs/
    ├── PRD.md
    ├── API-SPEC.md
    └── DEPLOYMENT-GUIDE.md
```

## LINE API Details

**Base URL**: `https://api.line.me/v2/bot`
**Auth**: `Authorization: Bearer {CHANNEL_ACCESS_TOKEN}` header on every request.

### Key Endpoints

| Purpose | Method | Path |
|---------|--------|------|
| Account info | GET | /info |
| Friend count | GET | /insight/followers?date={YYYYMMDD} |
| Message quota | GET | /message/quota |
| Quota consumption | GET | /message/quota/consumption |
| Broadcast | POST | /message/broadcast |
| Push message | POST | /message/push |
| Multicast | POST | /message/multicast |
| Narrowcast | POST | /message/narrowcast |
| Delivery stats | GET | /insight/message/delivery?date={YYYYMMDD} |
| User profile | GET | /profile/{userId} |
| List rich menus | GET | /richmenu/list |
| Create rich menu | POST | /richmenu |
| Set default menu | POST | /user/all/richmenu/{richMenuId} |
| Link menu to user | POST | /user/{userId}/richmenu/{richMenuId} |

### Message Format (for POST endpoints)

```json
{
  "to": "USER_ID",          // for push only
  "to": ["ID1", "ID2"],     // for multicast only
  "messages": [
    { "type": "text", "text": "Hello!" }
  ]
}
```

Broadcast has no "to" field — it goes to all friends.

### Rate Limits (do not exceed)

| Endpoint group | Limit |
|---------------|-------|
| Send message | 100,000 req/min |
| Get profile | 2,000 req/min |
| Rich menu | 1,000 req/min |
| Insight | 1,000 req/min |

## Tier System

Feature gating based on user's subscription tier:

```python
TIERS = {
    "free": {
        "allowed_tools": [
            "get_account_info",
            "get_friend_count",
            "get_message_quota",
        ],
        "daily_call_limit": 100,
    },
    "pro": {
        "allowed_tools": [
            "get_account_info", "get_friend_count", "get_message_quota",
            "send_broadcast", "send_push_message", "send_multicast",
            "send_narrowcast", "get_message_stats", "get_user_profile",
            "list_rich_menus", "create_rich_menu",
            "set_default_rich_menu", "link_rich_menu_to_user",
        ],
        "daily_call_limit": 5000,
    },
    "business": {
        "allowed_tools": "__all__",
        "daily_call_limit": -1,  # unlimited
    },
}
```

Every tool call must:
1. Validate the API key
2. Check if the tool is allowed for the user's tier
3. Check if daily call limit is exceeded
4. If blocked → return a clear error message with upgrade instructions

## Coding Standards

### Style
- Use `ruff` for formatting (line length 100)
- Use `mypy` strict mode for type checking
- All functions must have type hints
- All public functions must have docstrings
- Use `async/await` for all I/O operations

### Error Handling
- Catch `httpx.HTTPStatusError` and return user-friendly messages
- Never expose raw LINE API errors to the user
- Always include the HTTP status code in error responses
- Log errors to stderr (never stdout — it breaks MCP STDIO transport)

### Testing
- Use `pytest-asyncio` for async tests
- Mock LINE API calls with `httpx.MockTransport`
- Every tool must have at least:
  - 1 success test
  - 1 error test (invalid input)
  - 1 tier restriction test (free user trying pro tool)

### Language
- Code: English (variable names, comments, docstrings)
- User-facing messages: Thai primary, English fallback
- Error messages: bilingual (Thai + English)

Example:
```python
return "ส่ง broadcast สำเร็จไปยัง friends ทั้งหมด\nBroadcast sent successfully to all friends."
```

### Git
- Branch naming: `feature/tool-name` or `fix/bug-description`
- Commit messages: conventional commits (`feat:`, `fix:`, `docs:`, `test:`)
- Always run `pytest` before committing

## Environment Variables

```bash
# Required
LINE_CHANNEL_ACCESS_TOKEN=   # From LINE Developers Console
LINE_CHANNEL_SECRET=         # From LINE Developers Console

# LineWhiz auth (for premium features)
LINEWHIZ_API_KEY=            # User's LineWhiz API key
LINEWHIZ_DATABASE_URL=sqlite:///linewhiz.db

# Optional
LINEWHIZ_LOG_LEVEL=INFO
LINEWHIZ_RATE_LIMIT_WINDOW=86400  # 24 hours in seconds
```

## Important Warnings

1. **NEVER print() to stdout** — MCP uses STDIO for JSON-RPC. Use
   `print(..., file=sys.stderr)` or `logging` with stderr handler.

2. **NEVER hardcode LINE tokens** — always read from environment.

3. **NEVER store LINE tokens in the database** — they stay in env vars only.

4. **Message quota is real money** — LINE charges per message beyond the
   free tier. Always confirm with the user before broadcasting.

5. **Test with a test LINE OA** — never test broadcast on a production
   account with real customers.

## Quick Start for Development

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/linewhiz.git
cd linewhiz
uv sync

# Set environment
cp .env.example .env
# Edit .env with your LINE tokens

# Run the server locally
uv run src/server.py

# Test with MCP inspector
mcp dev src/server.py

# Run tests
uv run pytest

# Type check
uv run mypy src/
```

## Reference Files

- `docs/line-oa-mcp-spec.md` — Full technical specification (18 tools)
- `docs/ai-workflow-playbook.md` — Development workflow with AI tools
- `server.py` (root) — Starter code with 9 tools implemented
