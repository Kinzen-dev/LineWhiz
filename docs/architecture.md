# LineWhiz — System Architecture

## 1. Component Overview

```
┌──────────────────────────────────────────────────────────────┐
│  MCP Clients (Claude Desktop, Cursor, Antigravity, ChatGPT) │
└────────────────────────────┬─────────────────────────────────┘
                             │ JSON-RPC over STDIO
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                   LineWhiz MCP Server                        │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Auth Layer  │→ │ Rate Limiter │→ │Usage Tracker │       │
│  │ (api_keys)   │  │(daily count) │  │ (log calls)  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         └──────────────────┼─────────────────┘               │
│                            ▼                                  │
│  ┌─────────────────────────────────────────────────┐        │
│  │              Tool Router (dispatch)              │        │
│  └──┬──────┬──────────┬──────────┬─────────────────┘        │
│     ▼      ▼          ▼          ▼                           │
│  account  messaging  richmenu  insights                      │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │        LineClient (httpx async wrapper)          │        │
│  └──────────────────────┬──────────────────────────┘        │
│                         │                                    │
│  ┌──────────────┐       │                                    │
│  │  SQLite DB   │       │                                    │
│  │ (api_keys,   │       │                                    │
│  │  usage_logs) │       │                                    │
│  └──────────────┘       │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │ HTTPS
                          ▼
              ┌───────────────────────┐
              │  LINE Platform API    │
              │  api.line.me/v2/bot   │
              └───────────────────────┘
```

## 2. Data Flows

### Flow A: User sends broadcast via Claude

```
User: "Broadcast: 20% off all items today only!"
  │
  ▼
Claude Desktop recognizes intent → calls MCP tool
  │  send_broadcast(message="20% off all items today only!")
  ▼
LineWhiz server.call_tool("send_broadcast", {...})
  │
  ├─ 1. auth.validate_api_key(env.LINEWHIZ_API_KEY)
  │     → lookup key in api_keys table
  │     → check is_active = true
  │     → return tier ("pro" / "business")
  │     → FAIL? return "Invalid API key. Get one at linewhiz.dev"
  │
  ├─ 2. auth.check_tier_access("send_broadcast", tier)
  │     → is "send_broadcast" in TIERS[tier].allowed_tools?
  │     → FAIL? return "send_broadcast requires Pro plan ($15/mo)"
  │
  ├─ 3. rate_limiter.check(api_key_id, daily_limit)
  │     → count usage_logs WHERE api_key_id AND date = today
  │     → FAIL? return "Daily limit (5000) reached. Resets at midnight UTC."
  │
  ├─ 4. line_client.post("/message/broadcast", {messages: [{type: "text", text: msg}]})
  │     → FAIL? return "LINE API error (HTTP 429): Rate limit exceeded"
  │
  ├─ 5. usage_tracker.log(api_key_id, "send_broadcast", success=true)
  │     → INSERT INTO usage_logs
  │
  └─ 6. return "Broadcast sent successfully to all friends."
```

### Flow B: User checks analytics

```
User: "Show me delivery stats for yesterday"
  │
  ▼
Claude calls get_message_delivery_stats(date="20260316")
  │
  ├─ 1. auth.validate_api_key → ok (pro tier)
  ├─ 2. auth.check_tier_access → ok (pro tool)
  ├─ 3. rate_limiter.check → ok (under limit)
  ├─ 4. line_client.get("/insight/message/delivery?date=20260316")
  │     → returns: {broadcast: 2341, apiPush: 156, ...}
  ├─ 5. usage_tracker.log("get_message_delivery_stats", success=true)
  └─ 6. return JSON with formatted stats
         │
         ▼
Claude receives raw data → adds natural language analysis:
"Yesterday's broadcast reached 2,341 people. Your API push
messages hit 156 users. Engagement looks healthy."
```

### Flow C: Auto-reply when customer chats (FUTURE — v2.0)

```
Customer sends "What time do you open?" to LINE OA
  │
  ▼
LINE Platform sends webhook event to LineWhiz webhook URL
  │  POST https://linewhiz.fly.dev/webhook
  │  {type: "message", text: "What time do you open?", replyToken: "xxx"}
  ▼
LineWhiz webhook handler:
  ├─ 1. Verify webhook signature (LINE_CHANNEL_SECRET)
  ├─ 2. Lookup auto-reply rules in DB
  │     → SELECT * FROM auto_replies WHERE keyword matches
  ├─ 3. If match found:
  │     → line_client.post("/message/reply", {replyToken, messages: [...]})
  │     → return 200
  └─ 4. If no match:
        → pass to human (do nothing, message stays in LINE OA inbox)

NOTE: This flow requires a webhook server (HTTP endpoint).
Not included in MVP. MVP is STDIO-only (no incoming messages).
```

