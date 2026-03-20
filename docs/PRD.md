# LineWhiz — Product Requirements Document (PRD)

**Version**: 1.0
**Date**: March 2026
**Author**: Product Team
**Status**: Ready for development

---

## 1. Problem Statement

### The Problem

LINE Official Account is the backbone of business communication in Japan (95M users), Thailand (56M), and Taiwan (21M). Over 10 million businesses run LINE OAs across these markets. Yet managing a LINE OA today means one of two things:

**Option A: Click through web dashboards all day.** LINE OA Manager is free but entirely manual. Every broadcast, every rich menu change, every analytics check requires opening a browser, navigating menus, and clicking buttons. A marketing manager running 3 campaigns per week easily spends 5-8 hours on repetitive LINE OA tasks.

**Option B: Pay enterprise prices.** Tools like Crescendo Lab (MAAC) offer automation, but start at $100-300+/month with onboarding fees — pricing that locks out the 95% of LINE OA users who are SMEs, freelancers, and small agencies.

**Neither option connects to AI.** In 2026, millions of professionals already use AI assistants (Claude, ChatGPT, Cursor) daily for work. But none of these AI tools can touch LINE OA. The most they can do is draft a message — the user still has to manually copy it, open LINE OA Manager, paste it, select the audience, and click send.

### The Opportunity

The MCP (Model Context Protocol) ecosystem is growing rapidly — 18,000+ servers, 8M+ downloads, 85% month-over-month growth. Yet as of March 2026, **zero MCP servers exist for LINE's Messaging API**. This is a wide-open gap in a market with 10M+ potential business users.

### Our Thesis

> If we give AI agents direct access to LINE OA via MCP, we eliminate the manual bottleneck and unlock a workflow that's 10x faster than any existing tool — at a fraction of the cost.

---

## 2. Target Personas

### Persona A: "Yuki" — E-commerce Seller / SME Owner

| Attribute | Detail |
|-----------|--------|
| **Role** | Owner of a small e-commerce shop selling on LINE, Shopee, or own website |
| **Markets** | Thailand, Japan, Taiwan |
| **LINE OA friends** | 500 – 10,000 |
| **Tech skill** | Uses smartphone apps fluently, no coding ability |
| **AI usage** | Recently started using ChatGPT or Claude for writing product descriptions |
| **Current tools** | LINE OA Manager (free), maybe ZWIZ.AI or Zaapi |
| **Monthly budget for tools** | $10–30 |
| **Core pain** | Spends 1-2 hours/day on LINE OA: replying to customers, sending promotions, checking who opened messages. No time to learn complex automation platforms. |
| **Desired outcome** | "I want to type one sentence and have my promotion sent to the right people." |

### Persona B: "Ken" — Marketing Manager (Mid-size Company)

| Attribute | Detail |
|-----------|--------|
| **Role** | Marketing manager at a beauty clinic chain, restaurant group, or fitness brand |
| **Markets** | Japan, Thailand |
| **LINE OA friends** | 10,000 – 100,000 |
| **Tech skill** | Comfortable with digital tools, uses analytics dashboards, knows basic data concepts |
| **AI usage** | Power user of Claude or ChatGPT for campaign planning, copywriting, reporting |
| **Current tools** | LINE OA Manager + possibly Crescendo Lab or SleekFlow |
| **Monthly budget** | $30–100 |
| **Core pain** | Must produce weekly reports for management, plan campaigns across multiple channels, and constantly update rich menus for seasonal promotions. Current tools either lack AI or cost too much. |
| **Desired outcome** | "I want AI to analyze my LINE OA performance, suggest what to send next, and generate the weekly report automatically." |

### Persona C: "Alex" — Digital Marketing Agency Owner

