# LineWhiz — AI Workflow Playbook
## "ใครทำอะไร" ทุก step ตั้งแต่เริ่มจนถึง passive income

---

> **วิธีใช้เอกสารนี้**: เปิดไว้ตลอด ทำตามทีละ phase
> ทุก task บอกชัดเจนว่า (1) AI ตัวไหนทำ (2) prompt อะไร (3) output อะไร (4) ส่งต่อไปไหน
> 🧑 = คุณทำเอง | 🤖 = AI ทำให้ | ⏭️ = ส่ง output ไปต่อที่ไหน

---

## PHASE 0: Setup (วันที่ 1) — คุณทำเอง

ทั้งหมดนี้ AI ทำแทนไม่ได้ ต้องใช้ account จริงของคุณ

### 0.1 🧑 สมัคร LINE Developers Console
- ไป https://developers.line.biz/
- Login ด้วย LINE account ส่วนตัว
- สร้าง Provider → สร้าง Messaging API Channel
- จดไว้: **Channel Access Token** + **Channel Secret**

### 0.2 🧑 เตรียม AI Tools
- ✅ Claude Pro/Max (Chat + Cowork + Code)
- ✅ ChatGPT Plus
- ✅ Cursor Pro
- ✅ Google Antigravity (free)
- ✅ GitHub account (สำหรับ repo)

### 0.3 🧑 สร้าง GitHub Repo
- ชื่อ repo: `linewhiz` (หรือชื่อ product)
- Private repo
- Clone ลงเครื่อง

### 0.4 🧑 สมัคร Deploy Platform
- สมัคร Railway.app หรือ Fly.io (สำหรับ host server)
- สมัคร Stripe (สำหรับ billing) — หรือ Lemon Squeezy ถ้าไม่อยากจัดการ VAT

---

## PHASE 1: Discovery & Validation (สัปดาห์ที่ 1)

### 1.1 🤖 Claude Chat — วิจัย competitor และ validate idea
```
PROMPT:
"ช่วยวิเคราะห์ตลาด LINE OA management tools ในไทย ให้ครบ:
1. มี tool อะไรบ้างที่ช่วยจัดการ LINE OA อยู่แล้ว (ทั้ง free และ paid)
2. แต่ละตัวมีจุดแข็ง/จุดอ่อนอะไร
3. ราคาเท่าไหร่
4. pain point ที่ยังไม่มีใครแก้ได้
5. ใครคือ target customer ที่ยินดีจ่ายเงิน
วิเคราะห์แบบตรงไปตรงมา ไม่ต้อง sugarcoat"
```
**Output ที่ได้**: Market analysis document
**⏭️ ส่งต่อ**: เก็บไว้ใน `/docs/market-analysis.md` ใน repo

### 1.2 🤖 Claude Chat — เขียน PRD (Product Requirement Document)
```
PROMPT:
"จาก market analysis ที่วิเคราะห์มา + technical spec ที่มีอยู่
(แนบ linewhiz-spec.md)
ช่วยเขียน PRD ให้สมบูรณ์:
- Problem statement
- Target persona 3 แบบ (SME owner, marketer, agency)
- User stories สำหรับแต่ละ persona
- Feature priority (must-have / nice-to-have / future)
- Success metrics
- MVP scope (ตัด feature ที่ไม่จำเป็นสำหรับ launch ออก)"
```
**Output ที่ได้**: PRD document
**⏭️ ส่งต่อ**: เก็บไว้ใน `/docs/PRD.md`

### 1.3 🤖 ChatGPT — สร้าง Landing Page Mockup
```
PROMPT:
"สร้างรูป mockup ของ landing page สำหรับ product ชื่อ [ชื่อ product]
ซึ่งเป็น AI-powered LINE OA management tool
ออกแบบ hero section ที่แสดง:
- หน้าจอ Claude Desktop กำลังสั่ง broadcast ข้อความ LINE
- Dashboard แสดง analytics
- สไตล์ modern, สี green (LINE) + dark
ทำ 2 แบบ: แบบ minimal และแบบ feature-rich"
```
**Output ที่ได้**: 2 mockup images
**⏭️ ส่งต่อ**: เก็บไว้ใน `/assets/` สำหรับทำ landing page จริง

