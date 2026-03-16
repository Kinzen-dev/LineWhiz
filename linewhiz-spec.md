# LineWhiz — Technical Specification

## Product: LINE Official Account Management MCP Server
## Codename: `linewhiz`
## Version: 1.0 MVP Spec
## Target Market: ธุรกิจไทย/SEA ที่ใช้ LINE Official Account

---

## 1. Executive Summary

### Problem
ธุรกิจไทยกว่า 2 ล้านรายใช้ LINE Official Account แต่การจัดการยังทำผ่าน LINE OA Manager ซึ่งเป็น web UI ที่ต้องคลิกเอง ทำ automation ยาก ไม่มี AI integration

### Solution
MCP Server ที่ให้ AI agents (Claude, ChatGPT, Cursor, Antigravity) จัดการ LINE OA ได้ทั้งหมดผ่านคำสั่งภาษาธรรมชาติ — broadcast ข้อความ, จัดการ rich menu, ดู analytics, ตอบลูกค้าอัตโนมัติ

### Revenue Target
- Month 1-3: ฿15,000-50,000/เดือน (30-100 users @ ฿500/mo)
- Month 6-12: ฿100,000-300,000/เดือน (200-600 users)
- Year 2+: ฿500,000+/เดือน (scaling + enterprise tier)

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   MCP Clients                        │
│  Claude Desktop │ Claude Code │ Cursor │ Antigravity │
└────────┬────────────────┬──────────────┬─────────────┘
         │    MCP Protocol (JSON-RPC)    │
         ▼                               ▼
┌─────────────────────────────────────────────────────┐
│              linewhiz server                      │
│                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Auth     │ │ Rate     │ │ Usage    │            │
│  │ Layer    │ │ Limiter  │ │ Tracker  │            │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       │            │            │                    │
│  ┌────▼────────────▼────────────▼────────┐          │
│  │           Tool Router                  │          │
│  │  messaging │ richmenu │ insight │ ...  │          │
│  └────────────────┬──────────────────────┘          │
└───────────────────┼──────────────────────────────────┘
                    │ HTTPS
                    ▼
         ┌─────────────────────┐
         │  LINE Platform API  │
         │  api.line.me/v2/bot │
         └─────────────────────┘
```

### Tech Stack
- **Language**: Python 3.11+ (เร็วในการ prototype, มี LINE SDK official)
- **MCP SDK**: `mcp` (official Python SDK) v1.2+
- **LINE SDK**: `line-bot-sdk-python` (official)
- **Auth**: API key + JWT
- **Database**: SQLite (MVP) → PostgreSQL (scale)
- **Hosting**: Docker on Railway / Fly.io / Apify
- **Billing**: Stripe (global) หรือ PromptPay (Thai)

---

## 3. Tool Definitions (MCP Tools)

### Tier: FREE (ดึงคนเข้ามาใช้)

#### Tool 1: `get_account_info`
```python
@mcp.tool()
async def get_account_info() -> str:
    """Get LINE Official Account information including
    bot name, friend count, and plan details."""
```
- **Input**: ไม่มี (ใช้ channel token ที่ config ไว้)
- **Output**: Account name, friend count, plan type, message quota
- **LINE API**: `GET /v2/bot/info`

#### Tool 2: `get_friend_count`
```python
@mcp.tool()
async def get_friend_count(date: str = "today") -> str:
    """Get number of friends (followers) on a specific date.
    Date format: YYYYMMDD or 'today'"""
```
- **LINE API**: `GET /v2/bot/insight/followers`

#### Tool 3: `get_message_quota`
```python
@mcp.tool()
async def get_message_quota() -> str:
    """Get remaining message quota for this month.
    Shows total quota, used, and remaining."""