| Attribute | Detail |
|-----------|--------|
| **Role** | Runs a digital agency managing LINE OAs for 10-50 client brands |
| **Markets** | Global (agencies serving JP/TH/TW clients) |
| **LINE OA friends** | Manages multiple accounts, each 1K–100K friends |
| **Tech skill** | High — uses AI tools daily, comfortable with APIs and developer tools |
| **AI usage** | Heavy Claude Code or Cursor user, automates everything possible |
| **Current tools** | LINE OA Manager + custom scripts + maybe Crescendo Lab for large clients |
| **Monthly budget** | $50–200 (bills clients separately) |
| **Core pain** | Switching between 20+ LINE OA accounts daily is a nightmare. Creating reports for each client takes hours. Can't scale beyond current client count without hiring more staff. |
| **Desired outcome** | "I want to manage all my clients' LINE OAs from one AI interface, generate client reports in seconds, and handle twice the accounts with the same team." |

### Who pays first? (Prioritized)

1. **Alex (Agency)** — Highest willingness to pay, clearest ROI, understands MCP/AI already
2. **Ken (Marketing Manager)** — Has budget, values AI insights, needs reporting automation
3. **Yuki (SME Owner)** — Largest volume but slowest to convert, most price-sensitive

---

## 3. User Stories

### Persona A — Yuki (SME Owner)

| ID | Story | Priority |
|----|-------|----------|
| A1 | As Yuki, I want to **send a promotional broadcast** to all my followers by just describing what I want to say, so I don't have to format and send it manually. | Must-have |
| A2 | As Yuki, I want to **check how many messages I can still send this month**, so I don't accidentally exceed my quota and get charged. | Must-have |
| A3 | As Yuki, I want to **see how many new followers I got this week**, so I know if my marketing is working. | Must-have |
| A4 | As Yuki, I want to **send a direct message to a specific customer** by describing who they are, so I can follow up on orders. | Must-have |
| A5 | As Yuki, I want AI to **create a beautiful Flex Message** from a simple description like "product card for red dress, 590 baht, with buy link", so I don't have to learn Flex Message JSON. | Nice-to-have |

### Persona B — Ken (Marketing Manager)

| ID | Story | Priority |
|----|-------|----------|
| B1 | As Ken, I want to **see delivery stats** (sent, opened, clicked) for any date, so I can measure campaign performance. | Must-have |
| B2 | As Ken, I want to **send targeted messages** to specific audience segments (by age, gender, region), so I can run personalized campaigns. | Must-have |
| B3 | As Ken, I want to **create and swap rich menus** by describing what I need, so I can update the menu for seasonal campaigns in seconds instead of hours. | Must-have |
| B4 | As Ken, I want AI to **generate a weekly performance report** covering friend growth, message engagement, and recommendations, so I don't have to compile it manually for management. | Nice-to-have |
| B5 | As Ken, I want to **get AI-powered suggestions** on the best time to send broadcasts and what content types perform best, so I can optimize campaigns data-driven. | Nice-to-have |

### Persona C — Alex (Agency)

| ID | Story | Priority |
|----|-------|----------|
| C1 | As Alex, I want to **switch between client LINE OAs** by changing a config, so I can manage all accounts from one AI workspace. | Must-have |
| C2 | As Alex, I want to **send multicast messages** to a specific list of user IDs, so I can run targeted campaigns for clients. | Must-have |
| C3 | As Alex, I want to **pull audience demographics and insights** for any client, so I can include data in strategy presentations. | Nice-to-have |
| C4 | As Alex, I want to **create coupons** and send them to targeted user segments, so I can run promotions for retail clients. | Future |
| C5 | As Alex, I want to **set up keyword-based auto-replies** for common customer questions, so my clients' OAs respond 24/7 without human staff. | Future |

---

## 4. Feature Priority Matrix

### Must-Have (MVP — Launch with these)

These 9 tools are the absolute minimum to deliver value and start charging.

