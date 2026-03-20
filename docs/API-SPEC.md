# LineWhiz — API Specification

**Version**: 1.0
**Protocol**: MCP (Model Context Protocol) over JSON-RPC
**Transport**: STDIO (MVP) | HTTP/SSE (v1.1+)
**Server Name**: `line-oa-mcp`

---

## Overview

LineWhiz exposes 18 MCP tools organized into 3 tiers. Every tool call passes through the authentication pipeline before execution:

```
call_tool(name, args)
  → 1. validate_api_key()     — Is the key valid and active?
  → 2. check_tier_access()    — Is this tool allowed for the user's tier?
  → 3. check_rate_limit()     — Is the user under their daily call cap?
  → 4. execute tool handler   — Call LINE API
  → 5. log to usage_logs      — Track the call
  → 6. return result or error — Always TextContent
```

All responses are returned as `TextContent(type="text", text=...)`. Errors never raise exceptions to the client.

---

## Authentication

### Environment Variables (Required)

| Variable | Description |
|----------|-------------|
| `LINE_CHANNEL_ACCESS_TOKEN` | Long-lived token from LINE Developers Console |
| `LINE_CHANNEL_SECRET` | Channel secret from LINE Developers Console |
| `LINEWHIZ_TIER` | Tier override for MVP: `free`, `pro`, `business` (default: `pro`) |
| `LINEWHIZ_API_KEY` | LineWhiz API key (DB-backed auth, v1.1+) |
| `LINEWHIZ_DATABASE_URL` | SQLite connection string (default: `sqlite:///linewhiz.db`) |
| `LINEWHIZ_LOG_LEVEL` | Logging level (default: `INFO`) |

### Tier Permissions

| Tier | Price | Allowed Tools | Daily Call Limit | Max Broadcasts/Day |
|------|-------|---------------|------------------|--------------------|
| **Free** | $0 | Tools 1–3 | 100 | 0 |
| **Pro** | $15/mo | Tools 1–13 | 5,000 | 10 |
| **Business** | $45/mo | Tools 1–18 (all) | Unlimited | Unlimited |

---

## LINE API Base URLs

| Purpose | Base URL |
|---------|----------|
| Messaging & Management | `https://api.line.me/v2/bot` |
| Binary Data (images) | `https://api-data.line.me/v2/bot` |

**Auth Header**: `Authorization: Bearer {LINE_CHANNEL_ACCESS_TOKEN}`

---

## Common Input Validation Rules

| Field | Rule | Example |
|-------|------|---------|
| `user_id` | Must match `^U[a-f0-9]{32}$` | `Uf3b0a...` |
| `date` | Must match `^\d{8}$` (YYYYMMDD) | `20260317` |
| `message` | Max 5,000 characters | — |
| `user_ids` | Max 500 items | — |
| `rich_menu_id` | String, LINE-issued ID | `richmenu-abc123...` |

---

## Error Response Format

All errors return a user-friendly `TextContent` message. Raw LINE API errors are never exposed.

```json
{
  "type": "text",
  "text": "Error: {user_friendly_message}\n\nDetails: HTTP {status_code} from LINE API."
}
```

### Error Code Mapping

| HTTP Code | User-Facing Message |
|-----------|---------------------|
| 400 | Invalid request. Please check your input and try again. |
| 401 | LINE API authentication failed. Check your LINE_CHANNEL_ACCESS_TOKEN. |
| 403 | Permission denied. Your LINE OA plan may not support this feature. |
| 404 | Resource not found. The user ID or rich menu ID may be invalid. |
| 409 | Conflict. This action has already been performed. |
| 429 | LINE API rate limit hit. Please wait a moment and try again. |
| 500 | LINE Platform error. This is temporary — try again in a few seconds. |

### Auth/Tier Errors

