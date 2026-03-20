# CLAUDE.md — LineWhiz

> Read this FIRST before writing any code. This is the single source of truth.

## What is LineWhiz

Premium MCP server that lets AI agents manage LINE Official Accounts.
Users type natural language in Claude/ChatGPT/Cursor → LineWhiz calls LINE API.

## Strategy

- **English-first**. All code, docs, responses, listings in English.
- **Global market**. LINE is used in Japan (95M), Thailand (56M), Taiwan (21M).
- **Pricing**: Free / $15/mo (Pro) / $45/mo (Business) — in USD.
- Tool responses in English. MCP client auto-translates for local users.
- **Do NOT hardcode Thai/Japanese strings anywhere.**

## Tech Stack

Python 3.11+ | `mcp` SDK v1.2+ | `line-bot-sdk` | `httpx` (async) | `pydantic` | `aiosqlite` | `pytest` + `pytest-asyncio` | `ruff` | `mypy` strict | `uv` | Docker → Railway.app

## Project Structure

```
linewhiz/
├── CLAUDE.md
├── pyproject.toml
├── Dockerfile
├── .env.example
├── README.md
├── src/
│   ├── server.py          # MCP entry point + tool registration
│   ├── config.py          # Env config via pydantic Settings
│   ├── auth/
│   │   ├── api_keys.py    # Key validation (SHA-256 hash lookup)
│   │   └── tiers.py       # Free/Pro/Business gating + rate limits
│   ├── tools/
│   │   ├── account.py     # get_account_info, get_friend_count, get_message_quota
│   │   ├── messaging.py   # send_broadcast, send_push, send_multicast, send_narrowcast
│   │   ├── richmenu.py    # list/create/set/link rich menus
│   │   ├── insights.py    # get_message_stats, get_audience_insights
│   │   ├── automation.py  # [future] auto-reply, flex message
│   │   └── reporting.py   # [future] weekly report
│   ├── services/
│   │   ├── line_api.py    # Async LINE API wrapper (all HTTP calls go through here)
│   │   └── flex_builder.py
│   ├── models/
│   │   ├── user.py        # Pydantic models for API key + tier
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
    ├── architecture.md
    ├── PRD.md
    ├── linewhiz-spec.md
    └── market-analysis.md
```

## Architecture: Request Pipeline

Every MCP tool call flows through this exact pipeline:

```
call_tool(name, args)
  → 1. validate_api_key(env.LINEWHIZ_API_KEY)     # is key valid + active?
  → 2. check_tier_access(tool_name, tier)          # is tool allowed for this tier?
  → 3. check_rate_limit(api_key_id, daily_limit)   # under daily call cap?
  → 4. execute tool handler                         # call LINE API
  → 5. log to usage_logs                            # track call
  → 6. return result or error                       # always TextContent
```

If any step fails → return error immediately, do NOT continue pipeline.

### MVP simplification

For initial launch, skip DB-backed auth. Use env-var tier:

```python
TIER = os.environ.get("LINEWHIZ_TIER", "pro")  # hardcode pro for beta
```

Add DB-backed auth in v1.1 when differentiating free/paid users.

## Database Schema (SQLite)

```sql
CREATE TABLE api_keys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash    TEXT    NOT NULL UNIQUE,   -- SHA-256, never store plaintext
    tier        TEXT    NOT NULL DEFAULT 'free',
    label       TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

CREATE TABLE usage_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id  INTEGER NOT NULL REFERENCES api_keys(id),
    tool_name   TEXT    NOT NULL,
    success     INTEGER NOT NULL DEFAULT 1,
    error_msg   TEXT,
    called_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_usage_api_date ON usage_logs(api_key_id, called_at);
```

Rate limit query:
```sql
SELECT COUNT(*) FROM usage_logs
WHERE api_key_id = ? AND called_at >= date('now');
```

## Tier System

```python
TIERS = {
    "free": {
        "allowed_tools": [
            "get_account_info", "get_friend_count", "get_message_quota",
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
        "daily_call_limit": -1,
    },
}
```

## LINE API Quick Reference

**Base URL**: `https://api.line.me/v2/bot`
**Auth**: `Authorization: Bearer {LINE_CHANNEL_ACCESS_TOKEN}`

| Purpose | Method | Path |
|---------|--------|------|
| Account info | GET | /info |
| Friend count | GET | /insight/followers?date={YYYYMMDD} |
| Message quota | GET | /message/quota |
| Quota used | GET | /message/quota/consumption |
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

**Rate limits**: Send 100K/min, Profile 2K/min, Richmenu 1K/min, Insight 1K/min.

## Error Handling

```python
ERROR_MESSAGES = {
    400: "Invalid request. Check your input.",
    401: "LINE auth failed. Check LINE_CHANNEL_ACCESS_TOKEN.",
    403: "Permission denied. Your LINE OA plan may not support this.",
    404: "Not found. Check the user ID or rich menu ID.",
    429: "LINE rate limit hit. Wait a moment and retry.",
    500: "LINE Platform error. Temporary — retry in a few seconds.",
}
```

Rules:
- Never expose raw LINE API error bodies to user
- Always return `TextContent(type="text", text=...)` — never raise to client
- Log all errors to stderr with `logger.warning()` or `logger.error()`
- Do NOT auto-retry broadcasts (could send duplicates)

## Input Validation

```python
# Validate before calling LINE API
user_id:  must match r"^U[a-f0-9]{32}$"
date:     must match r"^\d{8}$"
message:  max 5000 chars
user_ids: max 500 items (LINE multicast limit)
```

## Coding Rules

1. **NEVER print() to stdout** — breaks MCP STDIO. Use stderr/logging.
2. **NEVER hardcode tokens** — env vars only.
3. **NEVER store tokens in DB** — env vars only.
4. **NEVER hardcode Thai/Japanese** — English responses, AI client translates.
5. **ALWAYS confirm before broadcast** — message quota costs money.
6. **ALWAYS test on test LINE OA** — never production.
7. **async/await** for all I/O.
8. **Type hints** on every function.
9. **Docstrings** (English) on every public function.
10. **Conventional commits**: `feat:`, `fix:`, `docs:`, `test:`.

## Environment Variables

```bash
LINE_CHANNEL_ACCESS_TOKEN=   # From LINE Developers Console → Messaging API tab
LINE_CHANNEL_SECRET=         # From LINE Developers Console → Basic settings
LINEWHIZ_TIER=pro            # MVP: hardcoded tier (free/pro/business)
LINEWHIZ_DATABASE_URL=sqlite:///linewhiz.db
LINEWHIZ_LOG_LEVEL=INFO
```

## Quick Start

```bash
cd linewhiz && uv sync
cp .env.example .env        # fill in LINE tokens
uv run src/server.py        # run
mcp dev src/server.py       # test with inspector
uv run pytest               # tests
```

## What to build (in order)

### MVP (9 tools — ship this first)
1. get_account_info
2. get_friend_count
3. get_message_quota
4. send_broadcast
5. send_push_message
6. send_multicast
7. get_message_delivery_stats
8. get_user_profile
9. list_rich_menus
+ auth middleware (env-var tier for MVP)
+ usage logging to SQLite

### v1.1 (add after launch)
10. send_narrowcast
11. create_rich_menu
12. set_default_rich_menu
13. link_rich_menu_to_user
14. get_audience_insights
15. create_flex_message
+ DB-backed API key auth
+ HTTP/SSE transport

### v2.0 (future)
16. create_coupon
17. setup_auto_reply (needs webhook server)
18. generate_weekly_report
+ Multi-account switching
+ Stripe billing