### 1.4 🧑 Validate demand (คุณทำเอง)
- สร้าง landing page ง่ายๆ (ใช้ Carrd.co หรือ Framer)
- ใส่ mockup + รายละเอียด + ปุ่ม "สนใจ ลงชื่อรอ"
- โพสต์ใน Thai Programmer FB Group, LINE Developer TH
- **เป้าหมาย: 20+ signups ใน 1 สัปดาห์ = ไฟเขียวไปต่อ**

---

## PHASE 2: Architecture & Design (สัปดาห์ที่ 2)

### 2.1 🤖 Claude Chat — ออกแบบ System Architecture
```
PROMPT:
"จาก PRD และ technical spec ที่มี
(แนบ PRD.md + linewhiz-spec.md)

ออกแบบ system architecture ให้ละเอียด:
1. Component diagram (server, auth, billing, LINE API, database)
2. Data flow สำหรับ 3 scenarios หลัก:
   - User ส่ง broadcast ผ่าน Claude
   - User ดู analytics
   - Auto-reply เมื่อลูกค้า chat เข้ามา
3. Database schema (users, api_keys, usage_logs, subscriptions)
4. Auth flow (API key validation → tier check → rate limit)
5. Error handling strategy
6. สร้างเป็น CLAUDE.md ที่ Claude Code จะอ่านตอน develop"
```
**Output ที่ได้**: Architecture doc + CLAUDE.md
**⏭️ ส่งต่อ**: ใส่ `CLAUDE.md` ไว้ root ของ repo → Claude Code จะอ่านเอง

### 2.2 🤖 Cowork — สร้างเอกสาร Design จริง
```
TASK (Cowork):
"อ่านไฟล์ใน /docs/ folder ทั้งหมด
แล้วสร้างไฟล์ต่อไปนี้:
1. /docs/API-SPEC.md — API specification ของ MCP tools ทั้ง 18 ตัว
2. /docs/DATABASE-SCHEMA.sql — SQL schema สำหรับ SQLite
3. /docs/DEPLOYMENT-GUIDE.md — วิธี deploy ทุก step
บันทึกลงใน /docs/ folder"
```
**Output ที่ได้**: 3 documentation files
**⏭️ ส่งต่อ**: อยู่ใน repo พร้อมใช้

### 2.3 🤖 Antigravity — Scaffold Project Structure
```
PROMPT (Antigravity Agent Manager):
"สร้าง Python project structure สำหรับ MCP server ชื่อ linewhiz
ตาม spec ใน CLAUDE.md

สร้าง:
- pyproject.toml (dependencies: mcp>=1.2, httpx, line-bot-sdk, pydantic)
- src/ folder structure ตาม spec
- Dockerfile
- docker-compose.yml
- .env.example
- tests/ folder with pytest setup
- README.md

ใช้ Opus model, อ่าน CLAUDE.md ก่อนเริ่ม"
```
**Output ที่ได้**: Complete project scaffold
**⏭️ ส่งต่อ**: Push to GitHub → พร้อมให้ Cursor/Claude Code เข้าทำงาน

**💰 TOKEN SAVINGS**: Antigravity ทำ scaffold ฟรี ไม่กิน Claude token

---

## PHASE 3: Development (สัปดาห์ที่ 3-4)

### 3.1 🤖 Antigravity — Build Free Tier Tools (3 tools)
```
PROMPT (Agent 1 of 3):
"Implement free tier tools ใน src/tools/insights.py:
- get_account_info
- get_friend_count  
- get_message_quota

ใช้ LINE API endpoints ตามที่ระบุใน CLAUDE.md
เขียน tests ใน tests/test_insights.py
ดู server.py ที่มีอยู่แล้วเป็นตัวอย่าง"
```

### 3.2 🤖 Antigravity — Build Messaging Tools (4 tools) [parallel]
```
PROMPT (Agent 2 of 3, run parallel):
"Implement messaging tools ใน src/tools/messaging.py:
- send_broadcast
- send_push_message
- send_multicast
- send_narrowcast

รองรับ message types: text, image, flex
เขียน tests ใน tests/test_messaging.py"
```

### 3.3 🤖 Antigravity — Build Rich Menu Tools (4 tools) [parallel]
```
PROMPT (Agent 3 of 3, run parallel):
"Implement rich menu tools ใน src/tools/richmenu.py:
- list_rich_menus
- create_rich_menu
- set_default_rich_menu
- link_rich_menu_to_user

เขียน tests ใน tests/test_richmenu.py"
```