| # | Tool | Tier | Story | Effort |
|---|------|------|-------|--------|
| 1 | `get_account_info` | Free | A2 | 2h |
| 2 | `get_friend_count` | Free | A3 | 2h |
| 3 | `get_message_quota` | Free | A2 | 2h |
| 4 | `send_broadcast` | Pro | A1 | 4h |
| 5 | `send_push_message` | Pro | A4 | 3h |
| 6 | `send_multicast` | Pro | C2 | 3h |
| 7 | `get_message_delivery_stats` | Pro | B1 | 3h |
| 8 | `get_user_profile` | Pro | B1 | 2h |
| 9 | `list_rich_menus` | Pro | B3 | 2h |
| — | **Auth + tier gating** | Core | All | 8h |
| — | **Usage tracking** | Core | All | 4h |
| | | | **Total** | **~35h** |

### Nice-to-Have (v1.1 — Within 2 weeks after launch)

| # | Tool | Tier | Story | Effort |
|---|------|------|-------|--------|
| 10 | `send_narrowcast` | Pro | B2 | 6h |
| 11 | `create_rich_menu` | Pro | B3 | 6h |
| 12 | `set_default_rich_menu` | Pro | B3 | 2h |
| 13 | `link_rich_menu_to_user` | Pro | B3 | 2h |
| 14 | `get_audience_insights` | Business | C3 | 6h |
| 15 | `create_flex_message` | Business | A5 | 8h |
| | | | **Total** | **~30h** |

### Future (v2.0 — Month 2-3)

| # | Tool | Tier | Story | Effort |
|---|------|------|-------|--------|
| 16 | `create_coupon` | Business | C4 | 6h |
| 17 | `setup_auto_reply` | Business | C5 | 12h |
| 18 | `generate_weekly_report` | Business | B4 | 8h |
| — | Multi-account switching | Enterprise | C1 | 10h |
| — | Webhook server for auto-reply | Business | C5 | 12h |
| — | Image upload for rich menus | Pro | B3 | 6h |
| | | | **Total** | **~54h** |

---

## 5. MVP Scope — What We Build First

### In Scope (MVP)

- 9 MCP tools (3 free + 6 pro)
- API key authentication
- Tier-based feature gating (free/pro/business)
- Daily usage tracking + rate limiting
- STDIO transport (local usage via Claude Desktop, Cursor, etc.)
- English responses by default
- Documentation (README + getting started guide)
- Listed on 3+ MCP marketplaces (Apify, MCPize, MCP.so)

### Explicitly OUT of Scope (MVP)

- HTTP/SSE remote transport (add after local STDIO is proven)
- Webhook server for receiving LINE messages (auto-reply needs this)
- Rich menu image upload (requires multipart form handling)
- Stripe billing integration (use marketplace billing first)
- Landing page (build after MVP validates demand)
- Admin dashboard / web UI (the whole point is NO UI — just AI)
- Multi-language hardcoded responses (let AI client handle it)
- Multi-account management (v2.0)

### Why this cut?

The MVP must answer one question: **"Will people actually use an MCP server to manage their LINE OA?"**

To answer that, we need:
- Enough free tools to attract users (3 read-only tools)
- Enough paid tools to justify $15/month (messaging + stats + rich menu listing)
- Working auth + billing so we can actually collect revenue

We do NOT need a beautiful landing page, webhook infrastructure, or image upload to validate demand. Those come after we confirm product-market fit.

---

## 6. Pricing

| Tier | Price | Tools | Daily Calls | Target |
|------|-------|-------|-------------|--------|
| **Free** | $0 | 3 (read-only) | 100 | Everyone — funnel entry |
| **Pro** | $15/month | 13 (messaging + menus + stats) | 5,000 | SME owners, marketers |
| **Business** | $45/month | All 18 | Unlimited | Agencies, power users |
| **Enterprise** | Custom | All + multi-account + SLA | Unlimited | Large companies |

### Pricing rationale

- **$15/month** is cheap enough that an SME owner spending 1 hour/day on manual LINE OA work would save $150+/month worth of time — 10x ROI.
- **$45/month** for agencies managing 10+ clients is a no-brainer — it replaces hours of report generation and account switching.
- Competitors: ZWIZ.AI starts at ~$15, Zaapi at ~$13, SleekFlow at ~$79, Respond.io at ~$99. Our Pro tier competes directly with ZWIZ/Zaapi on price while offering AI-native workflow they can't match.