| Condition | Message |
|-----------|---------|
| Missing API key | `LINEWHIZ_API_KEY not configured. Set it in your environment.` |
| Invalid API key | `Invalid API key. Get one at linewhiz.dev` |
| Tier blocked | `{tool_name} requires {min_tier} plan (${price}/mo). Upgrade at linewhiz.dev/pricing` |
| Rate limit exceeded | `Daily limit ({limit}) reached. Resets at midnight UTC.` |

---

## Tools — FREE Tier

### Tool 1: `get_account_info`

Get LINE Official Account information.

| Property | Value |
|----------|-------|
| **Tier** | Free |
| **LINE API** | `GET /v2/bot/info` |
| **Rate Limit** | 2,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Output** (JSON string):
```json
{
  "bot_name": "My Shop",
  "user_id": "U1234567890abcdef...",
  "basic_id": "@myshop",
  "premium_id": "@premium-id",
  "picture_url": "https://profile.line-scdn.net/...",
  "chat_mode": "chat",
  "mark_as_read_mode": "auto"
}
```

---

### Tool 2: `get_friend_count`

Get the number of followers on a specific date.

| Property | Value |
|----------|-------|
| **Tier** | Free |
| **LINE API** | `GET /v2/bot/insight/followers?date={YYYYMMDD}` |
| **Rate Limit** | 1,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "date": {
      "type": "string",
      "description": "Date in YYYYMMDD format. Defaults to yesterday if omitted."
    }
  }
}
```

**Output** (JSON string):
```json
{
  "date": "20260316",
  "followers": 2847,
  "targeted_reaches": 2500,
  "blocks": 12,
  "status": "ready"
}
```

---

### Tool 3: `get_message_quota`

Get remaining message quota for the current month.

| Property | Value |
|----------|-------|
| **Tier** | Free |
| **LINE API** | `GET /v2/bot/message/quota` + `GET /v2/bot/message/quota/consumption` |
| **Rate Limit** | 2,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Output** (JSON string):
```json
{
  "quota_type": "limited",
  "total_quota": 25000,
  "used_this_month": 1230,
  "remaining": 23770
}
```

---

## Tools — PRO Tier ($15/mo)

### Tool 4: `send_broadcast`

Send a message to ALL friends. Use carefully — this reaches everyone and consumes message quota.

| Property | Value |
|----------|-------|
| **Tier** | Pro |
| **LINE API** | `POST /v2/bot/message/broadcast` |
| **Rate Limit** | 100,000 req/min (LINE) |
| **Caution** | No auto-retry (could send duplicates) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "message": {
      "type": "string",
      "description": "Text message to broadcast (max 5000 chars)"
    },
    "message_type": {
      "type": "string",
      "enum": ["text", "image", "flex", "template"],
      "description": "Message type. Default: 'text'"
    },
    "schedule_time": {
      "type": "string",
      "description": "ISO 8601 datetime for scheduled send (optional, future feature)"
    }
  },
  "required": ["message"]
}
```

**Output**: `"Broadcast sent successfully. Message: '{first_50_chars}...'"`

---

### Tool 5: `send_push_message`

Send a direct message to a specific user.

| Property | Value |
|----------|-------|
| **Tier** | Pro |
| **LINE API** | `POST /v2/bot/message/push` |
| **Rate Limit** | 100,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "LINE user ID (starts with U, 33 chars)"
    },
    "message": {
      "type": "string",
      "description": "Text message to send (max 5000 chars)"
    },
    "message_type": {
      "type": "string",
      "enum": ["text", "image", "flex", "template"],
      "description": "Message type. Default: 'text'"
    }
  },
  "required": ["user_id", "message"]
}
```

**Output**: `"Push message sent to {user_id}. Message: '{first_50_chars}...'"`

---

### Tool 6: `send_multicast`

Send a message to multiple specific users (max 500).

| Property | Value |
|----------|-------|
| **Tier** | Pro |
| **LINE API** | `POST /v2/bot/message/multicast` |
| **Rate Limit** | 100,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "user_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of LINE user IDs (max 500)"
    },
    "message": {
      "type": "string",
      "description": "Text message to send (max 5000 chars)"
    },
    "message_type": {
      "type": "string",
      "enum": ["text", "image", "flex", "template"],
      "description": "Message type. Default: 'text'"
    }
  },
  "required": ["user_ids", "message"]
}
```