## 3. Database Schema (SQLite)

### Table: api_keys

```sql
CREATE TABLE api_keys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash    TEXT    NOT NULL UNIQUE,  -- SHA-256 of the API key (never store plaintext)
    tier        TEXT    NOT NULL DEFAULT 'free',  -- 'free', 'pro', 'business'
    label       TEXT,                     -- user-defined label e.g. "My shop OA"
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
```

### Table: usage_logs

```sql
CREATE TABLE usage_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id  INTEGER NOT NULL REFERENCES api_keys(id),
    tool_name   TEXT    NOT NULL,         -- e.g. 'send_broadcast'
    success     INTEGER NOT NULL DEFAULT 1,
    error_msg   TEXT,                     -- null if success
    called_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_usage_api_date ON usage_logs(api_key_id, called_at);
```

### Table: auto_replies (FUTURE — v2.0)

```sql
CREATE TABLE auto_replies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id  INTEGER NOT NULL REFERENCES api_keys(id),
    keyword     TEXT    NOT NULL,
    match_type  TEXT    NOT NULL DEFAULT 'contains',  -- 'exact', 'contains', 'starts_with'
    response    TEXT    NOT NULL,          -- message text to reply with
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

### Why this schema is minimal

- **No users table** — MVP uses marketplace billing (Apify/MCPize handle users + payments). We only track API keys.
- **No subscriptions table** — tier is stored directly on api_key. When user upgrades via marketplace, we update the tier.
- **key_hash not plaintext** — API key is only shown once at creation. We store SHA-256 hash for validation.
- **SQLite for MVP** — zero config, file-based, runs anywhere. Migrate to PostgreSQL when we hit 1000+ users.

### Helper queries

```sql
-- Count today's usage for rate limiting
SELECT COUNT(*) FROM usage_logs
WHERE api_key_id = ? AND called_at >= date('now');

-- Get usage stats for a key (last 30 days)
SELECT tool_name, COUNT(*) as calls, SUM(success) as ok
FROM usage_logs
WHERE api_key_id = ? AND called_at >= date('now', '-30 days')
GROUP BY tool_name;

-- Most popular tools across all users
SELECT tool_name, COUNT(*) as total_calls
FROM usage_logs
WHERE called_at >= date('now', '-7 days')
GROUP BY tool_name
ORDER BY total_calls DESC;
```

## 4. Auth Flow (detailed)

```
Every tool call passes through this pipeline:

call_tool(name, arguments)
    │
    ▼
┌─ STEP 1: Extract API key ──────────────────────────────────┐
│  key = os.environ.get("LINEWHIZ_API_KEY")                   │
│  if not key:                                                 │
│      → check arguments for "api_key" field                   │
│  if still not key:                                           │
│      → return error: "LINEWHIZ_API_KEY not configured"       │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ STEP 2: Validate key ─────────────────────────────────────┐
│  key_hash = sha256(key)                                      │
│  row = SELECT * FROM api_keys WHERE key_hash = ? AND active  │
│  if not row:                                                 │
│      → return error: "Invalid API key"                       │
│  tier = row.tier                                             │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ STEP 3: Check tier permission ────────────────────────────┐
│  allowed = TIERS[tier].allowed_tools                         │
│  if tool_name not in allowed:                                │
│      → return error: "{tool} requires {min_tier} ($X/mo).    │
│        Upgrade at linewhiz.dev/pricing"                      │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ STEP 4: Check rate limit ─────────────────────────────────┐
│  today_count = SELECT COUNT(*) FROM usage_logs               │
│                WHERE api_key_id = ? AND date = today         │
│  limit = TIERS[tier].daily_call_limit                        │
│  if limit != -1 AND today_count >= limit:                    │
│      → return error: "Daily limit ({limit}) reached.         │
│        Resets at midnight UTC."                              │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ STEP 5: Execute tool ─────────────────────────────────────┐
│  result = await tool_handler(arguments)                      │
│  if error:                                                   │
│      → log failure to usage_logs                             │
│      → return user-friendly error message                    │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ STEP 6: Log + return ─────────────────────────────────────┐
│  INSERT INTO usage_logs (api_key_id, tool_name, success)     │
│  return result to MCP client                                 │
└──────────────────────────────────────────────────────────────┘
```

### MVP simplification

For the very first version, we can skip the database entirely and use a simpler approach:

```python
# MVP auth — environment-variable only, no DB
# Users just set LINE tokens. No API key management yet.
# Tier is hardcoded to "pro" for all users during beta.