---

## 7. Success Metrics

### North Star Metric
**Monthly Recurring Revenue (MRR)** — because this is a passive income product.

### Primary Metrics (track weekly)

| Metric | Month 1 | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|---------|----------|
| Free signups | 30 | 150 | 500 | 1,500 |
| Paying users | 0-5 | 15-30 | 50-100 | 150-400 |
| MRR | $0-75 | $225-450 | $750-1,500 | $2,250-6,000 |
| Free→Pro conversion | — | 10-15% | 15-20% | 15-20% |
| Monthly churn | — | <15% | <10% | <8% |

### Secondary Metrics (track monthly)

| Metric | Target |
|--------|--------|
| GitHub stars | 50+ by month 3 |
| MCP marketplace installs | 200+ by month 3 |
| Tool calls per user per day | 5-15 (healthy engagement) |
| Support tickets per week | <5 (product is self-serve) |
| Net Promoter Score (NPS) | >30 |

### Kill Criteria (when to pivot)

If after **3 months** we see:
- < 50 total free users AND
- < 5 paying users AND
- No organic word-of-mouth (0 mentions on Reddit/Twitter/communities)

Then: **Pivot** — either to a different LINE market (Japan focus) or to a different MCP server entirely (Shopee/Stripe/etc). Do not continue investing time if all three conditions are met.

If we have users but no revenue (many free, few paid) → adjust pricing or feature gating, don't kill the product.

---

## 8. Technical Constraints

### LINE API Constraints
- Broadcast consumes message quota — LINE charges beyond free tier (pricing varies by country/plan)
- Rich menu creation requires image upload (separate API call with multipart form)
- Narrowcast audience must have 100+ targetable users to send
- Webhook events (for auto-reply) require a publicly accessible HTTPS URL
- Rate limits: 100K msg/min (generous), 2K profile/min, 1K richmenu/min

### MCP Constraints
- STDIO transport: server runs locally on user's machine alongside their AI client
- HTTP/SSE transport: server runs remotely, user connects via URL (better for marketplace distribution)
- MCP tools can only return text/JSON — no binary data (images must be URLs)
- No persistent state between tool calls (each call is independent)

### Business Constraints
- MVP must be buildable in 4-6 weeks with AI tools only (no hiring)
- Hosting cost must stay under $20/month until revenue covers it
- Must work with Claude Desktop, Cursor, and Antigravity (the three AI tools user already has)

---

## 9. User Flow (MVP)

### First-time Setup (one-time, 5 minutes)

```
User has Claude Desktop + LINE OA
         │
         ▼
1. Get LINE Channel Access Token
   (from developers.line.biz → Messaging API tab)
         │
         ▼
2. Install LineWhiz
   Option A: npx linewhiz (if published on npm)
   Option B: uvx linewhiz (if published on PyPI)
   Option C: git clone + uv run
         │
         ▼
3. Add to claude_desktop_config.json:
   {
     "mcpServers": {
       "linewhiz": {
         "command": "uvx",
         "args": ["linewhiz"],
         "env": {
           "LINE_CHANNEL_ACCESS_TOKEN": "xxx",
           "LINE_CHANNEL_SECRET": "xxx"
         }
       }
     }
   }
         │
         ▼
4. Restart Claude Desktop
         │
         ▼
5. Type: "How many friends does my LINE OA have?"
   → LineWhiz responds with follower count
   → User is delighted
```

### Daily Usage Flow