**💰 TOKEN SAVINGS**: 3 agents ทำ parallel ฟรีบน Antigravity = ประหยัดมหาศาล

### 3.4 🤖 Cursor — UI/UX Polish + Quick Fixes
```
หลัง Antigravity build เสร็จ, เปิด project ใน Cursor:
- Review code ที่ Antigravity สร้าง
- แก้ไข inline (Tab autocomplete)
- ปรับ error messages ให้ user-friendly
- เพิ่ม Thai language support ใน responses
- ปรับ code style ให้ consistent
```

**💰 TOKEN SAVINGS**: Cursor = flat $20/mo ไม่กิน Claude token

### 3.5 🤖 Claude Chat — Debug ปัญหายาก
```
เมื่อเจอ bug ที่ Cursor/Antigravity แก้ไม่ได้:

PROMPT:
"ผมมี MCP server ที่เชื่อมกับ LINE API
ตอน call send_narrowcast ได้ error นี้:
[paste error]

นี่คือ code ที่เกี่ยวข้อง:
[paste relevant code]

ช่วยวิเคราะห์สาเหตุและวิธีแก้"
```
**ใช้ Claude Chat เฉพาะปัญหายากเท่านั้น** — ประหยัด token

### 3.6 🤖 Claude Code — Auth + Billing Layer
```
PROMPT (Claude Code ใน terminal):
"อ่าน CLAUDE.md แล้ว implement:
1. src/auth/api_keys.py — API key generation + validation
2. src/auth/tiers.py — Free/Pro/Business feature gating
3. src/models/usage.py — Usage tracking (count calls per day)
4. src/db/database.py — SQLite connection + migrations

ต้องมั่นใจว่า:
- Free tier users ใช้ได้แค่ 3 tools + 100 calls/day
- Pro tier users ใช้ได้ 13 tools + 5000 calls/day
- Business tier = unlimited
- ถ้าเกิน limit ให้ return error message ที่ชัดเจน"
```
**ใช้ Claude Code สำหรับ auth/billing เพราะต้อง touch หลายไฟล์ + ต้องถูก 100%**

---

## PHASE 4: Testing & QA (สัปดาห์ที่ 5)

### 4.1 🤖 Claude Chat — เขียน Test Plan
```
PROMPT:
"จาก tools ทั้ง 18 ตัวในi MCP server นี้
(แนบ API-SPEC.md)

ช่วยเขียน test plan ที่ครอบคลุม:
1. Unit tests สำหรับแต่ละ tool
2. Integration tests (MCP client → server → LINE API)
3. Edge cases ที่ต้อง test (rate limit, invalid token, expired key)
4. Load test scenarios
5. Security tests (token leak, injection)

ให้เป็น checklist ที่ tick ได้"
```
**Output**: Test plan checklist
**⏭️ ส่งต่อ**: ให้ Claude Code run tests

### 4.2 🤖 Claude Code — Run Tests + Fix Bugs
```
PROMPT:
"run all tests ด้วย pytest
ดู test plan ใน /docs/TEST-PLAN.md
fix ทุก test ที่ fail
ถ้า test pass หมดแล้ว run mypy type check ด้วย"
```

### 4.3 🤖 Cursor — Final Polish
```
เปิดใน Cursor:
- Review tests ที่ Claude Code เขียน
- ปรับ error messages
- เช็ค Thai text encoding
- เช็ค README.md ว่าครบ
```

### 4.4 🧑 Manual Test (คุณทำเอง)
- เปิด Claude Desktop
- ใส่ config ใน claude_desktop_config.json (ดูใน spec)
- ทดสอบทุก tool กับ LINE OA จริงของคุณ
- ✅ get_account_info ทำงาน?
- ✅ send_broadcast ส่งได้จริง?
- ✅ rich menu สร้างได้?
- ✅ free tier ถูก block จาก paid tools?

---

## PHASE 5: Deploy & Launch Prep (สัปดาห์ที่ 5-6)

