# LineWhiz — Test Plan

**Phase**: 4 (QA & Testing)
**Date**: March 2026
**Status**: Ready for execution

---

## How to use this document

- Run through each section in order
- Check off items as they pass
- If a test fails → fix → re-run → then check off
- Target: **100% of Must-Pass**, 80%+ of Nice-to-Have
- Give this file to **Claude Code** with: `"Read docs/TEST-PLAN.md and run all tests. Fix any that fail."`

---

## 1. Unit Tests — Per Tool

### 1.1 Free Tier Tools

#### get_account_info

- [ ] Returns valid JSON with all expected fields (bot_name, user_id, basic_id, picture_url, chat_mode)
- [ ] All field values are strings (not None/null)
- [ ] Works with valid LINE_CHANNEL_ACCESS_TOKEN
- [ ] Returns clear error when token is missing
- [ ] Returns clear error when token is invalid (401 from LINE)

#### get_friend_count

- [ ] Returns follower count for a valid date (YYYYMMDD)
- [ ] Defaults to yesterday when no date is provided
- [ ] Returns JSON with followers, targeted_reaches, blocks, status fields
- [ ] Followers count is an integer >= 0
- [ ] Returns error for invalid date format (e.g. "2026-03-16" instead of "20260316")
- [ ] Returns error for future date (LINE API returns no data)
- [ ] Returns error for date too far in the past (LINE keeps ~30 days)

#### get_message_quota

- [ ] Returns JSON with quota_type, total_quota, used_this_month, remaining
- [ ] total_quota is integer or "none" (for unlimited plans)
- [ ] used_this_month is integer >= 0
- [ ] remaining = total - used (or "unlimited")
- [ ] Works correctly at start of month (used = 0)
- [ ] Works correctly near end of quota (remaining = low number)

---

### 1.2 Pro Tier Tools — Messaging

#### send_broadcast

- [ ] Sends text message successfully, returns confirmation string
- [ ] Confirmation includes message preview (truncated to 80 chars)
- [ ] Handles messages up to 5000 chars (LINE max)
- [ ] Returns error for empty message ("")
- [ ] Returns error for message over 5000 chars
- [ ] Returns error when LINE API returns 400 (bad request)
- [ ] Returns error when LINE API returns 429 (rate limited)
- [ ] Does NOT auto-retry on failure (prevents duplicate broadcasts)

#### send_push_message

- [ ] Sends message to valid user_id, returns confirmation
- [ ] Confirmation includes user_id and message preview
- [ ] Returns error for invalid user_id format (not matching `U[a-f0-9]{32}`)
- [ ] Returns error for non-existent user_id (LINE returns 400)
- [ ] Returns error for empty message
- [ ] Returns error for blocked user (LINE returns 400)

#### send_multicast

- [ ] Sends to list of valid user_ids, returns confirmation with count
- [ ] Handles 1 user_id (minimum)
- [ ] Handles 500 user_ids (maximum)
- [ ] Returns error for 501+ user_ids with clear message about the 500 limit
- [ ] Returns error for empty user_ids list
- [ ] Returns error if any user_id has invalid format
- [ ] Returns error for empty message

#### send_narrowcast (v1.1)

- [ ] Sends with gender filter only
- [ ] Sends with age_range filter only
- [ ] Sends with area filter only
- [ ] Sends with combined filters (gender + age)
- [ ] Returns error when target audience < 100 users (LINE requirement)
- [ ] Returns error for invalid gender value (not male/female)
- [ ] Returns error for invalid age_range format

---

### 1.3 Pro Tier Tools — Read Operations

#### get_message_delivery_stats

- [ ] Returns JSON with all stat fields for valid date
- [ ] Includes broadcast, targeting, auto_response, api_broadcast, api_push, api_multicast counts
- [ ] All count values are integers >= 0
- [ ] Returns error for invalid date format
- [ ] Returns `status: "not_ready"` for very recent dates (LINE needs processing time)

#### get_user_profile

- [ ] Returns JSON with display_name, picture_url, status_message, language
- [ ] display_name is a non-empty string
- [ ] picture_url is a valid URL or "N/A"
- [ ] language code is valid (e.g. "en", "ja", "th") or "N/A"
- [ ] Returns error for invalid user_id format
- [ ] Returns error for non-existent user_id
- [ ] Handles users with no profile picture gracefully
- [ ] Handles users with no status message gracefully

#### list_rich_menus