**Output**: `"Multicast sent to {count} users. Message: '{first_50_chars}...'"`

---

### Tool 7: `send_narrowcast`

Send targeted messages to specific audience segments.

| Property | Value |
|----------|-------|
| **Tier** | Pro |
| **LINE API** | `POST /v2/bot/message/narrowcast` |
| **Rate Limit** | 100,000 req/min (LINE) |
| **Constraint** | Audience must have 100+ targetable users |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "message": {
      "type": "string",
      "description": "Text message to send (max 5000 chars)"
    },
    "gender": {
      "type": "string",
      "enum": ["male", "female"],
      "description": "Filter by gender. Omit for all."
    },
    "age_range": {
      "type": "string",
      "description": "Age range filter, e.g. '20-30', '30-40'"
    },
    "area": {
      "type": "string",
      "description": "Region/prefecture code for geographic targeting"
    },
    "message_type": {
      "type": "string",
      "enum": ["text", "image", "flex", "template"],
      "description": "Message type. Default: 'text'"
    }
  },
  "required": ["message"]
}
```

**Output**: `"Narrowcast sent to targeted audience. Filters: gender={gender}, age={age_range}, area={area}"`

---

### Tool 8: `get_message_stats`

Get delivery statistics for messages sent on a specific date.

| Property | Value |
|----------|-------|
| **Tier** | Pro |
| **LINE API** | `GET /v2/bot/insight/message/delivery?date={YYYYMMDD}` |
| **Rate Limit** | 1,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "date": {
      "type": "string",
      "description": "Date in YYYYMMDD format"
    }
  },
  "required": ["date"]
}
```

**Output** (JSON string):
```json
{
  "date": "20260316",
  "status": "ready",
  "broadcast_sent": 2341,
  "targeting_sent": 500,
  "auto_response_sent": 120,
  "welcome_response_sent": 15,
  "chat_sent": 45,
  "api_broadcast_sent": 2341,
  "api_push_sent": 156,
  "api_multicast_sent": 300,
  "api_reply_sent": 80
}
```

---

### Tool 9: `get_user_profile`

Get profile information of a LINE user.

| Property | Value |
|----------|-------|
| **Tier** | Pro |
| **LINE API** | `GET /v2/bot/profile/{userId}` |
| **Rate Limit** | 2,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "LINE user ID (starts with U)"
    }
  },
  "required": ["user_id"]
}
```

**Output** (JSON string):
```json
{
  "user_id": "Uf3b0a1234567890abcdef1234567890",
  "display_name": "John Doe",
  "picture_url": "https://profile.line-scdn.net/...",
  "status_message": "Hello world",
  "language": "en"
}
```

---

### Tool 10: `list_rich_menus`

List all rich menus created for this LINE OA.

| Property | Value |
|----------|-------|
| **Tier** | Pro |
| **LINE API** | `GET /v2/bot/richmenu/list` |
| **Rate Limit** | 1,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Output** (JSON string):
```json
[
  {
    "rich_menu_id": "richmenu-abc123...",
    "name": "Main Menu Q1",
    "chat_bar_text": "Tap to open menu",
    "size": { "width": 2500, "height": 1686 },
    "selected": false,
    "areas_count": 3
  }
]
```

---

### Tool 11: `create_rich_menu`

Create a new rich menu with interactive areas.

| Property | Value |
|----------|-------|
| **Tier** | Pro |
| **LINE API** | `POST /v2/bot/richmenu` |
| **Rate Limit** | 1,000 req/min (LINE) |
| **Note** | Image upload is a separate step: `POST /v2/bot/richmenu/{richMenuId}/content` |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Internal menu name"
    },
    "chat_bar_text": {
      "type": "string",
      "description": "Text shown on the chat bar button"
    },
    "areas": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "x": { "type": "integer" },
          "y": { "type": "integer" },
          "width": { "type": "integer" },
          "height": { "type": "integer" },
          "action_type": {
            "type": "string",
            "enum": ["uri", "message", "postback"]
          },
          "action_data": { "type": "string" }
        }
      },
      "description": "List of clickable areas with actions"
    }
  },
  "required": ["name", "chat_bar_text", "areas"]
}
```