### 5.1 🤖 Claude Code — Dockerize + Deploy
```
PROMPT:
"deploy project นี้:
1. Build Docker image
2. Push to Railway.app (หรือ Fly.io)
3. Set environment variables จาก .env.example
4. Test health endpoint
5. Setup HTTPS + custom domain ถ้ามี"
```

### 5.2 🤖 Antigravity — Build Landing Page
```
PROMPT:
"สร้าง landing page สำหรับ [ชื่อ product]
เป็น Next.js + Tailwind CSS

Sections:
1. Hero: headline + subheadline + CTA "เริ่มใช้ฟรี"
2. Problem: pain points ของ LINE OA management
3. Solution: screenshot/demo ของ MCP server
4. Features: 3 tiers (Free/Pro/Business) พร้อมราคา
5. How it works: 3 steps (ติดตั้ง → เชื่อม LINE → สั่งงาน AI)
6. Testimonials: placeholder
7. FAQ: 5 คำถาม
8. Footer: links + contact

ภาษาไทย เป็นหลัก + English toggle
สี: LINE Green (#06C755) + dark theme
Deploy to Vercel"
```

### 5.3 🤖 ChatGPT — สร้าง Marketing Assets
```
PROMPT (ChatGPT):
"สร้างรูปสำหรับ social media promotion ของ [ชื่อ product]:

1. Facebook cover (1200x630): แสดง Claude + LINE logo 
   พร้อมข้อความ 'จัดการ LINE OA ด้วย AI'
2. Instagram post (1080x1080): Before/After
   ก่อน = คนนั่งจิ้ม LINE OA Manager เหนื่อยๆ
   หลัง = พิมพ์คำสั่งเดียว AI จัดการหมด
3. OG image สำหรับ landing page (1200x630)

สไตล์ modern, clean, professional"
```

### 5.4 🤖 Claude Chat — เขียน Content
```
PROMPT:
"เขียน content สำหรับ launch:
1. Blog post: 'ทำไม LINE OA ของคุณต้องการ AI' (800 คำ, Thai)
2. Facebook post ประกาศ launch (3 versions: short/medium/long)
3. Email template สำหรับ waitlist users
4. README.md สำหรับ GitHub (English, developer-focused)
5. Documentation site content (Getting Started guide)"
```

### 5.5 🤖 Cowork — Setup Automation
```
TASK (Cowork):
"ตั้ง scheduled task:
1. ทุกวันจันทร์ 9:00 — สรุป signups ใหม่จากสัปดาห์ก่อน
2. ทุกวันที่ 1 — สร้าง monthly revenue report
3. ทุกวัน 8:00 — เช็ค server health + uptime

บันทึก reports ลง /reports/ folder"
```

---

## PHASE 6: Distribution (สัปดาห์ที่ 6)

### 6.1 🤖 Claude Chat — เตรียม Marketplace Submission
```
PROMPT:
"เขียน listing สำหรับ MCP marketplace submissions:

1. Apify Store listing:
   - Title, description, tags
   - Pricing model (pay-per-event)
   - Screenshots descriptions

2. MCPize listing:
   - Title, description
   - Pricing tiers
   - Feature list

3. MCP.so listing:
   - Short description
   - Category tags

4. npm package description (package.json)
5. PyPI description (pyproject.toml)

ทุก listing ต้อง SEO-optimized"
```

### 6.2 🧑 Submit to Marketplaces (คุณทำเอง)
- [ ] Apify Store — https://apify.com/mcp/developers
- [ ] MCPize — https://mcpize.com/developers
- [ ] MCP.so — Submit form
- [ ] LobeHub — https://lobehub.com/mcp
- [ ] npm publish (ถ้าเป็น TypeScript)
- [ ] PyPI publish (ถ้าเป็น Python)

### 6.3 🧑 Community Launch (คุณทำเอง)
- [ ] โพสต์ Thai Programmer FB Group
- [ ] โพสต์ Pantip Technopolis
- [ ] โพสต์ LINE Developers Thailand
- [ ] โพสต์ Reddit r/SaaS + r/MCP
- [ ] โพสต์ Indie Hackers
- [ ] โพสต์ Product Hunt (schedule launch day)

---

## PHASE 7: Post-Launch Operations (ongoing)

### Weekly Routine (30 นาที/สัปดาห์)