- [ ] Returns JSON array of rich menus when menus exist
- [ ] Each menu has rich_menu_id, name, chat_bar_text, size, areas_count
- [ ] Returns "No rich menus found" message when none exist
- [ ] rich_menu_id follows LINE's format
- [ ] areas_count is integer >= 0

---

### 1.4 Pro Tier Tools — Rich Menu Management (v1.1)

#### create_rich_menu

- [ ] Creates menu with valid name, chat_bar_text, and areas
- [ ] Returns the new rich_menu_id
- [ ] Handles 1 area (minimum)
- [ ] Handles 20 areas (maximum per LINE spec)
- [ ] Returns error for missing required fields
- [ ] Returns error for invalid area coordinates

#### set_default_rich_menu

- [ ] Sets valid rich_menu_id as default, returns confirmation
- [ ] Returns error for non-existent rich_menu_id
- [ ] Returns error for empty rich_menu_id

#### link_rich_menu_to_user

- [ ] Links valid rich_menu_id to valid user_id
- [ ] Returns error for invalid user_id format
- [ ] Returns error for non-existent rich_menu_id

---

## 2. Integration Tests (MCP Client → Server → LINE API)

These test the full pipeline, not just individual tools.

### 2.1 MCP Protocol Integration

- [ ] Server starts successfully with `uv run src/server.py`
- [ ] Server registers all expected tools (check `list_tools` response)
- [ ] Tool count matches expected number for current version
- [ ] Each tool has a valid `inputSchema` with correct types
- [ ] Server responds to `call_tool` with `TextContent` type
- [ ] Server handles unknown tool name gracefully (returns error, doesn't crash)
- [ ] Server handles malformed JSON arguments (returns error, doesn't crash)
- [ ] Server handles missing required arguments (returns error, doesn't crash)

### 2.2 MCP Inspector Test

- [ ] `mcp dev src/server.py` launches without errors
- [ ] All tools appear in inspector tool list
- [ ] Can call get_account_info through inspector and see LINE OA info
- [ ] Can call get_friend_count through inspector
- [ ] Can call send_push_message to a test user through inspector
- [ ] Error responses display correctly in inspector

### 2.3 Claude Desktop Integration

- [ ] Config in claude_desktop_config.json loads LineWhiz server
- [ ] Tools icon appears in Claude Desktop chat input
- [ ] User can ask "How many friends does my LINE OA have?" → Claude calls get_friend_count
- [ ] User can ask "Broadcast: hello everyone" → Claude calls send_broadcast
- [ ] User can ask "Show me yesterday's message stats" → Claude calls get_message_delivery_stats
- [ ] Error messages from LineWhiz display clearly in Claude chat

### 2.4 End-to-End Scenario Tests

#### Scenario A: Morning check routine
- [ ] Ask: "Give me a quick overview of my LINE OA" → calls get_account_info
- [ ] Ask: "How many followers do I have?" → calls get_friend_count
- [ ] Ask: "How many messages can I still send this month?" → calls get_message_quota
- [ ] All 3 calls succeed within 5 seconds total

#### Scenario B: Campaign broadcast
- [ ] Ask: "Send a broadcast: 20% off all items today only" → calls send_broadcast
- [ ] Verify message actually arrives on LINE OA test account
- [ ] Ask: "Show me delivery stats for today" → calls get_message_delivery_stats (may show "not_ready")
- [ ] Ask same stats query next day → shows actual delivery numbers

#### Scenario C: Customer follow-up
- [ ] Ask: "Send a message to user U1234...5678: Your order shipped!" → calls send_push_message
- [ ] Verify message arrives on test user's LINE
- [ ] Ask: "Show me their profile" → calls get_user_profile with same user_id

---

## 3. Edge Cases

### 3.1 Authentication Edge Cases

- [ ] Missing LINE_CHANNEL_ACCESS_TOKEN env var → clear error on server startup
- [ ] Empty string LINE_CHANNEL_ACCESS_TOKEN → clear error
- [ ] Expired/revoked LINE token → clear error on first tool call (not crash)
- [ ] LINE token with wrong channel (valid format but wrong OA) → LINE returns 401 → clear error
- [ ] Missing LINEWHIZ_TIER env var → defaults to "pro" (MVP behavior)
- [ ] Invalid LINEWHIZ_TIER value (e.g. "premium") → defaults to "free" or errors clearly

### 3.2 Rate Limit Edge Cases

- [ ] Exactly at daily limit (call 5000/5000) → should succeed
- [ ] One over daily limit (call 5001/5000) → should fail with clear message
- [ ] Rate limit resets correctly at midnight UTC
- [ ] Free tier user hits 100 limit → error includes upgrade suggestion
- [ ] Business tier (unlimited) never hits rate limit → confirm with 10000+ calls

### 3.3 Tier Gating Edge Cases

- [ ] Free user calls get_account_info → succeeds
- [ ] Free user calls send_broadcast → blocked with "requires Pro ($15/mo)" message
- [ ] Free user calls list_rich_menus → blocked with clear error
- [ ] Pro user calls send_broadcast → succeeds
- [ ] Pro user calls create_flex_message (business tool) → blocked
- [ ] Business user calls any tool → all succeed
- [ ] Error message includes specific tool name and required tier
- [ ] Error message includes upgrade link (linewhiz.dev/pricing)

### 3.4 LINE API Edge Cases

- [ ] LINE API returns 429 (rate limited) → user gets "wait and retry" message
- [ ] LINE API returns 500 (server error) → user gets "temporary, retry" message
- [ ] LINE API timeout (> 30 seconds) → user gets timeout error, not hang
- [ ] LINE API returns unexpected JSON structure → handled gracefully, no crash
- [ ] LINE API returns empty response body → handled gracefully
- [ ] Network disconnection during API call → clear error message

### 3.5 Input Edge Cases

- [ ] Message with only spaces → should error or LINE handles it
- [ ] Message with Unicode emoji → sends correctly
- [ ] Message with Japanese characters → sends correctly
- [ ] Message with Thai characters → sends correctly
- [ ] Message exactly 5000 chars → succeeds
- [ ] Message 5001 chars → error before calling LINE API
- [ ] user_id with uppercase U + 32 hex chars → valid
- [ ] user_id with lowercase u → invalid, caught by validation
- [ ] user_id too short (< 33 chars) → invalid
- [ ] user_id too long (> 33 chars) → invalid
- [ ] Date "00000000" → invalid
- [ ] Date "99991231" → valid format but future date, LINE returns error
- [ ] Empty arguments object {} for tool requiring args → clear error

---

## 4. Load Test Scenarios

### 4.1 Sequential Load

- [ ] Call get_account_info 100 times sequentially → all succeed, no degradation
- [ ] Call get_friend_count 100 times → all succeed
- [ ] Call send_push_message 50 times to same user → all succeed (check LINE API rate limit)
- [ ] Mixed tool calls: 200 random calls across all tools → all succeed or fail gracefully

### 4.2 Concurrent Load (if using HTTP/SSE transport — future)

- [ ] 10 simultaneous get_account_info calls → all return correctly
- [ ] 5 simultaneous send_push_message calls → all send, no duplicates
- [ ] 20 simultaneous mixed calls → no crashes, no data corruption

### 4.3 Memory & Resource Tests

- [ ] Server runs for 1 hour with periodic calls → no memory leak (RSS stays stable)
- [ ] SQLite DB stays under 10MB after 10,000 usage_log entries
- [ ] Server startup time < 3 seconds
- [ ] Single tool call response time < 2 seconds (excluding LINE API latency)

### 4.4 LINE API Rate Limit Awareness

- [ ] Sending 1000 push messages in 1 minute → should work (LINE allows 100K/min)
- [ ] Track actual response times from LINE → document P50, P95, P99
- [ ] If LINE returns 429 → LineWhiz reports it, doesn't retry

---

## 5. Security Tests

### 5.1 Token/Key Protection

- [ ] LINE_CHANNEL_ACCESS_TOKEN never appears in any log output
- [ ] LINE_CHANNEL_SECRET never appears in any log output
- [ ] API keys never appear in full in log output (only first 8 chars max)
- [ ] No tokens/keys in error messages returned to user
- [ ] No tokens/keys in usage_logs database table
- [ ] `.env` file is in `.gitignore`
- [ ] Verify git history has no committed secrets (run `git log --all -p | grep -i "channel_access_token"`)

### 5.2 Input Injection

- [ ] Message with SQL injection attempt (`'; DROP TABLE usage_logs; --`) → handled safely (parameterized queries)
- [ ] Message with MCP protocol injection (`{"jsonrpc": "2.0", ...}`) → treated as plain text, no execution
- [ ] user_id with path traversal (`../../../etc/passwd`) → caught by regex validation
- [ ] Tool name injection (calling non-existent tool with special chars) → clean error
- [ ] Arguments with extremely large strings (1MB+) → rejected before processing

### 5.3 Data Isolation

- [ ] Usage logs for one API key can't be read by another key
- [ ] Rate limit for one API key doesn't affect another key
- [ ] SQLite DB file has restrictive permissions (owner read/write only)

### 5.4 Transport Security

- [ ] STDIO transport: data doesn't leave the local machine (verify no outbound except LINE API)
- [ ] All LINE API calls use HTTPS (never HTTP)
- [ ] No sensitive data in URL parameters (all in headers or POST body)

### 5.5 Dependency Security

- [ ] Run `uv pip audit` or `pip-audit` → no known vulnerabilities in dependencies
- [ ] All dependencies pinned to specific versions in pyproject.toml
- [ ] No unnecessary dependencies installed

---

## 6. Regression Checklist (run before every release)

Quick smoke test to run before pushing any update:

- [ ] `uv sync` completes without errors
- [ ] `uv run pytest` — all tests pass
- [ ] `uv run mypy src/` — no type errors
- [ ] `uv run ruff check src/` — no lint errors
- [ ] `mcp dev src/server.py` — server starts, tools listed
- [ ] Call get_account_info → returns valid data
- [ ] Call send_push_message to test user → message arrives on LINE
- [ ] Call with missing token → error message (not crash)
- [ ] Check server logs (stderr) — no warnings/errors during normal operation

---

## 7. Test Infrastructure

### Mock Strategy

```python
# tests/conftest.py

import pytest
import httpx

@pytest.fixture
def mock_line_api():
    """Mock LINE API responses for unit tests."""
    
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        
        if path == "/v2/bot/info":
            return httpx.Response(200, json={
                "userId": "U1234567890abcdef1234567890abcdef",
                "basicId": "@linewhiz-test",
                "displayName": "Test OA",
                "pictureUrl": "https://example.com/pic.jpg",
                "chatMode": "bot",
                "markAsReadMode": "manual",
            })
        
        if path == "/v2/bot/message/quota":
            return httpx.Response(200, json={
                "type": "limited",
                "value": 1000,
            })
        
        if path == "/v2/bot/message/quota/consumption":
            return httpx.Response(200, json={
                "totalUsage": 350,
            })
        
        if path == "/v2/bot/message/broadcast":
            return httpx.Response(200, json={})
        
        if path.startswith("/v2/bot/message/push"):
            return httpx.Response(200, json={})
        
        if path.startswith("/v2/bot/profile/"):
            user_id = path.split("/")[-1]
            return httpx.Response(200, json={
                "userId": user_id,
                "displayName": "Test User",
                "pictureUrl": "https://example.com/user.jpg",
                "statusMessage": "Hello",
                "language": "en",
            })
        
        if path == "/v2/bot/richmenu/list":
            return httpx.Response(200, json={"richmenus": []})
        
        if "/insight/followers" in path:
            return httpx.Response(200, json={
                "status": "ready",
                "followers": 2847,
                "targetedReaches": 2500,
                "blocks": 47,
            })
        
        if "/insight/message/delivery" in path:
            return httpx.Response(200, json={
                "status": "ready",
                "broadcast": 2341,
                "targeting": 0,
                "autoResponse": 45,
                "welcomeResponse": 12,
                "chat": 156,
                "apiBroadcast": 2341,
                "apiPush": 89,
                "apiMulticast": 0,
                "apiReply": 23,
            })
        
        return httpx.Response(404, json={"message": "Not found"})
    
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport, base_url="https://api.line.me")
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_messaging.py

# Run specific test
uv run pytest tests/test_messaging.py::test_send_broadcast_success

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Type check
uv run mypy src/

# Lint
uv run ruff check src/ tests/
```

### CI Pipeline (future — GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run ruff check src/ tests/
      - run: uv run mypy src/
      - run: uv run pytest --cov=src
```

---

## Pass Criteria

| Category | Must pass | Target |
|----------|-----------|--------|
| Unit tests (free tier) | 100% | All 15 checks |
| Unit tests (pro messaging) | 100% | All 28 checks |
| Unit tests (pro read) | 100% | All 20 checks |
| Integration (MCP protocol) | 100% | All 8 checks |
| Integration (Claude Desktop) | 100% | All 6 checks |
| Edge cases (auth) | 100% | All 6 checks |
| Edge cases (tier gating) | 100% | All 8 checks |
| Edge cases (LINE API) | 100% | All 6 checks |
| Edge cases (input) | 90%+ | 12 of 14 checks |
| Load tests | 80%+ | 4 of 5 checks |
| Security tests | 100% | All 15 checks |
| **Total** | **95%+** | **~130 checks** |

---

*Next step: Give this file to Claude Code →*
*`"Read docs/TEST-PLAN.md. Run all existing tests. Write tests for any uncovered items. Fix failures."`*