**Output**: `"Rich menu created successfully. ID: {richMenuId}. Upload an image to complete setup."`

---

### Tool 12: `set_default_rich_menu`

Set a rich menu as the default for all users.

| Property | Value |
|----------|-------|
| **Tier** | Pro |
| **LINE API** | `POST /v2/bot/user/all/richmenu/{richMenuId}` |
| **Rate Limit** | 1,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "rich_menu_id": {
      "type": "string",
      "description": "Rich menu ID to set as default"
    }
  },
  "required": ["rich_menu_id"]
}
```

**Output**: `"Rich menu {rich_menu_id} set as default for all users."`

---

### Tool 13: `link_rich_menu_to_user`

Link a specific rich menu to a specific user (per-user customization).

| Property | Value |
|----------|-------|
| **Tier** | Pro |
| **LINE API** | `POST /v2/bot/user/{userId}/richmenu/{richMenuId}` |
| **Rate Limit** | 1,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "LINE user ID"
    },
    "rich_menu_id": {
      "type": "string",
      "description": "Rich menu ID to link"
    }
  },
  "required": ["user_id", "rich_menu_id"]
}
```

**Output**: `"Rich menu {rich_menu_id} linked to user {user_id}."`

---

## Tools — BUSINESS Tier ($45/mo)

### Tool 14: `create_flex_message`

Generate a LINE Flex Message JSON from a natural language description.

| Property | Value |
|----------|-------|
| **Tier** | Business |
| **LINE API** | N/A (generates JSON for use with send_broadcast/push) |
| **Note** | Leverages AI client's reasoning to build Flex JSON |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "description": {
      "type": "string",
      "description": "Natural language description of desired Flex Message, e.g. 'product card for iPhone 16, price $999, with image and buy button'"
    },
    "style": {
      "type": "string",
      "enum": ["product_card", "receipt", "booking", "menu", "custom"],
      "description": "Predefined style template. Default: 'product_card'"
    }
  },
  "required": ["description"]
}
```

**Output**: Flex Message JSON string ready to use with broadcast/push tools.

---

### Tool 15: `get_audience_insights`

Get comprehensive audience demographics and behavior insights.

| Property | Value |
|----------|-------|
| **Tier** | Business |
| **LINE API** | Multiple insight endpoints combined |
| **Rate Limit** | 1,000 req/min (LINE) |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Output** (JSON string):
```json
{
  "gender_ratio": { "male": 42, "female": 55, "unknown": 3 },
  "age_distribution": { "20-29": 25, "30-39": 35, "40-49": 20, "50+": 20 },
  "friend_growth_7d": { "added": 120, "blocked": 8, "net": 112 },
  "engagement_rate": 0.51,
  "peak_active_hours": ["18:00-20:00", "12:00-13:00"]
}
```

---

### Tool 16: `create_coupon`

Create a coupon that can be distributed to users.

| Property | Value |
|----------|-------|
| **Tier** | Business |
| **LINE API** | `POST /v2/bot/coupon` (Coupon management endpoints) |
| **Phase** | v2.0 |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Coupon name"
    },
    "description": {
      "type": "string",
      "description": "Coupon details/terms"
    },
    "expiry_date": {
      "type": "string",
      "description": "Expiry date in YYYY-MM-DD format"
    },
    "max_redemptions": {
      "type": "integer",
      "description": "Maximum number of times this coupon can be redeemed (optional, null = unlimited)"
    }
  },
  "required": ["name", "description", "expiry_date"]
}
```

**Output**: `"Coupon '{name}' created. ID: {couponId}. Expires: {expiry_date}."`