TIER = os.environ.get("LINEWHIZ_TIER", "pro")
```

Then add DB-backed auth in v1.1 when we need to differentiate free vs paid users.

## 5. Error Handling Strategy

### Principle: Never expose raw errors. Always be helpful.

```python
ERROR_MAP = {
    400: "Invalid request. Please check your input and try again.",
    401: "LINE API authentication failed. Check your LINE_CHANNEL_ACCESS_TOKEN.",
    403: "Permission denied. Your LINE OA plan may not support this feature.",
    404: "Resource not found. The user ID or rich menu ID may be invalid.",
    409: "Conflict. This action has already been performed.",
    429: "LINE API rate limit hit. Please wait a moment and try again.",
    500: "LINE Platform error. This is temporary — try again in a few seconds.",
}
```

### Error response format

```python
# All errors return a helpful TextContent, never raise exceptions to the client
return TextContent(
    type="text",
    text=f"Error: {user_friendly_message}\n\nDetails: HTTP {status_code} from LINE API."
)
```

### Error categories

| Category | Example | How we handle |
|----------|---------|---------------|
| Auth error | Invalid API key | Return error + link to docs |
| Tier error | Free user tries pro tool | Return error + pricing link |
| Rate limit | 5000 calls exceeded | Return error + reset time |
| LINE API error | 429 rate limit | Return error + retry suggestion |
| LINE API error | 400 bad request | Return error + input hint |
| Network error | Connection timeout | Return error + retry suggestion |
| Unexpected error | Anything else | Log to stderr + return generic error |

### Retry strategy

LineWhiz does NOT auto-retry. If LINE API returns an error, we report it to the user and let them decide. Rationale: a broadcast retry could send duplicate messages to all followers. The user should explicitly re-send.

### Logging

```python
import sys
import logging

# CRITICAL: Configure logging to stderr, NEVER stdout
logging.basicConfig(
    stream=sys.stderr,
    level=os.environ.get("LINEWHIZ_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("linewhiz")

# Log every tool call (success and failure)
logger.info(f"Tool called: {tool_name} by key:{key_id[:8]}... → success")
logger.warning(f"Tool failed: {tool_name} → HTTP {status}")
logger.error(f"Unexpected error in {tool_name}: {str(e)}")
```

## 6. Security Considerations

### API key storage
- User's LINE tokens: environment variables ONLY. Never in DB.
- LineWhiz API keys: stored as SHA-256 hash in DB. Plaintext shown once at creation.
- Never log full API keys. Log only first 8 chars for debugging.

### Input validation
- All tool inputs validated with Pydantic before hitting LINE API.
- user_id must match pattern `^U[a-f0-9]{32}$`
- date must match pattern `^\d{8}$`
- message text max 5000 chars (LINE limit)
- multicast user_ids max 500 (LINE limit)

### Transport security
- STDIO transport (MVP): data stays local, no network exposure
- HTTP/SSE transport (future): require TLS, validate API key in header

## 7. Deployment Architecture (MVP)

```
Developer's machine:
┌─────────────────────────────────────────────┐
│  Claude Desktop / Cursor / Antigravity       │
│       │                                      │
│       │ STDIO (stdin/stdout)                 │
│       ▼                                      │
│  LineWhiz MCP server (Python process)        │
│       │                                      │
│       │ HTTPS (outbound only)                │
│       ▼                                      │
│  ─────── internet ──────                     │
└─────────────────────────────────────────────┘
              │
              ▼
     LINE Platform API
     (api.line.me)
```

### MVP: Local only (STDIO)
- Server runs as a Python process on user's machine
- Launched by Claude Desktop via config
- No hosting cost
- No server to maintain
- Data stays local

### Future: Remote (HTTP/SSE)
- Server runs on Railway.app / Fly.io
- Users connect via URL in MCP config
- Enables marketplace distribution
- Hosting cost ~$5-20/month
- Requires API key auth (DB-backed)