```
- **LINE API**: `GET /v2/bot/message/quota` + `/quota/consumption`

---

### Tier: PRO ฿500/เดือน (core value)

#### Tool 4: `send_broadcast`
```python
@mcp.tool()
async def send_broadcast(
    message: str,
    message_type: str = "text",
    schedule_time: str | None = None
) -> str:
    """Send a broadcast message to ALL friends.
    
    Args:
        message: Text content or Flex Message JSON
        message_type: 'text', 'image', 'flex', 'template'
        schedule_time: ISO8601 datetime for scheduled send (optional)
    """
```
- **LINE API**: `POST /v2/bot/message/broadcast`
- **Message types**: text, image, video, audio, flex, template
- **Limit**: ตาม plan ของ LINE OA (free plan = 200/month)

#### Tool 5: `send_push_message`
```python
@mcp.tool()
async def send_push_message(
    user_id: str,
    message: str,
    message_type: str = "text"
) -> str:
    """Send a direct message to a specific user.
    
    Args:
        user_id: LINE user ID
        message: Message content
        message_type: 'text', 'image', 'flex', 'template'
    """
```
- **LINE API**: `POST /v2/bot/message/push`

#### Tool 6: `send_multicast`
```python
@mcp.tool()
async def send_multicast(
    user_ids: list[str],
    message: str,
    message_type: str = "text"
) -> str:
    """Send a message to multiple specific users (max 500).
    
    Args:
        user_ids: List of LINE user IDs (max 500)
        message: Message content
        message_type: 'text', 'image', 'flex', 'template'
    """
```
- **LINE API**: `POST /v2/bot/message/multicast`

#### Tool 7: `send_narrowcast`
```python
@mcp.tool()
async def send_narrowcast(
    message: str,
    gender: str | None = None,
    age_range: str | None = None,
    area: str | None = None,
    message_type: str = "text"
) -> str:
    """Send targeted messages to specific audience segments.
    
    Args:
        message: Message content
        gender: 'male', 'female', or None (all)
        age_range: e.g. '20-30', '30-40'
        area: Region/prefecture code
        message_type: 'text', 'image', 'flex', 'template'
    """
```
- **LINE API**: `POST /v2/bot/message/narrowcast`

#### Tool 8: `get_message_stats`
```python
@mcp.tool()
async def get_message_stats(date: str) -> str:
    """Get delivery statistics for messages sent on a specific date.
    Returns: sent, delivered, opened, clicked counts.
    
    Args:
        date: YYYYMMDD format
    """
```
- **LINE API**: `GET /v2/bot/insight/message/delivery`
- **Returns**: จำนวนส่ง, delivered, opened, clicked, video/audio played

#### Tool 9: `get_user_profile`
```python
@mcp.tool()
async def get_user_profile(user_id: str) -> str:
    """Get profile information of a LINE user.
    Returns display name, profile picture URL, status message.
    
    Args:
        user_id: LINE user ID
    """
```
- **LINE API**: `GET /v2/bot/profile/{userId}`

#### Tool 10: `list_rich_menus`
```python
@mcp.tool()
async def list_rich_menus() -> str:
    """List all rich menus created for this LINE OA.
    Returns menu ID, name, size, and link status."""
```
- **LINE API**: `GET /v2/bot/richmenu/list`

#### Tool 11: `create_rich_menu`
```python
@mcp.tool()
async def create_rich_menu(
    name: str,
    chat_bar_text: str,
    areas: list[dict]
) -> str:
    """Create a new rich menu with interactive areas.
    
    Args:
        name: Menu name (internal)
        chat_bar_text: Text shown on chat bar
        areas: List of clickable areas with actions
               [{"x":0, "y":0, "width":800, "height":270,
                 "action_type": "uri", "action_data": "https://..."}]
    """
```
- **LINE API**: `POST /v2/bot/richmenu`
- **Note**: ต้อง upload image แยก → `POST /v2/bot/richmenu/{richMenuId}/content`

#### Tool 12: `set_default_rich_menu`
```python
@mcp.tool()
async def set_default_rich_menu(rich_menu_id: str) -> str:
    """Set a rich menu as the default for all users.
    
    Args:
        rich_menu_id: Rich menu ID to set as default
    """