```
User opens Claude Desktop
         │
         ▼
"Send a broadcast to all my followers:
 New menu this week! Grilled salmon set
 only $12.99 until Friday."
         │
         ▼
Claude calls LineWhiz send_broadcast tool
         │
         ▼
LineWhiz → LINE API → message sent
         │
         ▼
"Broadcast sent successfully to all 2,847 friends."
         │
         ▼
"Now show me the delivery stats for yesterday."
         │
         ▼
Claude calls get_message_delivery_stats
         │
         ▼
LineWhiz → LINE API → returns stats
         │
         ▼
Claude presents: "Yesterday's broadcast reached
2,341 people (82% delivery rate), 1,205 opened
(51%), 287 clicked (12%). This is above average."
```

---

## 10. Development Phases

### Phase 1: MVP (Week 1-4)
- Build 9 must-have tools
- Auth + tier gating
- Local STDIO transport
- README + docs
- Test with real LINE OA
- List on marketplaces

### Phase 2: Growth (Week 5-8)
- Add 6 nice-to-have tools (narrowcast, rich menu CRUD, flex message, insights)
- HTTP/SSE remote transport (easier for users who don't want local install)
- Stripe billing integration
- Landing page

### Phase 3: Scale (Month 3-6)
- Add 6 future tools (coupon, auto-reply, weekly report)
- Multi-account management
- Webhook server for incoming messages
- Japan market localization push
- Partner with LINE OA educators/influencers

### Phase 4: Platform (Month 6+)
- Open plugin system (let others build tools on top of LineWhiz)
- Shopee/Lazada MCP integration (cross-platform commerce)
- Enterprise features (SSO, audit log, team management)
- Consider Japan/Taiwan dedicated marketing

---

## 11. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Low MCP adoption globally | Medium | High | Free tier as funnel, educate via content marketing |
| LINE API breaking changes | Medium | Medium | Pin API version, monitor LINE Developer changelog |
| LINE builds native AI features | Medium | Medium | Our value is MCP-native (works in Claude/Cursor), LINE's will be LINE-only |
| ZWIZ.AI adds MCP support | Low | Medium | First-mover advantage + faster iteration as solo founder |
| Users don't want to pay | Medium | Medium | Generous free tier, clear value gap between free and pro |
| MCP marketplace doesn't drive traffic | Medium | Low | Diversify: GitHub, Reddit, Indie Hackers, direct marketing |
| Security incident (token leak) | Low | Critical | Never store tokens in DB, encrypt in transit, security audit |

---

## 12. Open Questions (to resolve during build)

1. **STDIO vs HTTP first?** STDIO is easier to build but requires local install. HTTP/SSE is easier for users but more infra work. → **Decision: STDIO first** (less infra, validates core value).

2. **Marketplace billing or own billing?** Apify/MCPize handle billing but take 15-25% cut. Own Stripe billing is 100% revenue but more work. → **Decision: Marketplace billing for MVP**, own billing later.

3. **PyPI or npm?** Python SDK is easier to build with, but npm has larger MCP community. → **Decision: Python (PyPI) first**, TypeScript port later if demand exists.

4. **Rich menu image upload?** Requires multipart form upload to LINE API, adds complexity. → **Decision: Defer to v1.1**. MVP lists and links existing menus only.

---

## Appendix: Competitive Quick Reference

| Tool | Price | AI-native | MCP | LINE-focused | SME-friendly |
|------|-------|-----------|-----|-------------|-------------|
| LINE OA Manager | Free | No | No | Yes | Yes |
| ZWIZ.AI | ~$15/mo | Partial | No | Yes | Yes |
| Zaapi | ~$13/mo | Partial | No | Partial | Yes |
| BOTNOI | Points-based | Partial | No | Yes | Yes |
| Crescendo Lab | $100+/mo | Partial | No | Yes | No |
| SleekFlow | ~$79/mo | Partial | No | Partial | No |
| Respond.io | ~$99/mo | Partial | No | Partial | No |
| **LineWhiz** | **$0-45/mo** | **Yes** | **Yes** | **Yes** | **Yes** |

---

*Next step: Copy this file to /docs/PRD.md in the LineWhiz repo*
*Then proceed to Phase 2: Architecture & Design (see ai-workflow-playbook.md)*