---

### Tool 17: `setup_auto_reply`

Configure keyword-based auto-reply rules for incoming messages.

| Property | Value |
|----------|-------|
| **Tier** | Business |
| **LINE API** | N/A (internal rule engine + webhook handler) |
| **Phase** | v2.0 |
| **Requires** | Webhook server running with public HTTPS URL |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "keyword": {
      "type": "string",
      "description": "Trigger word or phrase"
    },
    "response_message": {
      "type": "string",
      "description": "Auto-reply message content"
    },
    "match_type": {
      "type": "string",
      "enum": ["exact", "contains", "starts_with"],
      "description": "How to match the keyword. Default: 'contains'"
    }
  },
  "required": ["keyword", "response_message"]
}
```

**Output**: `"Auto-reply rule created. When user says '{keyword}' ({match_type}), reply with: '{response_message}'."`

---

### Tool 18: `generate_weekly_report`

Generate a comprehensive weekly performance report with AI-powered insights.

| Property | Value |
|----------|-------|
| **Tier** | Business |
| **LINE API** | Multiple insight endpoints combined |
| **Phase** | v2.0 |

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "start_date": {
      "type": "string",
      "description": "Start date in YYYYMMDD format. Defaults to 7 days ago."
    }
  }
}
```

**Output**: Formatted report including message stats, friend growth, engagement rates, top-performing messages, and AI-generated recommendations.

---

## LINE API Rate Limits Reference

| Endpoint Category | Rate Limit |
|-------------------|-----------|
| Send message (push/multicast/broadcast/narrowcast) | 100,000 req/min |
| Get profile | 2,000 req/min |
| Rich menu operations | 1,000 req/min |
| Insight endpoints | 1,000 req/min |
| Other endpoints | 2,000 req/min |

---

## Tool-to-LINE API Mapping

| # | MCP Tool | LINE API Endpoint | Method | Phase |
|---|----------|-------------------|--------|-------|
| 1 | `get_account_info` | `/v2/bot/info` | GET | MVP |
| 2 | `get_friend_count` | `/v2/bot/insight/followers?date={YYYYMMDD}` | GET | MVP |
| 3 | `get_message_quota` | `/v2/bot/message/quota` + `/quota/consumption` | GET | MVP |
| 4 | `send_broadcast` | `/v2/bot/message/broadcast` | POST | MVP |
| 5 | `send_push_message` | `/v2/bot/message/push` | POST | MVP |
| 6 | `send_multicast` | `/v2/bot/message/multicast` | POST | MVP |
| 7 | `send_narrowcast` | `/v2/bot/message/narrowcast` | POST | v1.1 |
| 8 | `get_message_stats` | `/v2/bot/insight/message/delivery?date={YYYYMMDD}` | GET | MVP |
| 9 | `get_user_profile` | `/v2/bot/profile/{userId}` | GET | MVP |
| 10 | `list_rich_menus` | `/v2/bot/richmenu/list` | GET | MVP |
| 11 | `create_rich_menu` | `/v2/bot/richmenu` | POST | v1.1 |
| 12 | `set_default_rich_menu` | `/v2/bot/user/all/richmenu/{richMenuId}` | POST | v1.1 |
| 13 | `link_rich_menu_to_user` | `/v2/bot/user/{userId}/richmenu/{richMenuId}` | POST | v1.1 |
| 14 | `create_flex_message` | N/A (internal JSON generator) | — | v1.1 |
| 15 | `get_audience_insights` | Multiple insight endpoints | GET | v1.1 |
| 16 | `create_coupon` | `/v2/bot/coupon` | POST | v2.0 |
| 17 | `setup_auto_reply` | N/A (webhook + rule engine) | — | v2.0 |
| 18 | `generate_weekly_report` | Multiple insight endpoints | GET | v2.0 |

---

*Document created: March 2026*
*Source of truth: CLAUDE.md, linewhiz-spec.md, architecture.md, PRD.md*