```
- **LINE API**: `POST /v2/bot/user/all/richmenu/{richMenuId}`

#### Tool 13: `link_rich_menu_to_user`
```python
@mcp.tool()
async def link_rich_menu_to_user(
    user_id: str,
    rich_menu_id: str
) -> str:
    """Link a specific rich menu to a specific user.
    Enables per-user rich menu customization.
    
    Args:
        user_id: LINE user ID
        rich_menu_id: Rich menu ID to link
    """
```
- **LINE API**: `POST /v2/bot/user/{userId}/richmenu/{richMenuId}`

---

### Tier: BUSINESS ฿1,500/เดือน (advanced automation)

#### Tool 14: `create_flex_message`
```python
@mcp.tool()
async def create_flex_message(
    description: str,
    style: str = "product_card"
) -> str:
    """Generate a LINE Flex Message JSON from natural language description.
    AI creates beautiful, interactive message layouts.
    
    Args:
        description: What the flex message should show
                     e.g. "product card for iPhone 16, price 35900 baht,
                           with image, buy button linking to shop"
        style: 'product_card', 'receipt', 'booking', 'menu', 'custom'
    """
```
- **Note**: ใช้ AI ของ MCP client สร้าง Flex Message JSON → ส่งผ่าน broadcast/push
- **Value-add**: ไม่ต้องเขียน Flex JSON เอง แค่บอกเป็นภาษาธรรมชาติ

#### Tool 15: `get_audience_insights`
```python
@mcp.tool()
async def get_audience_insights() -> str:
    """Get comprehensive audience demographics and behavior insights.
    Returns: gender ratio, age distribution, active hours,
    friend add/block trends, message engagement rates."""
```
- **LINE API**: Multiple insight endpoints combined
- **Value**: วิเคราะห์ audience ได้โดยไม่ต้องดูหลายหน้า

#### Tool 16: `create_coupon`
```python
@mcp.tool()
async def create_coupon(
    name: str,
    description: str,
    expiry_date: str,
    max_redemptions: int | None = None
) -> str:
    """Create a coupon that can be sent to users.
    
    Args:
        name: Coupon name
        description: Coupon details
        expiry_date: YYYY-MM-DD format
        max_redemptions: Maximum number of redemptions
    """
```
- **LINE API**: Coupon management endpoints

#### Tool 17: `setup_auto_reply`
```python
@mcp.tool()
async def setup_auto_reply(
    keyword: str,
    response_message: str,
    match_type: str = "contains"
) -> str:
    """Configure auto-reply rules for incoming messages.
    When a user sends a message matching the keyword,
    automatically reply with the configured response.
    
    Args:
        keyword: Trigger word/phrase
        response_message: Auto-reply message content
        match_type: 'exact', 'contains', 'starts_with'
    """
```
- **Implementation**: Webhook handler + rule engine
- **Requires**: Webhook server running alongside MCP server

#### Tool 18: `generate_weekly_report`
```python
@mcp.tool()
async def generate_weekly_report(
    start_date: str | None = None
) -> str:
    """Generate a comprehensive weekly performance report.
    Includes: message stats, friend growth, engagement rates,
    top performing messages, and AI recommendations.
    
    Args:
        start_date: YYYYMMDD (defaults to 7 days ago)
    """