| วัน | Task | AI ตัวไหน | ทำอะไร |
|-----|------|----------|--------|
| จันทร์ | Review metrics | Cowork (auto) | สรุป signups, revenue, usage |
| อังคาร | Customer support | Claude Chat | ตอบ questions จาก users |
| พุธ | Bug fixes | Cursor | แก้ bugs เล็กๆ ที่ report เข้ามา |
| พฤหัสบดี | Content | ChatGPT + Claude | สร้าง social post + blog |
| ศุกร์ | Planning | Claude Chat | Plan next feature/improvement |

### Monthly Routine (2 ชั่วโมง/เดือน)

| Task | AI ตัวไหน |
|------|----------|
| Revenue report | Cowork (auto-generated) |
| Feature development | Antigravity (parallel agents) |
| Complex bug fixes | Claude Code |
| Marketing assets | ChatGPT (images) |
| Strategic planning | Claude Chat |

---

## TOKEN BUDGET GUIDE

### เป้าหมาย: ใช้ Claude token ให้น้อยที่สุด

| งาน | AI ที่ใช้ | เหตุผล |
|-----|----------|--------|
| Scaffold + parallel builds | **Antigravity** | ฟรี (Opus) |
| Quick edits + styling | **Cursor** | Flat $20/mo |
| Images + video + marketing | **ChatGPT** | Claude ทำไม่ได้ |
| Deep reasoning + strategy | **Claude Chat** | เก่งสุด, ถูกสุดในกลุ่ม Claude |
| Complex multi-file work | **Claude Code** | 5.5x efficient กว่า Cursor |
| Doc automation + scheduling | **Cowork** | มี scheduled tasks |
| All other tasks | **Claude Chat** | Default fallback |

### กฎทอง
1. ถ้า Antigravity ทำได้ → ทำฟรี
2. ถ้าเป็น quick edit → Cursor (flat rate)
3. ถ้าต้อง generate image → ChatGPT
4. ถ้าต้อง think hard → Claude Chat
5. ถ้าต้องแก้หลายไฟล์ → Claude Code
6. ถ้าต้อง automate → Cowork

---

## TROUBLESHOOTING

### "Antigravity rate limit โดน lock"
→ สลับไปใช้ Claude Code ชั่วคราว
→ หรือใช้ Cursor agent mode

### "Claude Pro usage หมด"
→ ย้าย reasoning tasks ไป ChatGPT ชั่วคราว
→ ทำ quick edits ใน Cursor แทน
→ รอ reset (ทุก 5 ชั่วโมง)

### "LINE API return error"
→ ถาม Claude Chat (paste error message)
→ เช็ค LINE API status: https://status.line.biz/

### "MCP server ไม่โผล่ใน Claude Desktop"
→ Restart Claude Desktop
→ เช็ค config path ใน claude_desktop_config.json
→ เช็ค server logs: `uv run server.py 2>&1`

---

## CHECKLIST สำหรับแต่ละ Milestone

### ✅ Milestone 1: MVP Ready (สัปดาห์ที่ 4)
- [ ] Free tier 3 tools ทำงาน
- [ ] Pro tier 10 tools ทำงาน
- [ ] Auth + tier gating ทำงาน
- [ ] ทดสอบกับ Claude Desktop สำเร็จ
- [ ] Unit tests pass 100%

### ✅ Milestone 2: Launch Ready (สัปดาห์ที่ 6)
- [ ] Deployed on Railway/Fly.io
- [ ] Landing page live
- [ ] Listed on 3+ MCP marketplaces
- [ ] README + documentation ครบ
- [ ] 5+ beta users ทดสอบแล้ว

### ✅ Milestone 3: Revenue (เดือนที่ 2-3)
- [ ] 10+ paying users
- [ ] Revenue > ฿5,000/เดือน
- [ ] Churn rate < 10%
- [ ] NPS score > 7

### ✅ Milestone 4: Passive Income (เดือนที่ 6+)
- [ ] 100+ paying users
- [ ] Revenue > ฿50,000/เดือน
- [ ] Weekly maintenance < 2 ชั่วโมง
- [ ] Cowork scheduled tasks ทำงานอัตโนมัติ
- [ ] ลูกค้าแนะนำต่อ (organic growth)

---

*Last updated: March 2026*
*Version: 1.0*
*ใช้คู่กับ: linewhiz-spec.md + server.py*