```
- **Combines**: Multiple insight APIs + AI analysis
- **Output**: Formatted report with charts description + actionable insights

---

## 4. Project Structure

```
linewhiz/
├── src/
│   ├── server.py              # MCP server entry point
│   ├── config.py              # Configuration management
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── api_keys.py        # API key validation
│   │   └── tiers.py           # Free/Pro/Business tier logic
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── messaging.py       # send_broadcast, send_push, etc.
│   │   ├── richmenu.py        # rich menu management tools
│   │   ├── insights.py        # analytics and reporting tools
│   │   ├── audience.py        # user profile and segmentation
│   │   ├── coupons.py         # coupon management
│   │   └── automation.py      # auto-reply, scheduled messages
│   ├── services/
│   │   ├── __init__.py
│   │   ├── line_api.py        # LINE API client wrapper
│   │   ├── flex_builder.py    # Flex Message generator
│   │   └── report_builder.py  # Weekly report generator
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py            # User/subscription models
│   │   └── usage.py           # Usage tracking models
│   └── db/
│       ├── __init__.py
│       └── database.py        # SQLite/PostgreSQL connection
├── tests/
│   ├── test_messaging.py
│   ├── test_richmenu.py
│   └── test_insights.py
├── scripts/
│   ├── setup_webhook.py       # Webhook server setup
│   └── seed_demo.py           # Demo data for testing
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
├── LICENSE
└── .env.example
```

---

## 5. Configuration & Authentication

### User Configuration (claude_desktop_config.json)
```json
{
  "mcpServers": {
    "line-oa": {
      "command": "uvx",
      "args": ["linewhiz"],
      "env": {
        "LINE_CHANNEL_ACCESS_TOKEN": "your_token_here",
        "LINE_CHANNEL_SECRET": "your_secret_here",
        "LINE_OA_MCP_API_KEY": "your_mcp_api_key_here"
      }
    }
  }
}
```

### Remote (HTTP/SSE) Configuration
```json
{
  "mcpServers": {
    "line-oa": {
      "type": "url",
      "url": "https://linewhiz.fly.dev/sse",
      "headers": {
        "Authorization": "Bearer your_mcp_api_key_here",
        "X-Line-Token": "your_line_token_here"
      }
    }
  }
}
```

### Tier-based Feature Gating
```python
TIER_FEATURES = {
    "free": {
        "tools": ["get_account_info", "get_friend_count", "get_message_quota"],
        "daily_calls": 100,
        "max_broadcast_per_day": 0,
    },
    "pro": {
        "tools": [
            "get_account_info", "get_friend_count", "get_message_quota",
            "send_broadcast", "send_push_message", "send_multicast",
            "send_narrowcast", "get_message_stats", "get_user_profile",
            "list_rich_menus", "create_rich_menu", "set_default_rich_menu",
            "link_rich_menu_to_user",
        ],
        "daily_calls": 5000,
        "max_broadcast_per_day": 10,
    },
    "business": {
        "tools": "__all__",
        "daily_calls": -1,  # unlimited
        "max_broadcast_per_day": -1,
    },
}
```

---

## 6. LINE API Reference Quick Map

| MCP Tool | LINE API Endpoint | HTTP Method |
|----------|-------------------|-------------|
| get_account_info | /v2/bot/info | GET |
| get_friend_count | /v2/bot/insight/followers | GET |
| get_message_quota | /v2/bot/message/quota | GET |
| send_broadcast | /v2/bot/message/broadcast | POST |
| send_push_message | /v2/bot/message/push | POST |
| send_multicast | /v2/bot/message/multicast | POST |
| send_narrowcast | /v2/bot/message/narrowcast | POST |
| get_message_stats | /v2/bot/insight/message/delivery | GET |
| get_user_profile | /v2/bot/profile/{userId} | GET |
| list_rich_menus | /v2/bot/richmenu/list | GET |
| create_rich_menu | /v2/bot/richmenu | POST |
| set_default_rich_menu | /v2/bot/user/all/richmenu/{id} | POST |
| link_rich_menu_to_user | /v2/bot/user/{userId}/richmenu/{id} | POST |
| create_coupon | /v2/bot/coupon | POST |

**Base URL**: `https://api.line.me`
**Auth Header**: `Authorization: Bearer {channel_access_token}`

---

## 7. Pricing Model

### Free Tier
- 3 read-only tools (account info, friend count, quota)
- 100 API calls/day
- No messaging capabilities
- **Purpose**: ดึงคนเข้ามาทดลอง

### Pro Tier — ฿500/เดือน (~$15 USD)
- 13 tools (all messaging + rich menu + insights)
- 5,000 API calls/day
- 10 broadcasts/day
- Email support
- **Target**: SME, ร้านค้าออนไลน์, คลินิก, ร้านอาหาร

### Business Tier — ฿1,500/เดือน (~$45 USD)
- All 18 tools
- Unlimited API calls
- Unlimited broadcasts
- Flex Message AI generator
- Auto-reply automation
- Weekly AI report
- Priority support + LINE group
- **Target**: Agency, enterprise, multi-location business

### Enterprise (custom)
- Multi-account management
- Custom tool development
- Dedicated support
- SLA guarantee
- **Target**: Large corporations, LINE OA agencies

---

## 8. Development Timeline (6-week MVP)

### Week 1: Foundation
- [ ] Setup Python project with MCP SDK
- [ ] Implement LINE API client wrapper (line_api.py)
- [ ] Create basic auth (API key validation)
- [ ] Implement Tool 1-3 (free tier: get_account_info, friend_count, quota)
- [ ] Test with Claude Desktop locally

### Week 2: Core Messaging
- [ ] Implement Tool 4-6 (broadcast, push, multicast)
- [ ] Implement Tool 7 (narrowcast with audience targeting)
- [ ] Add message type support (text, image, flex)
- [ ] Add usage tracking (count API calls per user)
- [ ] Write unit tests for messaging tools

### Week 3: Rich Menu & Insights
- [ ] Implement Tool 8-9 (message stats, user profile)
- [ ] Implement Tool 10-13 (rich menu CRUD + linking)
- [ ] Build combined audience insights (Tool 15)
- [ ] Add tier-based feature gating

### Week 4: Premium Features
- [ ] Implement Tool 14 (Flex Message AI generator)
- [ ] Implement Tool 16 (coupon creation)
- [ ] Implement Tool 18 (weekly report generator)
- [ ] Setup webhook server for auto-reply (Tool 17)

### Week 5: Deploy & Billing
- [ ] Dockerize the application
- [ ] Deploy to Railway / Fly.io
- [ ] Setup Stripe billing (or PromptPay for Thai market)
- [ ] Create landing page (Thai + English)
- [ ] Write documentation + README
- [ ] Submit to MCP marketplaces (Apify, MCPize, MCP.so)

### Week 6: Launch & Iterate
- [ ] Soft launch to 10-20 beta users
- [ ] Collect feedback
- [ ] Fix bugs and edge cases
- [ ] Write blog post / tutorial
- [ ] Post on Thai dev communities (Thai Programmer FB group, Pantip)
- [ ] Official launch

---

## 9. Distribution Channels

### Primary (MCP Marketplaces)
1. **Apify Store** — pay-per-event model, 36K+ dev community
2. **MCPize** — subscription model, 85% revenue share
3. **MCP.so** — listing for visibility (18K+ servers)
4. **LobeHub MCP Marketplace** — growing community

### Secondary (Direct)
5. **Own website** (linewhiz.com) — 100% revenue
6. **GitHub** — open-source free tier for trust/SEO
7. **npm / PyPI** — easy installation

### Thai Market Specific
8. **Thai Programmer Facebook Group** (200K+ members)
9. **LINE Developers Thailand Community**
10. **Pantip (Technopolis forum)**
11. **Thai startup/SME communities**

---

## 10. Competitive Landscape

| Competitor | Type | Weakness | Our Advantage |
|------------|------|----------|---------------|
| LINE OA Manager | Web UI | Manual, no AI, no automation | AI-powered, natural language |
| Manychat (LINE) | Chatbot | Expensive, complex setup | Simpler, MCP-native |
| Amity (LINE CRM) | SaaS | Enterprise pricing | SME-friendly pricing |
| Custom LINE bots | DIY | Requires developer | No-code via AI |
| **No MCP competitor** | — | — | **First mover in MCP for LINE** |

---

## 11. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LINE API changes | Medium | High | Version pinning, monitoring LINE changelog |
| LINE rate limits | Medium | Medium | Implement queue + retry logic, respect limits |
| Low adoption | Medium | High | Free tier as funnel, Thai community marketing |
| MCP protocol changes | Low | Medium | Follow MCP spec updates, use official SDK |
| Security (token leak) | Low | Critical | Encrypt tokens at rest, never log tokens |
| Competition enters | Medium | Medium | First mover advantage, rapid iteration |

---

## 12. Success Metrics

### Month 1
- 50+ free tier signups
- 10+ Pro tier paying users
- Revenue: ฿5,000+/month

### Month 3
- 200+ free tier users
- 50+ Pro tier users
- 5+ Business tier users
- Revenue: ฿32,500+/month

### Month 6
- 500+ free tier users
- 150+ Pro tier users
- 20+ Business tier users
- Revenue: ฿105,000+/month
- Break-even on development time

### Month 12
- 1,000+ free tier users
- 300+ Pro tier users
- 50+ Business tier users
- Revenue: ฿225,000+/month
- Passive income achieved (maintenance only)

---

## 13. Example Usage Scenarios

### Scenario 1: ร้านอาหารส่ง menu ประจำวัน
```
User: "broadcast ข้อความวันนี้ว่า เมนูพิเศษวันนี้
ข้าวมันไก่ 59 บาท ส้มตำปลาร้า 49 บาท
พร้อมส่งรูป menu จาก URL https://example.com/menu.jpg"

Claude: [calls send_broadcast with image + text message]
→ "ส่ง broadcast สำเร็จ ไปยัง friends ทั้งหมด 2,847 คน"
```

### Scenario 2: คลินิกเสริมความงาม ดู engagement
```
User: "สรุปผลการส่งข้อความสัปดาห์ที่ผ่านมาให้หน่อย"

Claude: [calls get_message_stats for last 7 days]
→ "สรุปสัปดาห์นี้:
   ส่งทั้งหมด: 5 ข้อความ
   เปิดอ่าน: 78% (สูงกว่าค่าเฉลี่ย)
   คลิก: 23%
   ข้อความที่ perform ดีที่สุด: โปรโมชั่นวันแม่
   แนะนำ: ควรส่งข้อความช่วง 18:00-20:00 เพราะ engagement สูงสุด"
```

### Scenario 3: Agency จัดการหลาย rich menu
```
User: "สร้าง rich menu ใหม่ชื่อ 'เมนูหลัก Q2'
มี 3 ปุ่ม: สินค้าใหม่ (ลิงก์ shop), โปรโมชั่น (ลิงก์ promo),
ติดต่อเรา (เปิดแชท) แล้วตั้งเป็น default"

Claude: [calls create_rich_menu → set_default_rich_menu]
→ "สร้าง rich menu 'เมนูหลัก Q2' สำเร็จ (ID: richmenu-xxx)
   ตั้งเป็น default แล้ว users ทุกคนจะเห็น menu ใหม่"
```

---

## Appendix A: LINE API Rate Limits

| Endpoint | Rate Limit |
|----------|-----------|
| Send message (push/multicast/broadcast) | 100,000 requests/min |
| Get profile | 2,000 requests/min |
| Rich menu operations | 1,000 requests/min |
| Insight endpoints | 1,000 requests/min |
| Other endpoints | 2,000 requests/min |

## Appendix B: Required LINE Permissions

To use all features, the LINE OA needs:
1. **Messaging API enabled** (via LINE Developers Console)
2. **Channel Access Token** (long-lived or stateless)
3. **Webhook URL** configured (for auto-reply feature)
4. **LINE OA Plan**: Communicate plan or higher (for push messages)

---

*Document created: March 2026*
*Author: AI Product Spec Generator*
*Status: Ready for development*
